"""
Spinnaker Camera Capture Framework

This script provides a comprehensive interface for managing camera operations
using the Spinnaker SDK. It includes features such as initialization, image
capture, exposure control, and data processing utilities.

Written by:
    Lillian Kelley
    Sai Keshav Sasanapuri
    Will Shuley

For use in projects requiring customizable camera solutions.
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
        self.ORIGINAL_EXPOSURE = 0.7
        self.selected_exposure_array = [self.ORIGINAL_EXPOSURE] * 16
        self.acquisition_mode = 'SingleFrame'

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

            # Configure manual settings as per snippet
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.camera.ExposureTime.SetValue(self.get_microseconds(self.ORIGINAL_EXPOSURE))
            self.camera.GainAuto.SetValue(PySpin.GainAuto_Off)
            self.camera.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)

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

    @staticmethod
    def format_filename(base_name, light=None):
        """
        Format the image filename with timestamp and optional light direction.
        """
        parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
        images_dir = os.path.join(parent_dir, "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        if light:
            return os.path.join(images_dir, f"{base_name}_{light}_captured_at_{current_time}.tif")
        return os.path.join(images_dir, f"{base_name}_captured_at_{current_time}.tif")

    @staticmethod
    def image_again():
        """
        Prompt user to continue imaging.
        """
        while True:
            print("Image again? [Y/n]")
            re = input(">> ").lower()
            if re == 'y':
                return False
            elif re == 'n':
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
        print(f"Set PWM to {pwm_value}")

    def show_help(self):
        """
        Display help message with available commands.
        """
        print("\nAvailable Commands:")
        print("  F: Four-capture mode (captures images with all four lights: N, E, S, W)")
        print("  U: Single-capture mode (captures one image with a specified light: N, S, E, or W)")
        print("  P: Set PWM value for light brightness (0-255)")
        print("  R: Reset Arduino state (turns off all lights, resets light sequence)")
        print("  H: Show this help message")
        print("  Q: Quit the program\n")

    def capture_image(self, light=None):
        """
        Capture and save an image with the specified light.
        """
        try:
            self.camera.BeginAcquisition()
            image = self.camera.GetNextImage()
            if image.IsIncomplete():
                print(f'Image incomplete with status {image.GetImageStatus()}')
            else:
                filename = CameraController.format_filename("Image", light)
                image_converted = image.Convert(PySpin.PixelFormat_RGB8, PySpin.HQ_LINEAR)
                numpy_array = image_converted.GetNDArray()
                imwrite(filename, numpy_array)
                print(f"Image saved successfully at {filename}")
            image.Release()
            self.camera.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Spinnaker Exception: {ex}")

    def serial_com(self, mode='U', light=None):
        """
        Handle serial communication for image capture.
        """
        finish = False
        light_map = {0: 'N', 1: 'E', 2: 'S', 3: 'W'}
        if mode == 'F':
            lights = ['N', 'S', 'E', 'W']
            for light in lights:
                self.arduino.write(light.encode())
                while True:
                    x = self.arduino.read()
                    if x == b'L':
                        if self.arduino.in_waiting > 0:
                            light_index = self.arduino.read()[0]
                            print(
                                f"Arduino confirmed light {light_map.get(light_index, 'Unknown')} (index {light_index})")
                        continue
                    elif x == b'A':
                        self.capture_image(light)
                        print(f"Capture done for light {light}")
                        time.sleep(0.7)
                        self.arduino.write('B'.encode())
                        break
                    elif x == b'D':
                        return True
                    elif x == b'E':
                        print(f"Error received from Arduino for light {light}")
                        return True
        else:
            self.arduino.write(light.encode())
            while True:
                x = self.arduino.read()
                if x == b'L':
                    if self.arduino.in_waiting > 0:
                        light_index = self.arduino.read()[0]
                        print(f"Arduino confirmed light {light_map.get(light_index, 'Unknown')} (index {light_index})")
                    continue
                elif x == b'A':
                    self.capture_image(light)
                    print(f"Capture done for light {light}")
                    time.sleep(0.7)
                    self.arduino.write('B'.encode())
                    break
                elif x == b'D':
                    return True
                elif x == b'E':
                    print(f"Error received from Arduino for light {light}")
                    return True
        return finish

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
        print("Connect system to power now.\n")
        done = False
        try:
            while not done:
                print("Enter a command (H for help):")
                command = input(">> ").strip().lower()
                if command == 'f':
                    self.arduino.write(command.encode())
                    done = self.serial_com(mode='F') or CameraController.image_again()
                elif command == 'u':
                    self.arduino.write(command.encode())
                    print("Choose the light to turn on, N, S, E, or W:")
                    light = input(">> ").strip().upper()
                    if light in ['N', 'S', 'E', 'W']:
                        done = self.serial_com(mode='U', light=light) or CameraController.image_again()
                    else:
                        print("Incorrect entry, retry.")
                elif command == 'p':
                    try:
                        pwm_value = int(input("Enter PWM value (0-255): "))
                        self.set_pwm(pwm_value)
                    except ValueError:
                        print("Error: Invalid PWM value")
                elif command == 'r':
                    self.arduino.write('R'.encode())
                    print("Arduino reset")
                elif command == 'h':
                    self.show_help()
                elif command == 'q':
                    done = True
                else:
                    print("Incorrect command, retry.")
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
    print("Use the commands below to capture images, adjust light brightness, or reset the system.")

    # Show help message
    controller = CameraController()
    controller.show_help()
    controller.run()


if __name__ == "__main__":
    main()