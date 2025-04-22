import serial
import sys
import time
import PySpin
import os
from tifffile import imwrite

class CameraController:
    def __init__(self, serial_port='COM5', baud_rate=9600, max_retries=3):
        self.ORIGINAL_EXPOSURE = 0.7
        # self.selected_exposure_array = [self.ORIGINAL_EXPOSURE] * 16
        self.acquisition_mode = 'SingleFrame'
        self.timeout = 5  # Align with Arduino's 5-second timeout
        self.max_retries = max_retries

        # Initialize serial connection with handshake
        for attempt in range(max_retries):
            try:
                self.arduino = serial.Serial(serial_port, baud_rate, timeout=1)
                self.arduino.DTR = False
                time.sleep(0.2)
                self.arduino.flushInput()
                # Handshake: Send 'C' and expect 'C' response
                self.arduino.write('C'.encode())
                time.sleep(1.0)
                response = self.arduino.read()
                print(f"DEBUG: Handshake response received: {response}")
                if response == b'C':
                    print("Serial connection established with Arduino!")
                    break
                else:
                    print(f"Handshake failed, expected b'C', got {response}, attempt {attempt + 1}/{max_retries}")
                    self.arduino.close()
            except serial.SerialException as ex:
                print(f"Serial connection failed: {ex}, attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    print("Max retries reached, exiting.")
                    sys.exit()
                time.sleep(1)
        else:
            sys.exit("Failed to establish serial connection.")

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
            self.initialize_camera()
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
        return seconds * 1_000_000

    @staticmethod
    def format_filename(base_name, light=None):
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
        while True:
            print("Image again? [Y/n]")
            re = input(">> ").upper()
            if re == 'Y':
                return False
            elif re == 'N':
                return True
            print("Incorrect entry. Retry.")

    def initialize_camera(self, mode='SingleFrame'):
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
        if not 0 <= pwm_value <= 255:
            print("Error: PWM value must be between 0 and 255")
            return False
        self.arduino.write('P'.encode())
        time.sleep(0.1)  # Small delay for Arduino to process
        self.arduino.write(bytes([pwm_value]))
        self.arduino.flush()
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.arduino.read() == b'P':
                print(f"Set PWM to {pwm_value}")
                return True
        print(f"Timeout waiting for PWM confirmation")
        return False

    def show_help(self):
        print("\nAvailable Commands:")
        print("  F: Four-capture mode (captures images with all four lights: N, E, S, W)")
        print("  U: Single-capture mode (captures one image with a specified light: N, S, E, or W)")
        print("  P: Set PWM value for light brightness (0-255)")
        print("  R: Reset Arduino state (turns off all lights, resets light sequence)")
        print("  H: Show this help message")
        print("  Q: Quit the program\n")

    def capture_image(self, light=None):
        try:
            self.camera.BeginAcquisition()
            image = self.camera.GetNextImage()
            if image.IsIncomplete():
                print(f'Image incomplete with status {image.GetImageStatus()}')
            else:
                filename = CameraController.format_filename("Image", light)
                try:
                    image_converted = image.Convert(PySpin.PixelFormat_RGB8, PySpin.HQ_LINEAR)
                    numpy_array = image_converted.GetNDArray()
                    print(f"Image array shape: {numpy_array.shape}")
                    imwrite(filename, numpy_array)
                    print(f"Image saved successfully at {filename}")
                except Exception as ex:
                    print(f"Failed to save image at {filename}: {ex}")
            image.Release()
            self.camera.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Spinnaker Exception: {ex}")

    def serial_com(self, mode='U', light=None):
        finish = False
        captured = False
        light_map = {0: 'N', 1: 'E', 2: 'S', 3: 'W'}
        if mode == 'F':
            lights = ['N', 'S', 'E', 'W']
            for light in lights:
                self.arduino.write(light.encode())
                self.arduino.flush()
                time.sleep(0.1)  # Small delay for Arduino
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    x = self.arduino.read()
                    if not x:
                        continue
                    print(f"DEBUG: Received from Arduino: {x}")
                    if x == b'L':
                        if self.arduino.in_waiting > 0:
                            light_index = self.arduino.read()[0]
                            print(f"Arduino confirmed light {light_map.get(light_index, 'Unknown')} (index {light_index})")
                        continue
                    elif x == b'A':
                        self.capture_image(light)
                        print(f"Capture done for light {light}")
                        time.sleep(0.5)
                        self.arduino.write('B'.encode())
                        self.arduino.flush()
                        captured = True
                        break
                    elif x == b'E':
                        print(f"Error received from Arduino for light {light}")
                        return True, False
                else:
                    print(f"Timeout waiting for Arduino response for light {light}")
                    return True, False
                # Wait for 'D' to confirm completion
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.arduino.read() == b'D':
                        break
                else:
                    print(f"Warning: Did not receive completion signal for light {light}")
        else:
            self.arduino.write(light.encode())
            self.arduino.flush()
            time.sleep(0.1)
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                x = self.arduino.read()
                if not x:
                    continue
                print(f"DEBUG: Received from Arduino: {x}")
                if x == b'L':
                    if self.arduino.in_waiting > 0:
                        light_index = self.arduino.read()[0]
                        print(f"Arduino confirmed light {light_map.get(light_index, 'Unknown')} (index {light_index})")
                    continue
                elif x == b'A':
                    self.capture_image(light)
                    print(f"Capture done for light {light}")
                    time.sleep(0.5)
                    self.arduino.write('B'.encode())
                    self.arduino.flush()
                    captured = True
                    break
                elif x == b'E':
                    print(f"Error received from Arduino for light {light}")
                    return True, False
            else:
                print(f"Timeout waiting for Arduino response for light {light}")
                return True, False
            # Wait for 'D' to confirm completion
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.arduino.read() == b'D':
                    break
            else:
                print(f"Warning: Did not receive completion signal for light {light}")
        return finish, captured

    def cleanup(self):
        # Send reset command to Arduino
        if hasattr(self, 'arduino') and self.arduino.is_open:
            self.arduino.write('R'.encode())
            self.arduino.flush()
            time.sleep(0.1)
            self.arduino.close()
        if hasattr(self, 'camera') and self.camera:
            self.camera.DeInit()
        if hasattr(self, 'cam_list'):
            self.cam_list.Clear()
        if hasattr(self, 'system'):
            self.system.ReleaseInstance()

    def run(self):
        print("Connect system to power now.\n")
        done = False
        try:
            while not done:
                print("Enter a command (H for help):")
                command = input(">> ").strip().upper()
                if command == 'F':
                    self.arduino.write(command.encode())
                    self.arduino.flush()
                    time.sleep(0.1)
                    finish, captured = self.serial_com(mode='F')
                    done = finish or (CameraController.image_again() if captured else False)
                elif command == 'U':
                    self.arduino.write(command.encode())
                    self.arduino.flush()
                    time.sleep(0.1)
                    print("Choose the light to turn on, N, S, E, or W:")
                    light = input(">> ").strip().upper()
                    if light in ['N', 'S', 'E', 'W']:
                        finish, captured = self.serial_com(mode='U', light=light)
                        done = finish or (CameraController.image_again() if captured else False)
                    else:
                        print("Incorrect entry, retry.")
                elif command == 'P':
                    try:
                        pwm_value = int(input("Enter PWM value (0-255): "))
                        if self.set_pwm(pwm_value):
                            print("PWM set successfully")
                        else:
                            print("Failed to set PWM")
                    except ValueError:
                        print("Error: Invalid PWM value")
                elif command == 'R':
                    self.arduino.write('R'.encode())
                    self.arduino.flush()
                    time.sleep(0.1)
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

    print("\nWelcome to the Camera and Light Control System!")
    print("This program controls a camera and four lights (N, S, E, W) via an Arduino.")
    print("Use the commands below to capture images, adjust light brightness, or reset the system.\n")

    controller = CameraController()
    controller.show_help()
    controller.run()

if __name__ == "__main__":
    main()