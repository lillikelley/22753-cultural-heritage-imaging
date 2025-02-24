# Spinnaker camera init
import serial
import time
import PySpin

# Initialize serial communication with Arduino
ser = serial.Serial('COM3', 9600)  # Replace 'COM3' with the correct port
time.sleep(2)  # Wait for the connection to establish

def initialize_camera():
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    cam = cam_list[0]
    cam.Init()
    # Follow the documentation and set up the hardware trigger
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
    camera.BeginAcquisition()
    image = camera.GetNextImage()
    image.Save('image.jpg')
    image.Release()
    image.GetImageStatus()
    camera.EndAcquisition()

def send_command(command):
    ser.write(command.encode())  # Send command to Arduino
    while ser.in_waiting > 0:
        response = ser.readline().decode('utf-8').strip()
        print(response)
