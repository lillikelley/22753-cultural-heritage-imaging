# Spinnaker camera init
import os
import sys
import time

import PySpin
import serial

#Gain and exposure values: 12801 exposure, gain = 0, gamma = 1.

#Ensures that power supply is unplugged before opening serial interface. The power supply only
#needs to be removed when the python script is re-run, there is an option for continued imaging.
b = True
while (b):
    print("Is power supply unplugged? [Y/n]")
    a = input("<< ").strip().upper()
    if a == 'Y':
        b = False
    elif a == 'N':
        print("Unplug power supply.")
        b = True
    else:
        print("Incorrect entry. Try again.")
        b = True

# Initializes serial interface with arduino, 9600 baud rate
arduino = serial.Serial('COM6', 9600, timeout=1)
arduino.setDTR(False)

# Waits for 0.2 seconds for serial interface to connect
time.sleep(0.2)
arduino.flushInput()

# Initializes PySpin objects and camera
system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
num_cams = cam_list.GetSize()

# Check statement to make sure that the camera is detected 
if num_cams == 0:
    print("No cameras detected\n")
    print("Try unplugging and re-plugging in camera USB")
    cam_list.Clear()
    system.ReleaseInstance()
    sys.exit()
else:
    print("Camera detected")

# Specifies the camera object as the first in the cam_list vector
cam = cam_list.GetByIndex(0)

# Function set_exposure turns off auto-exposure, and sets the exposure value that is passed into 
# the function when it is called in capture_image()
def set_exposure(nodemap, exposure_time):
    try:
        
        # Turn off auto exposure
        exposure_auto = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if PySpin.IsAvailable(exposure_auto) and PySpin.IsWritable(exposure_auto):
            exposure_auto_off = exposure_auto.GetEntryByName('Off')
            if PySpin.IsAvailable(exposure_auto_off) and PySpin.IsReadable(exposure_auto_off):
                exposure_auto.SetIntValue(exposure_auto_off.GetValue())
        
        # Set the exposure time to the value of exposure_time, which was passed into the function
        exposure_time_node = PySpin.CFloatPtr(nodemap.GetNode('ExposureTime'))
        if PySpin.IsAvailable(exposure_time_node) and PySpin.IsWritable(exposure_time_node):
            exposure_bounds = [exposure_time_node.GetMin(), exposure_time_node.GetMax()]
            exposure_time = max(min(exposure_time, exposure_bounds[1]), exposure_bounds[0])
            exposure_time_node.SetValue(exposure_time)
        else:
            print("Set Exposure failed.")
            
    except PySpin.SpinnakerException as ex:
        print("Error setting exposure: ", ex)
    
# Function to set the gain of the camera
def set_gain(nodemap, gain_value):
    try: 
    
        # Turn off auto gain
        gain_auto = PySpin.CEnumerationPtr(nodemap.GetNode('GainAuto'))
        if PySpin.IsAvailable(gain_auto) and PySpin.IsWritable(gain_auto):
            gain_auto_off = gain_auto.GetEntryByName('Off')
            if PySpin.IsAvailable(gain_auto_off) and PySpin.IsReadable(gain_auto_off):
                gain_auto.SetIntValue(gain_auto_off.GetValue())
        
        # Set the gain to the value of gain_value, which was passed into the function
        gain_node = PySpin.CFloatPtr(nodemap.GetNode('Gain'))
        if PySpin.IsAvailable(gain_node) and PySpin.IsWritable(gain_node):
            gain_bounds = [gain_node.GetMin(), gain_node.GetMax()]
            gain_value = max(min(gain_value, gain_bounds[1]), gain_bounds[0])
            gain_node.SetValue(gain_value)
        
    except PySpin.SpinnakerException as ex:
        print("Error setting gain: ", ex)

