"""
Spinnaker Camera Capture Framework

This script provides a comprehensive interface for managing camera operations
using the Spinnaker SDK. It includes features such as initialization, image
capture, exposure control, and data processing utilities.

Written by:
    Lillian Kelley
    Sai Keshav Sasanapuri
    Will Schuley

For use in projects requiring high-performance and customizable camera solutions.
"""
import serial
import sys
import time
import PySpin
import os
from tifffile import imwrite

# LILLI TODO
# add lighting loop for four lights
# filename implement TODO TEST
# press F creates four different images with different names. U can be whatever name
# init function that does auto exposure and gain TODO TEST

b = True
while b:
    print("Is power supply unplugged? [Y/n]")
    a = input("<< ")
    if a == 'Y':
        b = False
    elif a == 'n':
        print("Unplug power supply.")
        b = True
    else:
        print("Incorrect entry. Try again.")
        b = True

# Establish a serial connection to the Arduino on COMX with a baud rate of 9600 and a 1-second timeout
# USER: Be sure to replace port parameter with your Arduino comms port!
arduino = serial.Serial('COM5', 9600, timeout=1)

# Temporarily reset the Data Terminal Ready (DTR) line to avoid issues with automatic resets during communication
arduino.setDTR(False)  # Note: 'setDTR' might not be recognized, refer to: https://stackoverflow.com/a/19656567
time.sleep(0.2) # Allow Arduino to reset

# Clear any existing data in the input buffer to start with fresh data
arduino.flushInput()

system = PySpin.System.GetInstance() # Initialize the PySpin system instance to manage camera interactions
cam_list = system.GetCameras() # Retrieve a list of all cameras connected to the system
num_cams = cam_list.GetSize() # Determine the number of connected cameras

# Check if any cameras are detected.
if num_cams == 0:
    # If no cameras are found, display a message to the user
    print("No cameras detected")
    # Clear the camera list and release system resources
    cam_list.Clear()
    system.ReleaseInstance()
    sys.exit()
else:
    # If at least one camera is detected, inform the user
    print("Camera detected")
# Access the first camera in the list
cam = cam_list.GetByIndex(0)


def __init__(self):
    """
    Constructor of the class. Initializes the camera, sets the exposure mode to manual,
    disables auto-gain and auto exposure target grey, and sets the exposure to default.

    :param None
    :return: None
    """
    # Initialize default exposure values
    self.ORIGINAL_EXPOSURE = 0.7
    self.selected_exposure_array = [self.ORIGINAL_EXPOSURE] * 16
    self.acquisition_mode = None

    try:
        # Initialize the camera
        self.initialize_camera()

        # If camera is initialized successfully, configure settings
        self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        self.camera.ExposureTime.SetValue(self.get_microseconds(self.ORIGINAL_EXPOSURE))
        self.camera.GainAuto.SetValue(PySpin.GainAuto_Off)
        self.camera.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)

    except PySpin.SpinnakerException:
        raise ValueError("Initialization failed")

    finally:
        # Ensure the camera is uninitialized to clean up resources
        self.uninitialize_camera()


def initialize_camera(self, mode='SingleFrame'):
    """
    Initializes the camera for image acquisition with a specified mode.

    :param mode: str
        The acquisition mode to be set ('SingleFrame' by default).
    :return: None
    """
    try:
        # Initialize camera and system variables
        self.camera = None
        self.acquisition_mode = mode
        self.system = PySpin.System.GetInstance()
        cam_list = self.system.GetCameras()

        # Check if cameras are available
        if cam_list.GetSize() == 0:
            raise PySpin.SpinnakerException("No cameras found. Initialization failed.")

        # Use the first available camera
        self.camera = cam_list.GetByIndex(0)
        self.camera.Init()

        # Set the acquisition mode
        nodemap = self.camera.GetNodeMap()
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsReadable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            raise PySpin.SpinnakerException("Acquisition mode is not accessible.")

        node_acquisition_mode_ = node_acquisition_mode.GetEntryByName(mode)
        if not PySpin.IsReadable(node_acquisition_mode_):
            raise PySpin.SpinnakerException("Desired acquisition mode is not accessible.")

        acquisition_mode_ = node_acquisition_mode_.GetValue()
        node_acquisition_mode.SetIntValue(acquisition_mode_)

        # Set additional stream buffer handling if in continuous mode
        if self.acquisition_mode == 'Continuous':
            sNodemap = self.camera.GetTLStreamNodeMap()
            node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
            if not PySpin.IsReadable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
                raise PySpin.SpinnakerException("Stream buffer handling mode not accessible.")

            node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
            if not PySpin.IsReadable(node_newestonly):
                raise PySpin.SpinnakerException("NewestOnly buffer handling mode not accessible.")

            node_newestonly_mode = node_newestonly.GetValue()
            node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

        cam_list.Clear()  # Clear the camera list

    except PySpin.SpinnakerException as ex:
        raise ValueError(f"Camera initialization failed: {ex}")


