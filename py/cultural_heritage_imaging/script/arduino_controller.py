import time


class SerialProtocolError(RuntimeError):
    """Raised when the Arduino handshake desyncs or stalls."""


def read_byte(arduino, timeout):
    """Read exactly one byte, raising SerialProtocolError on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        b = arduino.read(1)
        if b:
            return b
    raise SerialProtocolError(
        f"No byte from Arduino within {timeout:.1f}s (handshake desync?)"
    )


def read_until(arduino, target, timeout):
    """Discard bytes until `target` is seen, or raise on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        b = arduino.read(1)
        if b == target:
            return
        # Any other byte is protocol noise and is intentionally dropped,
        # exactly like the firmware's wait-for-'B' loop.
    raise SerialProtocolError(
        f"Expected {target!r} from Arduino within {timeout:.1f}s "
        f"(handshake desync?)"
    )


def _await_ready(arduino, expected_light, framed, timeout):
    """
    Wait for the Arduino's 'ready to capture' signal.

    Unframed firmware: just 'A'.
    Framed firmware: 'A' followed by the light letter, which we verify
    against the light Python is about to label. A mismatch means the
    LED state and the host loop have drifted apart -> hard error.
    """
    read_until(arduino, b'A', timeout)
    if framed:
        got = read_byte(arduino, timeout).decode(errors='replace')
        if expected_light is not None and got != expected_light:
            raise SerialProtocolError(
                f"Phase slip: firmware lit '{got}' but host expected "
                f"'{expected_light}'. Aborting before mislabeled capture."
            )


def set_pwm(arduino, pwm_value):
    """Send PWM value to Arduino and wait for confirmation."""
    if not 0 <= pwm_value <= 255:
        print("Error: PWM value must be between 0 and 255")
        return

    arduino.write(b'P')
    arduino.write(bytes([pwm_value]))
    arduino.flush()

    # Wait for Arduino to process (small safety delay)
    time.sleep(0.15)
    print(f"✓ PWM set to {pwm_value}")


def manual_light_control(arduino, timeout=5.0):
    """Manual mode: turn a single light on/off without the camera.
    """
    valid = {'N', 'S', 'E', 'W'}
    print("Manual Mode: Enter N, S, E, W, or Q to quit.\n")
    arduino.reset_input_buffer()

    while True:
        user_input = input("Light >> ").strip().upper()

        if user_input == 'Q':
            print("Exiting manual mode.\n")
            return

        if user_input not in valid:
            print("Invalid entry. Enter N, S, E, W, or Q.")
            continue

        arduino.reset_input_buffer()
        arduino.write(b'U')
        arduino.flush()
        time.sleep(0.15)            # let firmware enter case 'U' wait loop
        arduino.write(user_input.encode())
        arduino.flush()

        print(f"Turning on {user_input}...")

        try:
            _await_ready(arduino, user_input, framed=True, timeout=timeout)
        except SerialProtocolError as e:
            print(f"  -> {e}")
            continue

        print(f"\n>>> LIGHT {user_input} IS ON <<<")
        input("Press [ENTER] to turn OFF...")

        arduino.write(b'B')
        arduino.flush()

        try:
            read_until(arduino, b'D', timeout)
        except SerialProtocolError as e:
            print(f"  -> {e}")
            continue

        print(f"Light {user_input} turned OFF.\n")



def serial_com(arduino, capture_fn, mode='U', light=None, *,
               command=None, flush_fn=None, framed=False,
               timeout=5.0, stabilize_s=0.15):
    """
    Drive a four-capture ('F') or single-capture ('U') sequence.

    arduino      : open pyserial Serial object
    capture_fn   : callable(light_letter) -> performs ONE exposure and
                   saves it. It must trigger a fresh exposure, not return
                   a queued/free-run frame (that is the frame-lag bug).
    mode         : 'F' or 'U'
    light        : required for 'U' mode ('E'/'W'/'N'/'S')
    command      : if given, this byte is sent to the Arduino AFTER the
                   input buffer is cleared. Pass command=b'F' / b'U' and
                   remove the corresponding write from main.py to close
                   the startup race.
    flush_fn     : optional callable() that empties the camera's frame
                   queue. Called after the LED is confirmed on and the
                   stabilization delay has elapsed, immediately before
                   capture. Strongly recommended for free-run cameras.
    framed       : True if the firmware echoes the light letter after 'A'
                   (see firmware note at the bottom of this file).
    timeout      : per-read timeout in seconds.
    stabilize_s  : extra LED settle time on top of the firmware's delay.
    """
    # Order matters: clear stale bytes FIRST, then trigger the sequence.
    arduino.reset_input_buffer()
    if command is not None:
        arduino.write(command)
        arduino.flush()

    if mode == 'F':
        lights = ['E', 'W', 'N', 'S']
        print("Starting four-capture sequence...")

        for light_name in lights:
            _await_ready(arduino, light_name, framed, timeout)

            time.sleep(stabilize_s)  # LED settle
            if flush_fn is not None:
                flush_fn()  # drop any pre-LED frames
            capture_fn(light_name)  # fresh exposure, LED still on
            print(f"Capture done for light {light_name}")

            arduino.write(b'B')  # release Arduino to next LED
            arduino.flush()

        read_until(arduino, b'D', timeout)
        print("Four-capture sequence completed.\n")
        return True

    elif mode == 'U':
        if light is None:
            raise SerialProtocolError("Single-capture mode requires `light`.")

        time.sleep(stabilize_s)
        arduino.write(light.encode())
        arduino.flush()

        _await_ready(arduino, light, framed, timeout)

        time.sleep(stabilize_s)
        if flush_fn is not None:
            flush_fn()
        capture_fn(light)
        print(f"Capture done for light {light}")

        arduino.write(b'B')
        arduino.flush()

        read_until(arduino, b'D', timeout)
        return True

    else:
        raise SerialProtocolError(f"Unknown mode {mode!r} (expected 'F' or 'U').")

# ---------------------------------------------------------------------------
# To enable framed=True, add the light letter to the firmware's ready signal:
#
#   case 'F':
#     for (int i = 0; i < numLights; i++) {
#       turnOnLight(i);
#       delay(100);
#       Serial.write('A');
#       Serial.write("EWNS"[i]);   // <-- add this line
#       ...
#
# and likewise after the 'A' in case 'U'. Until that firmware change is
# flashed, leave framed=False (the default).
# ---------------------------------------------------------------------------