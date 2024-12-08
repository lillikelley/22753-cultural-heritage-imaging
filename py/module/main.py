from module import initialize_camera, capture_image, send_command, ser

def main():
    cam = initialize_camera()
    send_command('C')  # Send connection established command

    while True:
        command = ser.read()  # Read command from Arduino
        if command == b'I':
            capture_image(cam)  # Capture image
            send_command('T')  # Send image taken command
        elif command == b'E':
            break  # End process

    cam.DeInit()
    cam_list.Clear()
    system.ReleaseInstance()
    ser.close()  # Close the serial connection

if __name__ == "__main__":
    main()
