# Spinnaker camera init
import serial
import sys
import time
import PySpin
import os
import numpy
#import matplotlib.pyplot as plot
from tifffile import imwrite

b = True
while (b):
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

arduino = serial.Serial('COM3', 9600, timeout=1)
arduino.setDTR(False)
time.sleep(0.2)
arduino.flushInput()

#Initialize spinnaker system
system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
cam = cam_list.GetByIndex(0)


def initialize_camera():
    
    try:    
        num_cameras = cam_list.GetSize()
        
        if num_cameras == 0:
            raise PySpin.SpinnakerException('No Cameras Found! - Aborting')

        # Get the first camera in the camera list. Assuming only one camera is connected
        cam = cam_list.GetByIndex(0)
        
        nodemap_tldevice = cam.GetTLDeviceNodeMap()
        
        cam.Init()
        
        nodemap = cam.GetNodeMap()
        
        sNodemap = cam.GetTLStreamNodeMap()
        node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsReadable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
            raise PySpin.SpinnakerException('Unable to set stream buffer handling - Aborting')

        # Set buffer handling to 'newest only'. This ensures the newest images is retrieved from the camera
        node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
        if not PySpin.IsReadable(node_newestonly):
            raise PySpin.SpinnakerException('Unable to set stream buffer handling - Aborting')
        node_bufferhandling_mode.SetIntValue(node_newestonly.GetValue())
        
        # Set acquisition mode to acquire a single frame
        cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
        
        # ---Enable automatic exposure---
        # cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)
        # ---Enable automatic gain---
        # cam.GainAuto.SetValue(PySpin.GainAuto_Continuous)

        # ---Disable Auto Gain - Set gain for the camera. Ensure not over max settable value---
        # Gain  = [min:0 - max:27dB]
        # cam.GainAuto.SetValue(PySpin.GainAuto_Off)
        # gain_to_set = min(Gain, cam.Gain.GetMax())
        # cam.Gain.SetValue(gain_to_set)

        # ---Disable Auto Exposure - Set Exposure time for the camera. Ensure not over max settable value---
        # Provide Exposure time in seconds. [min:69 microseconds - max:30 seconds]
        # cam.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)  # Disable auto exposure target grey
        # cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off) # Disable automatic exposure
        # exposure_time = float(Exposure time) * 1e6 # Convert exposure time to micro-seconds. Ensure not over max settable value
        # exposure_time_to_set = min(cam.ExposureTime.GetMax(), exposure_time)
        # cam.ExposureTime.SetValue(exposure_time_to_set) # Set exposure time of the camera

    except PySpin.SpinnakerException as e:
        print(f"Camera initialization failed: {e}")
        system.ReleaseInstance()  # Follow the documentation and set up the hardware trigger

    return {"Success": True, "Camera": cam, "Cam List": cam_list, "System": system, "NodeMap": nodemap,
            "NodeMap TLDevice": nodemap_tldevice}


def capture_image(camera):
    camera.BeginAcquisition()
    image = camera.GetNextImage()
        
    if image.IsIncomplete():
        print(f'Image incomplete with status {image.GetImageStatus()}')
    #else:
        #numpy_array = image.GetNDArray()
        
    image.Release()
    save_picture(image)
    print("Image saved successfully")
    camera.EndAcquisition()

def save_picture(image_to_save):
    # Get current time
    current_time = time.localtime()  # Returns struct_time (local time)

    # Format the time to be included in the filename (e.g., YYYY-MM-DD_HH-MM-SS)
    formatted_time = time.strftime("%Y-%m-%d_%H-%M-%S", current_time)

    # Check if 'Images' directory exists, and create it if it doesn't
    if not os.path.exists("Images"):
        os.makedirs("Images")

    # Set path to save images (using os.path.join for cross-platform compatibility)
    save_path = os.path.join("Images", f"captured_at_{formatted_time}.tif")

    imwrite(save_path, image_to_save, shape=image_to_save.shape)
    print("Image saved at", save_path)


# Function 'serialCom' takes false boolean, and reas serial input from Arduino. Upon turning on a light, 
# the Arduino sends character 'A' over serial interface. Once 'A' is read in serialCom, it calls capture_image()
# to trigger the camera to capture. It then sends 'B' over the serial interface to the Arduino to turn off the light.
def serialCom(finish):
    while not (finish):
        x = arduino.read()
        if x == b'A':
            capture_image(cam)
            print("Capture done")
            time.sleep(0.7)  # This line controls time between captures, important
            arduino.write(('B').encode())
        elif x == b'D':
            finish = True
    print("Done Imaging.")
    return finish


def imageAgain():
    print("Image again? [Y/n]")
    re = input(">> ")
    y = True
    while (y):
        if re == 'Y':
            return False
            y = False
        elif re == 'n':
            return True
            y = False
        else:
            print("Incorrect entry. Retry.")
            y = True


def main():
    cam = initialize_camera()
    print("\n")
    arduino.write(('C').encode())
    print("Connect system to power now.")
    print("\n")

    done = False

    try:
        while not (done):

            print("Awaiting prompt to begin imaging:")
            print("Input F for 4-capture mode or U for single capture.")

            command = input(">> ")
            if command == 'F':
                arduino.write(command.encode())
                serialCom(done)
                done = imageAgain()

            elif command == 'U':
                arduino.write(command.encode())
                print("Choose the light to turn on, N, S, E, or W:")
                dir = input(">> ")

                if dir == 'N':
                    arduino.write(dir.encode())
                    serialCom(done)
                    done = imageAgain()

                elif dir == 'S':
                    arduino.write(dir.encode())
                    serialCom(done)
                    done = imageAgain()

                elif dir == 'E':
                    arduino.write(dir.encode())
                    serialCom(done)
                    done = imageAgain()

                elif dir == 'W':
                    arduino.write(dir.encode())
                    serialCom(done)
                    done = imageAgain()

                else:
                    print("Incorrect entry, retry.")

            else:
                print("Incorrect command, retry.")


    except KeyboardInterrupt:
        print("\nExiting")
    finally:

        cam.DeInit()
        cam_list.Clear()
        system.ReleaseInstance()
        arduino.close()


if __name__ == "__main__":
    main()
