# Spinnaker camera init
import serial
import time
import PySpin
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(port.device)

# Initialize serial communication with Arduino
arduino = serial.Serial('COM5', 9600)  # Replace 'COM3' with the correct port
time.sleep(2)  # Wait for the connection to establish
system = PySpin.System.GetInstance() # Initialize the system

# Get the list of cameras
cam_list = system.GetCameras()
num_cameras = cam_list.GetSize()
cam = cam_list[0]
# Get the first camera
cam = cam_list.GetByIndex(0)

if num_cameras == 0:
    print("No cameras detected.")
    cam_list.Clear()
    system.ReleaseInstance()

def initialize_camera():
    try:
        cam.Init()
    except PySpin.SpinnakerException as e:
        print(f"Camera initialization failed: {e}")
        system.ReleaseInstance()    # Follow the documentation and set up the hardware trigger
    cam.LineSelector.SetValue(PySpin.LineSelector_Line2)
    cam.V3_3Enable.SetValue(True)
    cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    cam.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
    cam.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
    cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
    return cam

def capture_image(camera):
    # Set acquisition mode to acquire a single frame
    camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)

    # Set the pixel format to a supported format (e.g., Mono8)
    nodemap = cam.GetNodeMap()
    pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
    pixel_format_mono8 = pixel_format.GetEntryByName("Mono8")
    pixel_format.SetIntValue(pixel_format_mono8.GetValue())
    camera.BeginAcquisition()
    print("Camera acquisition started.")

    # Get an image and save it
    image = camera.GetNextImage()
    image.Save('image.jpg')
    image.Release()
    image.GetImageStatus()
    camera.EndAcquisition()
    print("Camera acquisition ended.")

    # Display all images after the loop
    fig, axs = plt.subplots(1, 4, figsize=(20, 5))
    for i, (image_data, led_name) in enumerate(images):
        axs[i].imshow(image_data, cmap='gray')
        axs[i].set_title(f"{led_name} Light Image")
        axs[i].axis('off')
    plt.show()

# def send_command(command):
#     ser.write(bytearray(command.encode()))  # Send command to Arduino
#     print(command)
#     while ser.in_waiting > 0:
#         response = ser.readline().decode('utf-8').strip()
#         print(response)

def main():
    cam = initialize_camera()
    arduino.write(b'C')  # Send connection established command
    print("Connection established.")

    while True: # b prefix for byte marker in python
        command = arduino.read()  # Read command from Arduino
        if command == b'T':
            arduino.write(b'Z')  # Send image taken command
            print("Image taken.")
        if command == b'A':
            capture_image(cam)  # Capture image
            arduino.write(b'B')
        else:
            break  # End process

    cam.DeInit()
    # Clear the camera list before releasing the system
    cam_list.Clear()
    # Release the system
    system.ReleaseInstance()
    arduino.close()  # Close the serial connection

if __name__ == "__main__":
    main()
