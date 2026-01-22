"""
Spinnaker Camera Capture Framework

This script provides a comprehensive interface for managing camera operations
using the Spinnaker SDK. It includes features such as initialization, image
capture, exposure control, and data processing utilities.

Written by:
    Lillian Kelley
    Sai Keshav Sasanapuri
    William Shuley

"""

import serial

import sys
import time
import PySpin
import os
from tifffile import imwrite

class CameraController:
    def __init__(self, serial_port='COM5', baud_rate=9600):
        """
        Constructor of the class. Initializes the camera, sets the exposure mode to manual,
        disables auto-gain and auto exposure target gray, and sets the exposure to default.
        """
        # Initialize default exposure values
        self.ORIGINAL_EXPOSURE = 0.12
        self.selected_exposure_array = [self.ORIGINAL_EXPOSURE] * 16
        self.acquisition_mode = None
        self.image_type = None

        # Initialize serial connection
        try:
            self.arduino = serial.Serial(serial_port, baud_rate, timeout=1)
            self.arduino.DTR = False
            time.sleep(0.2)
            self.arduino.flushInput()
            print("Serial connection established!")
        except serial.SerialException as ex:
            print(f"Serial connection failed: {ex}")
            sys.exit()

        # Initialize camera system
        try:
            self.system = PySpin.System.GetInstance()
            self.cam_list = self.system.GetCameras()
            if self.cam_list.GetSize() == 0:
                print("No cameras detected")
                self.cleanup()
                sys.exit()
            self.camera = self.cam_list.GetByIndex(0)
            print("Camera detected")

            # Initialize camera with default settings
            self.initialize_camera()

            # Configure manual settings
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.camera.ExposureTime.SetValue(self.get_microseconds(self.ORIGINAL_EXPOSURE))
            self.camera.GainAuto.SetValue(PySpin.GainAuto_Off)
            self.camera.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)

            # 1. Turn off Auto White Balance (stops color flickering)
            if self.camera.BalanceWhiteAuto.GetAccessMode() == PySpin.RW:
                self.camera.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)

            # 2. Turn off Gamma (stops "enhancing" the darks)
            if self.camera.GammaEnable.GetAccessMode() == PySpin.RW:
                self.camera.GammaEnable.SetValue(False)

        except PySpin.SpinnakerException as ex:
            print(f"Camera initialization failed: {ex}")
            self.cleanup()
            sys.exit()

    @staticmethod
    def get_microseconds(seconds):
        """
        Convert exposure time from seconds to microseconds.
        """
        return seconds * 1_000_000

    def format_filename(self, light_code):
        """
        Formats filename based on RUNTHIS.py logic: [Type]_[Direction].tiff
        """
        # Map letters to full names
        direction_map = {'N': "north", 'E': "east", 'S': "south", 'W': "west"}

        # Map user selection to prefix
        type_map = {'A': 'flat', 'B': 'calibration', 'C': 'target'}

        prefix = type_map.get(self.image_type, 'image')
        direction = direction_map.get(light_code, 'unknown')

        # Save to the "images" directory one level up
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # ".." means go up one folder
        output_dir = os.path.abspath(os.path.join(script_dir, "..", "images"))
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, f"{prefix}_{direction}.tiff")

    @staticmethod
    def image_again():
        """
        Prompt user to continue imaging.
        """
        while True:
            print("Image again? [Y/n]")
            re = input(">> ").upper()
            if re == 'Y':
                return False
            elif re == 'N':
                return True
            print("Incorrect entry. Retry.")

    def initialize_camera(self, mode='SingleFrame'):
        """
        Initialize the camera with the specified acquisition mode.
        """
        try:
            self.camera.Init()
            nodemap = self.camera.GetNodeMap()
            node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
            node_acquisition_mode_ = node_acquisition_mode.GetEntryByName(mode)
            acquisition_mode_ = node_acquisition_mode_.GetValue()
            node_acquisition_mode.SetIntValue(acquisition_mode_)
        except PySpin.SpinnakerException as ex:
            raise ValueError(f"Camera initialization failed: {ex}")

    def set_pwm(self, pwm_value):
        """
        Send PWM value to Arduino.
        """
        if not 0 <= pwm_value <= 255:
            print("Error: PWM value must be between 0 and 255")
            return
        self.arduino.write('P'.encode())
        self.arduino.write(bytes([pwm_value]))
        self.arduino.flush()
        print(f"Set PWM to {pwm_value}")

    def manual_light_control(self):
        """
        Manually toggle a light on, wait for user input, then turn it off.
        FIXED: Explicitly waits for Arduino 'Done' signal to prevent bugs.
        """
        print("Manual Mode: Enter Light (N, S, E, W) to toggle ON.")
        print("Enter 'Q' to return to main menu.")

        while True:
            # Standard map (Since you reflashed Arduino, logic matches hardware)
            light_map = {'N': 'N', 'E': 'E', 'S': 'S', 'W': 'W'}

            user_input = input("Light >> ").strip().upper()

            if user_input == 'Q':
                break

            if user_input in light_map:
                physical_command = light_map[user_input]

                # 1. Turn ON
                self.arduino.write('U'.encode())
                self.arduino.flush()
                time.sleep(0.1)
                self.arduino.write(physical_command.encode())
                self.arduino.flush()

                print(f"Attempting to turn on {user_input}...")

                # 2. Wait for 'A' (Confirmation)
                start_time = time.time()
                light_is_on = False
                while time.time() - start_time < 5:
                    if self.arduino.in_waiting:
                        resp = self.arduino.read()
                        if resp == b'L':
                            if self.arduino.in_waiting: self.arduino.read()
                            continue
                        if resp == b'A':
                            light_is_on = True
                            break

                if light_is_on:
                    print(f"\n>>> LIGHT {user_input} IS ON <<<")
                    input("Press [ENTER] to turn light OFF...")

                    # 3. Turn OFF
                    self.arduino.write('B'.encode())
                    self.arduino.flush()

                    # --- PROTOCOL FIX: EAT THE 'D' ---
                    # We loop until we catch the 'D' from the Arduino.
                    # This ensures the buffer is 100% empty before we loop again.
                    timeout_d = time.time() + 3.0
                    got_d = False
                    while time.time() < timeout_d:
                        if self.arduino.in_waiting:
                            d_char = self.arduino.read()
                            if d_char == b'D':
                                got_d = True
                                break

                    if not got_d:
                        print("Warning: Arduino did not send 'Done' signal.")
                    else:
                        print(f"Light {user_input} turned OFF (Confirmed).\n")
                    # ---------------------------------
                else:
                    print("Error: Arduino did not confirm light status.\n")
                    self.arduino.write('R'.encode())
            else:
                print("Invalid input.")

    def show_help(self):
        """
        Display help message with available commands.
        """
        print("\nAvailable Commands:")
        print("  F: Four-capture mode (N, E, S, W)")
        print("  U: Single-capture mode")
        print("  M: Manual Light Toggle (Turn lights on without camera)")
        print("  P: Set PWM value")
        print("  R: Reset Arduino")
        print("  H: Help")
        print("  Q: Quit\n")

    def capture_image(self, light=None):
        """
        Capture and save an image with the specified lighting condition.
        """
        try:
            self.camera.BeginAcquisition()
            image = self.camera.GetNextImage()

            if image.IsIncomplete():
                print(f"Image incomplete with status {image.GetImageStatus()}")
            else:
                filename = self.format_filename(light)
                try:
                    # Convert to NumPy array for saving
                    numpy_array = image.GetNDArray()                    # print(f"Image array shape: {numpy_array.shape}")

                    imwrite(filename, numpy_array)
                    print(f"Image saved successfully at {filename}")
                except Exception as ex:
                    print(f"Failed to save image at {filename}: {ex}")

            image.Release()
            self.camera.EndAcquisition()

        except PySpin.SpinnakerException as ex:
            print(f"Spinnaker Exception: {ex}")

    def serial_com(self, mode='U', light=None):
        """
        Handle serial communication.
        FIXED:
          - 'U' Mode: Waits for 'D' after every capture.
          - 'F' Mode: Only waits for 'D' at the very end (after West).
        """
        # 1. Clean the mailbox (Buffer)
        self.arduino.reset_input_buffer()

        finish = False
        captured = False

        if mode == 'F':
            lights = ['N', 'E', 'S', 'W']

            # F-Mode Loop
            for light_name in lights:
                # Note: In F-mode, we do NOT send the light name.
                # The Arduino advances automatically. We just wait for 'A'.

                # 2. Wait for Ready ('A')
                start_time = time.time()
                while True:
                    if time.time() - start_time > 10:
                        print(f"Timeout waiting for light {light_name}")
                        return True, False

                    x = self.arduino.read()
                    if not x: continue

                    if x == b'L':  # Index confirmation
                        if self.arduino.in_waiting: self.arduino.read()
                        continue
                    elif x == b'A':
                        # 3. Capture
                        self.capture_image(light_name)
                        print(f"Capture done for light {light_name}")
                        time.sleep(1.0)

                        # 4. Next Light (Send 'B')
                        self.arduino.write('B'.encode())
                        self.arduino.flush()

                        captured = True
                        break  # Break inner loop, move to next light
                    elif x == b'E':
                        return True, False

            # 5. AFTER all 4 lights, consume the final 'D' (Done)
            # The Arduino sends this only once after West is finished.
            timeout_d = time.time() + 2.0
            while time.time() < timeout_d:
                if self.arduino.in_waiting:
                    if self.arduino.read() == b'D':
                        break

        else:  # Single Mode ('U')
            self.arduino.write(light.encode())
            self.arduino.flush()

            start_time = time.time()
            while True:
                if time.time() - start_time > 10:
                    print(f"Timeout waiting for light {light}")
                    return True, False
                x = self.arduino.read()
                if not x: continue

                if x == b'L':
                    if self.arduino.in_waiting: self.arduino.read()
                    continue
                elif x == b'A':
                    self.capture_image(light)
                    print(f"Capture done for light {light}")
                    time.sleep(1.0)
                    self.arduino.write('B'.encode())
                    self.arduino.flush()

                    # 6. In 'U' mode, we MUST wait for 'D' immediately
                    timeout_d = time.time() + 2.0
                    while time.time() < timeout_d:
                        if self.arduino.in_waiting:
                            if self.arduino.read() == b'D':
                                break

                    captured = True
                    break
                elif x == b'D':
                    print(f"Warning: Received unexpected D for light {light}")
                    return True, False
                elif x == b'E':
                    return True, False

        return finish, captured

    def cleanup(self):
        """
        Clean up camera and serial resources.
        """
        if hasattr(self, 'camera') and self.camera:
            self.camera.DeInit()
        if hasattr(self, 'cam_list'):
            self.cam_list.Clear()
        if hasattr(self, 'system'):
            self.system.ReleaseInstance()
        if hasattr(self, 'arduino'):
            self.arduino.close()

    def run(self):
        """
        Main loop for camera capture.
        """
        self.arduino.write('C'.encode())
        self.arduino.flush()
        print("Connect system to power now.\n")
        done = False
        try:
            while not done:
                print("\nInput type:\nA: Flat-fielding\nB: Calibration\nC: Target Object")
                valid_type = False
                while not valid_type:
                    type_input = input(">> ").strip().upper()
                    if type_input in ('A', 'B', 'C'):
                        self.image_type = type_input
                        valid_type = True
                    else:
                        print("Incorrect entry. Please enter A, B, or C.")
                print("Enter a command (H for help):")
                command = input(">> ").strip().upper()
                if command == 'F':
                    self.arduino.write(command.encode())
                    self.arduino.flush()
                    finish, captured = self.serial_com(mode='F')
                    done = finish or (CameraController.image_again() if captured else False)
                elif command == 'U':
                    self.arduino.write(command.encode())
                    self.arduino.flush()
                    print("Choose the light to turn on, N, S, E, or W:")
                    light = input(">> ").strip().upper()
                    if light in ['N', 'S', 'E', 'W']:
                        finish, captured = self.serial_com(mode='U', light=light)
                        done = finish or (CameraController.image_again() if captured else False)
                    else:
                        print("Incorrect entry, retry.")
                elif command == 'M':
                    self.manual_light_control()
                elif command == 'P':
                    try:
                        pwm_value = int(input("Enter PWM value (0-255): "))
                        self.set_pwm(pwm_value)
                    except ValueError:
                        print("Error: Invalid PWM value")
                elif command == 'R':
                    self.arduino.write('R'.encode())
                    self.arduino.flush()
                    print("Arduino reset")
                elif command == 'H':
                    self.show_help()
                elif command == 'Q':
                    done = True
                else:
                    print("Incorrect entry, retry.")
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.cleanup()

def main():
    while True:
        print("Is power supply unplugged? [Y/n]")
        a = input(">> ").strip().lower()
        if a in ['y', 'n']:
            if a == 'y':
                break
            print("Unplug power supply.")
        else:
            print("Invalid entry. Please enter 'Y' or 'n'.")

    # Welcome message
    print("\nWelcome to the Camera and Light Control System!")
    print("This program controls a camera and four lights (N, S, E, W) via an Arduino.")
    print("Use the commands below to capture images, adjust light brightness, or reset the system.\n")

    # Show help message
    controller = CameraController()
    controller.show_help()
    controller.run()

if __name__ == "__main__":
    main()