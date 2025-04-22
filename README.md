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
- [License](#license)
- [Contact](#contact)

## Introduction

This project aims to automate an imaging process using an Arduino to control multiple lights and a FLIR Blackfly 3 camera. The setup captures images with different lighting conditions and processes them using Python.

## Features

- **Arduino Control**: Manages light states (on/off) for multiple lights.
- **Image Capture**: Integrates with the FLIR Blackfly 3 camera using the Spinnaker SDK.
- **Serial Communication**: Uses Python to send and receive commands from Arduino.

## Hardware Requirements

- Arduino Board (e.g., Arduino Nano, Seeeduino Nano Development Board)
- FLIR Blackfly 3 Camera
- LEDs or lights controlled by the Arduino
- USB cables for Arduino and camera

## Software Requirements

- [Arduino IDE](https://www.arduino.cc/en/software) to upload the sketch to the Arduino.
- Python 3.10 (due to Spinnaker Python SDK version support)
- [PySerial](https://pythonhosted.org/pyserial/) library
- [PySpin](https://github.com/Teledyne-MV/Spinnaker-Examples) library

## Installation

1. **Arduino Setup**:
   - Open the Arduino IDE.
   - Upload the provided `main.cpp`, `light.cpp`, and `main.ino` files to the Arduino.

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please contact:
   - [Lilli Kelley](mailto:lmk8240@rit.edu)
   - [Will Shuley](mailto:wps8051@rit.edu)

