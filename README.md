# CMPE497
MSD Team MISHA Software Repository

This project integrates an Arduino-based control system with a FLIR Blackfly 3 camera using the Spinnaker Python SDK. The system captures images with varying lighting conditions and processes the data to enhance imaging capabilities.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

This project aims to automate an imaging process using an Arduino to control multiple lights and a FLIR Blackfly 3 camera. The setup captures images with different lighting conditions and processes them using Python.

## Features

- **Arduino Control**: Manages light states (on/off) for multiple lights.
- **Image Capture**: Integrates with the FLIR Blackfly 3 camera using the Spinnaker SDK.
- **Serial Communication**: Uses Python to send and receive commands from Arduino.
- **Modular Code Structure**: Clean separation of functionalities with header and source files.

## Hardware Requirements

- Arduino Board (e.g., Arduino Uno)
- FLIR Blackfly 3 Camera
- LEDs or lights controlled by the Arduino
- USB cables for Arduino and camera

## Software Requirements

- [Arduino IDE](https://www.arduino.cc/en/software) to upload the sketch to the Arduino.
- Python 3.7+
- [PySerial](https://pythonhosted.org/pyserial/) library
- [PySpin](https://github.com/Teledyne-MV/Spinnaker-Examples) library

## Installation

1. **Arduino Setup**:
   - Open the Arduino IDE.
   - Upload the provided `main.cpp` and `light.cpp` files to the Arduino.

2. **Python Setup**:
   - Clone this repository.
   - Install the required Python libraries:
     ```sh
     pip install pyserial PySpin
     ```

3. **Spinnaker SDK**:
   - Follow the installation instructions on the [Spinnaker SDK page](https://www.flir.com/products/spinnaker-sdk/).

## Usage

1. **Connect Hardware**:
   - Connect the Arduino to your computer.
   - Connect the FLIR Blackfly 3 camera.

2. **Run Python Script**:
   - Execute `main.py` to start the process:
     ```sh
     python main.py
     ```

3. **Arduino Commands**:
   - Commands are sent from the Python script to the Arduino to control the light states and capture images.

## Contributing

Contributions are welcome! Please fork this repository and submit pull requests for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please contact [Your Name](mailto:your.email@example.com).
