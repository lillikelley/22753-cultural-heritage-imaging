import PySpin
import serial 
import time
import matplotlib.pyplot as plt
import numpy as np

def capture_image(cam, image_number):
    # Retrieve an image
    image_result = cam.GetNextImage()

    if image_result.IsIncomplete():
        print(f"Image {image_number} incomplete with image status %d..." % image_result.GetImageStatus())
        return None
    else:
        # Convert image to numpy array
        image_data = image_result.GetNDArray()

        # Save the image
        image_result.Save(f"image_{image_number}.jpg")
        print(f"Image saved as image_{image_number}.jpg")

        # Release the image
        image_result.Release()

        return image_data

def main():
    # Initialize serial communication
    ser = serial.Serial('COM3', 9600) # Update 'COM3' to your Arduino's serial port

    # Initialize the system
    system = PySpin.System.GetInstance()

    # Get the list of cameras
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()

    if num_cameras == 0:
        print("No cameras detected.")
        cam_list.Clear()
        system.ReleaseInstance()
        return

    # Get the first camera
    cam = cam_list.GetByIndex(0)

    try:
        # Initialize the camera
        cam.Init()

        # Set the pixel format to a supported format (e.g., Mono8)
        nodemap = cam.GetNodeMap()
        pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
        pixel_format_mono8 = pixel_format.GetEntryByName("Mono8")
        pixel_format.SetIntValue(pixel_format_mono8.GetValue())

        # Begin image acquisition
        cam.BeginAcquisition()

        led_commands = ['1', '2', '3', '4'] # Commands for North, East, South, West
        led_names = ['North', 'East', 'South', 'West']
        images = [] # List to store images

        for i in range(4):
            ser.write(led_commands[i].encode()) # Turn on the corresponding LED
            time.sleep(1) # Wait for the LED to stabilize
            image_data = capture_image(cam, i+1) # Capture the image

            if image_data is not None:
                images.append((image_data, led_names[i])) # Store image and name

            ser.write(b'0') # Turn off all LEDs
            time.sleep(1) # Wait before the next cycle

        # End image acquisition
        cam.EndAcquisition()

        # Display all images after the loop
        fig, axs = plt.subplots(1, 4, figsize=(20, 5))
        for i, (image_data, led_name) in enumerate(images):
            axs[i].imshow(image_data, cmap='gray')
            axs[i].set_title(f"{led_name} Light Image")
            axs[i].axis('off')
        plt.show()

        # Deinitialize the camera
        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)

    # Release the camera
    del cam

    # Clear the camera list before releasing the system
    cam_list.Clear()

    # Release the system
    system.ReleaseInstance()

    # Close serial communication
    ser.close()

if __name__ == "__main__":
    main()