# Function to set the value of gamma in the camera
def set_gamma(nodemap, gamma_value):
    try:
        
        # Ensure that the gamma value is writable
        gamma_enable_node = PySpin.CBooleanPtr(nodemap.GetNode('GammaEnable'))
        if PySpin.IsAvailable(gamma_enable_node) and PySpin.IsWritable(gamma_enable_node):
            gamma_enable_node.SetValue(True)
        
        # Set the value of gamma to the gamma_value, which was passed into the function
        gamma_node = PySpin.CFloatPtr(nodemap.GetNode('Gamma'))
        if PySpin.IsAvailable(gamma_node) and PySpin.IsWritable(gamma_node):
            gamma_bounds = [gamma_node.GetMin(), gamma_node.GetMax()]
            gamma_value = max(min(gamma_value, gamma_bounds[1]), gamma_bounds[0])
            gamma_node.SetValue(gamma_value)
    
    except PySpin.SpinnakerException as ex:
        print("Error setting gamma: ", ex)

# Function capture_image() involves the necessary initialization and capture functions for 
# the camera. It takes as an argument a camera object, which in this case is the global "cam" object. 
def capture_image(camera):
    try:
        
        # Initialize camera object 
        camera.Init()
        
        # Get a list of nodes to use to set camera settings
        nodemap = camera.GetNodeMap()
        # Set pixel format to Mono8
        pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
        mono8 = pixel_format.GetEntryByName('Mono8')  # Or 'RGB8' if using color camera
        pixel_format.SetIntValue(mono8.GetValue())
        
        # Hardcode exposure, gain, and gamma values. Exposure is set to 12801 microseconds
        set_exposure(nodemap, 12801) #This integer sets the exposure value in microseconds
        set_gain(nodemap, 0)
        set_gamma(nodemap, 1)
        
        
        #Set the acquisition mode of the camera to take a single image rather than multiple or continuous images
        camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)  
        camera.BeginAcquisition()
        
        #Captures the next image
        image = camera.GetNextImage()
        print("[DEBUG] Image acquired.")

        #Check statement to ensure that the image was captured
        if image.IsIncomplete():
            print(f'Image incomplete with status {image.GetImageStatus()}')
        else:
            #saves the image with the appropriate file format
            filename = format_filename()
            if filename is None:
                print("[INFO] Skipping image save.")
            else:
                image.Save(filename)
                print("[DEBUG] Image saved.")

        #End acquisition and de-initialize the camera object
        image.Release()
        camera.EndAcquisition()
        camera.DeInit()
        
    except PySpin.SpinnakerException as ex:
        print("Spinnaker Exception:", ex)
    finally:
        
        #Delete camera object
        del camera
        print(f'Image saved successfully')

# Function format_filename() formats the .tif file to be saved, based on the type of image
# captured: either flat fielding, mirror ball (calibration), or object. This is for easy transfer
# into the 3D processing software.
def format_filename():
    inc_map = {
        1: "north",
        2: "east",
        3: "south",
        4: "west",
    }

    if typeIm == 'A':
        strng = 'flat_' + inc_map[inc]
    elif typeIm == 'B':
        strng = 'calibration_' + inc_map[inc]
    else:
        strng = 'target_' + inc_map[inc]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "Output Images")
    os.makedirs(output_dir, exist_ok=True)

    base_filename = os.path.join(output_dir, strng)
    file_path = base_filename + '.tiff'

    if os.path.exists(file_path):
        print(f"\n[WARNING] File already exists: {file_path}")
        while True:
            choice = input("Overwrite (O), Auto-Rename (R), or Cancel (C)? [O/R/C]: ").strip().upper()
            if choice == 'O':
                break
            elif choice == 'R':
                # Auto-increment filename
                counter = 1
                while True:
                    new_file_path = f"{base_filename}_{counter}.tiff"
                    if not os.path.exists(new_file_path):
                        file_path = new_file_path
                        break
                    counter += 1
                break
            elif choice == 'C':
                print("Cancelled image save.")
                return None
            else:
                print("Invalid input. Please enter O, R, or C.")

    print(f"[DEBUG] Saving image to: {file_path}")
    return file_path


