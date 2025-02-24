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
    return cam

def capture_image(camera):
    camera.BeginAcquisition()
    image = camera.GetNextImage()
    image.Save('image.jpg')
    image.Release()
    camera.EndAcquisition()

def send_command(command):
    ser.write(command.encode())  # Send command to Arduino
    while ser.in_waiting > 0:
        response = ser.readline().decode('utf-8').strip()
        print(response)
