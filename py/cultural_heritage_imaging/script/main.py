from flir_controller import CameraController, show_help


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

    # Show help message
    controller = CameraController()
    show_help()
    controller.run()


if __name__ == "__main__":
    main()