# Function 'serialCom' takes false boolean, and reads serial input from Arduino. Upon turning on a light, 
# the Arduino sends character 'A' over serial interface. Once 'A' is read in serialCom, it calls capture_image()
# to trigger the camera to capture. It then sends 'B' over the serial interface to the Arduino to turn off the light.
def serialCom(finish):
    global inc
    while not (finish):
    
        # Read serial data from the arduino
        x = arduino.read()
        if x == b'A':
            
            # Once the Arduino sends an 'A', the camera is triggered to capture an image
            capture_image(cam)
            time.sleep(0.7)  # This line controls time between captures
            
            # Write a 'B' to the arduino to move on to the next light
            arduino.write(('B').encode())
            
            # The inc variable is used to encode the direction into the file naming of the saved image
            inc += 1
            
        # The other character that the arduino will send is a 'D', which indicates that imaging is complete.
        elif x == b'D':
            finish = True
            
    print("Done Imaging.")
    return finish

# Function to prompt the user to either end or continue the imaging session
def imageAgain():
    print("Image again? [Y/n]")
    re = input(">> ").strip().upper()
    y = True
    while (y):
        if re == 'Y':
            y = False
            return False
        elif re == 'N':
            y = False
            return True
        else:
            print("Incorrect entry. Retry.")
            y = True


def main():

    # Sets the following as a global variables to be used in other functions
    global cam
    global typeIm
    global inc
    
    # Prompts the user to connect system to power, and plug in the 9V
    print("\n")
    arduino.write(('C').encode())
    print("Connect system to power now.")
    print("\n")

    # Boolean variable used for continous imaging without requiring re-running the python script
    done = False

    try:
        while not (done):
        
            #The variable inc is used to format the file according to the direction of the lights (it is used in function format_filename())
            inc = 1
            print("Awaiting prompt to begin imaging:")
            
            #Prompt user to select the type of image. This is used for formatting the filename for use in the processing software
            print("Input type:\nA: Flat-fielding\nB: Calibration\nC: Target Object")
            choose = False
            while not (choose):
                typeIm = input(">> ").strip().upper()
                if typeIm not in ('A', 'B', 'C'):
                    print("Incorrect entry. Retry.")
                    choose = False
                else:
                    choose = True
                
            #Prompt user to select four-capture mode or single capture mode which turns on a specific light
            print("Input F for 4-capture mode or U for single capture.")
            command = input(">> ").strip().upper()
            if command == 'F':
                
                # Send the command to the arduino to turn on appropriate lights
                arduino.write(command.encode())
                
                # Call the function to serial interface with the arduino
                serialCom(done)
                
                # Gives the option to end the imaging session and exit from the python script
                done = imageAgain()

            elif command == 'U':
                arduino.write(command.encode())
                print("Choose the light to turn on, N, S, E, or W:")
                dir = input(">> ").strip().upper()

                if dir == 'N':
                    arduino.write(dir.encode())
                    inc = 1
                    serialCom(done)
                    done = imageAgain()

                elif dir == 'S':
                    arduino.write(dir.encode())
                    inc = 3
                    serialCom(done)
                    done = imageAgain()

                elif dir == 'E':
                    arduino.write(dir.encode())
                    inc = 2
                    serialCom(done)
                    done = imageAgain()

                elif dir == 'W':
                    arduino.write(dir.encode())
                    inc = 4
                    serialCom(done)
                    done = imageAgain()

                else:
                    print("Incorrect entry, retry.")

            else:
                print("Incorrect command, retry.")


    except KeyboardInterrupt:
        print("\nExiting")
    finally:
    
        #Delete camera object 
        del cam
        
        #clear necessary camera objects and release system instance
        cam_list.Clear()
        system.ReleaseInstance()
        
        #close the serial communication between arduino and python 
        arduino.close()

if __name__ == "__main__":
    main()