def format_filename(base_name):
    """
    Formats the image file name after capture, ensuring it saves in the 'images' subdirectory.
    :param base_name: The base name of the file (e.g., 'Image')
    :return: The formatted filename as a string
    """
    # Get the parent directory (one level above the 'script' directory)
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))

    # Define the path to the 'images' subdirectory
    images_dir = os.path.join(parent_dir, "images")

    # Check if the 'images' subdirectory exists, and create it if it doesn't
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Get the current time for timestamping the filename
    current_time = time.localtime()
    formatted_time = time.strftime("%Y-%m-%d_%H-%M-%S", current_time)

    # Return the full path with the formatted filename
    return os.path.join(images_dir, f"{base_name}_captured_at_{formatted_time}.tif")


def capture_image(camera):
    """
    Captures an image using the camera and saves it as a TIFF file.
    :param camera: Camera object
    :return: None
    """
    try:
        # Initialize the camera
        camera.Init()

        # Set the acquisition mode to single frame
        camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)

        # Start acquiring images
        camera.BeginAcquisition()
        image = camera.GetNextImage()

        if image.IsIncomplete():
            # Handle incomplete images
            print(f'Image incomplete with status {image.GetImageStatus()}')
        else:
            # Dynamically format the filename using the format_filename function
            filename = format_filename("Image")  # 'Image' is the base name

            # Convert the image to RGB format for saving
            image_converted = image.Convert(PySpin.PixelFormat_RGB8, PySpin.HQ_LINEAR)

            # Convert the image to a NumPy array
            numpy_array = image_converted.GetNDArray()

            # Save the image as a TIFF file using tifffile's imwrite
            imwrite(filename, numpy_array)
            print(f"Image saved successfully at {filename}")

        # Release the image and stop acquisitions
        image.Release()
        camera.EndAcquisition()
        camera.DeInit()

    except PySpin.SpinnakerException as ex:
        # Handle exceptions raised by the PySpin library
        print("Spinnaker Exception:", ex)

    finally:
        # Cleanup and delete the camera object
        del camera


def serial_com(finish):
    """
    Reads serial input from Arduino to control camera captures and light operation.

    When the Arduino turns on the light, it sends the character 'A' over the serial interface.
    Upon detecting 'A', this function:
    - Triggers the camera to capture an image by calling capture_image().
    - Sends the character 'B' back to the Arduino to turn off the light.

    The function stops running when the Arduino sends the character 'D'.

    :param finish: Boolean indicating whether to finish the operation (typically initialized as False).
    :return: Boolean indicating completion of the imaging process.
    """
    while not finish:
        # Read a byte from the Arduino via the serial interface
        x = arduino.read()

        if x == b'A':
            # If Arduino sends 'A', capture an image
            capture_image(cam)
            print("Capture done")

            # Wait briefly before sending the 'B' command to control timing
            time.sleep(0.7)  # This controls the interval between image captures

            # Send 'B' to the Arduino to turn off the light
            arduino.write('B'.encode())

        elif x == b'D':
            # If Arduino sends 'D', mark the process as finished
            finish = True

    # Print completion message
    print("Done Imaging.")
    # Return the completion flag
    return finish


def image_again():
    """
    Prompt the user for multi-stage image capture.

    This function asks the user whether they would like to capture another image.
    - If the user enters 'Y' (or 'y'), it returns False, indicating the process should continue.
    - If the user enters 'n' (or 'N'), it returns True, indicating the process should stop.
    - If the user enters an invalid response, it prompts the user to retry.

    :return: bool
        False if the user wants to continue imaging, True if the user wants to stop.
    """
    # Prompt the user for input
    print("Image again? [Y/n]")
    re = input(">> ").lower()  # Convert input to lowercase for case-insensitivity

    # Initialize the loop control variable
    y = True
    while y:
        if re == 'y':
            # If the user enters 'y' or 'Y', stop the loop and return False (continue imaging)
            y = False
            return False
        elif re == 'n':
            # If the user enters 'n' or 'N', stop the loop and return True (stop imaging)
            y = False
            return True
        else:
            # Handle invalid input and prompt the user to retry
            print("Incorrect entry. Retry.")
            re = input(">> ").lower()  # Convert input to lowercase for retry

    # Return None explicitly as a fallback (added here for completeness)
    return None


def main():
    """
    Main camera capture loop.
    :return: None
    """
    global cam
    #cam = initialize_camera(cam)
    print("\n")
    arduino.write('C'.encode())
    print("Connect system to power now.")
    print("\n")

    done = False

    try:
        while not done:

            print("Awaiting prompt to begin imaging:")
            print("Input F for 4-capture mode or U for single capture.")

            command = input(">> ")
            if command == 'F':
                arduino.write(command.encode())
                serial_com(done)
                done = image_again()

            elif command == 'U':
                arduino.write(command.encode())
                print("Choose the light to turn on, N, S, E, or W:")
                dir = input(">> ")

                if dir == 'N':
                    arduino.write(dir.encode())
                    serial_com(done)
                    done = image_again()

                elif dir == 'S':
                    arduino.write(dir.encode())
                    serial_com(done)
                    done = image_again()

                elif dir == 'E':
                    arduino.write(dir.encode())
                    serial_com(done)
                    done = image_again()

                elif dir == 'W':
                    arduino.write(dir.encode())
                    serial_com(done)
                    done = image_again()

                else:
                    print("Incorrect entry, retry.")

            else:
                print("Incorrect command, retry.")

    except KeyboardInterrupt:
        print("\nExiting")
    finally:
        del cam
        cam_list.Clear()
        system.ReleaseInstance()
        arduino.close()


if __name__ == "__main__":
    main()
