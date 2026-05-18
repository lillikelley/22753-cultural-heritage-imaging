"""
Spinnaker Camera Capture Framework

This script provides a comprehensive interface for managing camera operations
using the Spinnaker SDK.

Written by:
    Lillian Kelley
    Sai Keshav Sasanapuri
    William Shuley
"""

import PySpin
import numpy as np
import sys, time, serial, os
import shutil
from tifffile import imwrite

import arduino_controller


def image_again():
    """Prompt user to continue imaging."""
    while True:
        print("Image again? [Y/n]")
        re = input(">> ").upper()
        if re == 'Y':
            return True
        elif re == 'N':
            return False
        print("Incorrect entry. Retry.")


def show_help():
    """Display help message with available commands."""
    print("""
        Available Commands:
          F: Four-capture mode (N, S, E, W)
          U: Single-capture mode
          M: Manual Light Toggle (Turn lights on without camera)
          P: Set PWM value
          E: Set exposure time
          R: Reset Arduino
          H: Help
          Q: Quit
    """)


class CameraController:
    @staticmethod
    def get_microseconds(seconds):
        """Convert exposure time from seconds to microseconds."""
        return seconds * 1_000_000

    def set_exposure(self):
        """Interactively set camera exposure time."""
        try:
            exp_node = PySpin.CFloatPtr(self.camera.GetNodeMap().GetNode('ExposureTime'))
            min_exp = exp_node.GetMin() / 1e6
            max_exp = exp_node.GetMax() / 1e6
        except Exception:
            min_exp, max_exp = 0.0001, 30.0

        print(f"\nExposure range: {min_exp:.4f} s → {max_exp:.1f} s")
        print(f"Current exposure: {self.ORIGINAL_EXPOSURE:.4f} s")

        while True:
            try:
                raw = input("Enter new exposure in seconds (or press ENTER to keep current): ").strip()
                if raw == '':
                    print("Exposure unchanged.")
                    return
                value = float(raw)
                if not min_exp <= value <= max_exp:
                    print(f"Out of range. Enter a value between {min_exp:.4f} and {max_exp:.1f}.")
                    continue
                self.ORIGINAL_EXPOSURE = value
                self.camera.ExposureTime.SetValue(self.get_microseconds(value))
                print(f"Exposure set to {value:.4f} s")
                return
            except ValueError:
                print("Invalid input. Enter a number.")

    def __init__(self, serial_port='COM5', baud_rate=9600):
        """Initialize camera and Arduino connection."""
        self.ORIGINAL_EXPOSURE = 0.125
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

        # Initialize camera
        try:
            self.system = PySpin.System.GetInstance()
            self.cam_list = self.system.GetCameras()
            if self.cam_list.GetSize() == 0:
                print("No cameras detected")
                self.cleanup()
                sys.exit()

            self.camera = self.cam_list.GetByIndex(0)
            print("Camera detected")

            self.initialize_camera()

            # Manual exposure settings
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.camera.ExposureTime.SetValue(self.get_microseconds(self.ORIGINAL_EXPOSURE))

            # Disable auto features
            self.camera.GainAuto.SetValue(PySpin.GainAuto_Off)
            self.camera.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)

            if self.camera.BalanceWhiteAuto.GetAccessMode() == PySpin.RW:
                self.camera.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)

            if self.camera.GammaEnable.GetAccessMode() == PySpin.RW:
                self.camera.GammaEnable.SetValue(False)

        except PySpin.SpinnakerException as ex:
            print(f"Camera initialization failed: {ex}")
            self.cleanup()
            sys.exit()

    def initialize_camera(self, mode='SingleFrame'):
        """Set camera to SingleFrame acquisition mode."""
        try:
            self.camera.Init()
            nodemap = self.camera.GetNodeMap()
            node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
            node_acquisition_mode_ = node_acquisition_mode.GetEntryByName(mode)
            acquisition_mode_ = node_acquisition_mode_.GetValue()
            node_acquisition_mode.SetIntValue(acquisition_mode_)
        except PySpin.SpinnakerException as ex:
            raise ValueError(f"Camera initialization failed: {ex}")

    def capture_image(self, light_code):
        """Capture, archive old file if exists, save new image, and show histogram."""
        try:
            self.camera.BeginAcquisition()
            image = self.camera.GetNextImage()

            if image.IsIncomplete():
                print(f"Image incomplete with status {image.GetImageStatus()}")
            else:
                filename = self.format_filename(light_code)

                # Archive previous file if it exists
                if os.path.exists(filename):
                    image_dir = os.path.dirname(filename)
                    archive_dir = os.path.join(image_dir, "archive")
                    os.makedirs(archive_dir, exist_ok=True)

                    name, ext = os.path.splitext(os.path.basename(filename))
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    archive_name = f"{name}_{timestamp}{ext}"
                    archive_path = os.path.join(archive_dir, archive_name)

                    try:
                        shutil.move(filename, archive_path)
                        print(f"  -> Archived previous image to: archive/{archive_name}")
                    except Exception as e:
                        print(f"  -> Warning: Could not archive old file: {e}")

                # Save new image
                try:
                    numpy_array = image.GetNDArray()
                    self.print_live_histogram(numpy_array, filename)
                    meta_ts = time.strftime("%Y:%m:%d %H:%M:%S")
                    imwrite(filename, numpy_array, metadata={'DateTime': meta_ts})
                    print(f"Image saved: {os.path.basename(filename)}")
                except Exception as ex:
                    print(f"Failed to save image: {ex}")

            image.Release()
            self.camera.EndAcquisition()

        except PySpin.SpinnakerException as ex:
            print(f"Spinnaker Exception: {ex}")

    def format_filename(self, light_code):
        """Generate filename like flat_north.tiff, calibration_east.tiff, etc."""
        direction_map = {'N': "north", 'E': "east", 'S': "south", 'W': "west"}
        type_map = {'A': 'flat', 'B': 'calibration', 'C': 'target'}

        prefix = type_map.get(self.image_type, 'image')
        direction = direction_map.get(light_code, 'unknown')

        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(script_dir, "..", "images"))
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, f"{prefix}_{direction}.tiff")

    def print_live_histogram(self, numpy_array, filename):
        """Improved histogram with clear capture type label."""
        if numpy_array.dtype == np.uint16:
            gray = (numpy_array / 256).astype(np.uint8)
        else:
            gray = numpy_array.astype(np.uint8)

        hist, _ = np.histogram(gray.ravel(), bins=256, range=(0, 255))
        total = gray.size
        mean_val = np.mean(gray)
        shadows = np.sum(hist[0:21]) / total * 100
        highlights = np.sum(hist[235:256]) / total * 100
        clipped = np.sum(gray == 255) / total * 100

        current_exp = self.ORIGINAL_EXPOSURE

        type_map = {'A': 'FLAT-FIELDING', 'B': 'CALIBRATION', 'C': 'TARGET OBJECT'}
        capture_type = type_map.get(self.image_type, 'UNKNOWN')

        # Suggestion logic
        if clipped > 30:
            suggested = current_exp * 0.30
        elif clipped > 10:
            suggested = current_exp * 0.45
        elif clipped > 2:
            suggested = current_exp * 0.65
        else:
            target_mean = 130.0
            scale_factor = target_mean / max(mean_val, 10)
            suggested = current_exp * scale_factor

        suggested = max(0.001, min(3.0, round(suggested, 3)))

        print(f"\n{'=' * 78}")
        print(f"HISTOGRAM CHECK → {os.path.basename(filename)}  [{capture_type}]")
        print(f"   Mean brightness     : {mean_val:.1f} / 255")
        print(f"   Shadows (0-20)      : {shadows:.1f}%")
        print(f"   Highlights (235-255): {highlights:.1f}%")
        print(f"   Pure white clipped  : {clipped:.2f}%")
        print(f"   Current exposure    : {current_exp:.3f} s")

        if mean_val < 90 or shadows > 15:
            status = "**TOO DARK**"
        elif mean_val > 160 or highlights > 5 or clipped > 0.5:
            status = "**TOO BRIGHT**"
        else:
            status = "**GOOD EXPOSURE** 👍"
            print(f"   → {status}")
            print(f"{'=' * 78}\n")
            return

        print(f"   → {status}")
        print(f"      Suggested next exposure: **{suggested:.3f} s**")

        if suggested <= 0.001 and clipped > 5:
            print("   ⚠️  Lights are still too bright even at minimum exposure!")
            print("      → Use 'P' command to lower PWM (try 140-160).")

        print(f"{'=' * 78}\n")

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'camera') and self.camera:
            self.camera.DeInit()
        if hasattr(self, 'cam_list'):
            self.cam_list.Clear()
        if hasattr(self, 'system'):
            self.system.ReleaseInstance()
        if hasattr(self, 'arduino'):
            self.arduino.close()

    def run(self):
        """Main command loop."""
        self.arduino.write('C'.encode())
        self.arduino.flush()
        print("Connect system to power now.\n")

        done = False

        def get_image_type():
            """Ask for capture type (A/B/C) with clean prompt."""
            print("\nInput type:\nA: Flat-fielding\nB: Calibration\nC: Target Object")
            while True:
                t_input = input(">> ").strip().upper()
                if t_input in ('A', 'B', 'C'):
                    return t_input
                print("Incorrect entry. Please enter A, B, or C.")

        try:
            while not done:
                print("\nEnter a command (H for help):")
                command = input(">> ").strip().upper()

                if command == 'F':
                    self.image_type = get_image_type()
                    while True:
                        print(f"Starting {self.image_type} four-capture sequence...")
                        captured = arduino_controller.serial_com(
                            self.arduino, self.capture_image,
                            mode='F', command=b'F', framed=True
                        )
                        if not captured or not image_again():
                            break

                elif command == 'U':
                    self.image_type = get_image_type()
                    print("Choose the light to turn on, N, S, E, or W:")
                    light = input(">> ").strip().upper()
                    if light not in ('N', 'S', 'E', 'W'):
                        print("Invalid light. Please enter N, S, E, or W.")
                    else:
                        while True:
                            captured = arduino_controller.serial_com(
                                self.arduino, self.capture_image,
                                mode='U', light=light, command=b'U', framed=True
                            )
                            if not captured or not image_again():
                                break

                elif command == 'M':
                    arduino_controller.manual_light_control(self.arduino)

                elif command == 'P':
                    try:
                        pwm_value = int(input("Enter PWM value (0-255): "))
                        arduino_controller.set_pwm(self.arduino, pwm_value)
                    except ValueError:
                        print("Error: Please enter a number between 0 and 255")

                elif command == 'E':
                    self.set_exposure()

                elif command == 'R':
                    self.arduino.write('R'.encode())
                    self.arduino.flush()
                    print("Arduino reset.")

                elif command == 'H':
                    show_help()

                elif command == 'Q':
                    print("Exiting program...")
                    done = True

                else:
                    print("Incorrect entry, retry.")

        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user. Exiting...")
        finally:
            self.cleanup()