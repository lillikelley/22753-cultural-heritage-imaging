# MISHA 3D
**Cultural Heritage Imaging System**
 
This project integrates an Arduino-based light control system with a FLIR Blackfly 3 camera using the Spinnaker Python SDK. 
The system captures Photometric Stereo images under directional lighting (N, S, E, W) and supports flat-field, calibration, and target object imaging workflows.


## Table of Contents
 
- [Introduction](#introduction)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [License](#license)
- [Contact](#contact)


## Introduction

The system automates a multi-light imaging process for cultural heritage documentation. 
An Arduino controls four directional LED lights (North, South, East, West) via PWM-driven enable pins. 
A FLIR Blackfly 3 camera captures images in sync with each light via a serial handshake protocol. 
Images are saved as 16-bit TIFFs with metadata timestamps, and previous captures are automatically archived.


## Hardware Requirements

- Arduino Board (e.g., Arduino Nano, Seeeduino Nano Development Board)
- FLIR Blackfly 3 Camera
- Four directional LEDs controlled by the Arduino
- USB cables for Arduino and camera


## Software Requirements

- Python **3.10** — required for Spinnaker SDK compatibility
- [Arduino IDE](https://www.arduino.cc/en/software) — for uploading firmware
- [Spinnaker SDK](https://www.flir.com/products/spinnaker-sdk/) — FLIR's camera SDK (install before PySpin)
- Python libraries:
  ```
  pyserial
  PySpin (installed via Spinnaker SDK)
  tifffile
  numpy
  ```

## Project Structure
 
```
cultural_heritage_imaging/
├── py/
│   └── cultural_heritage_imaging/
│       └── script/
│           ├── main.py                # Entry point
│           ├── flir_controller.py     # CameraController class (camera + run loop)
│           └── arduino_controller.py  # Serial communication functions
├── arduino/
│   └── main/
│       └── main.ino                   # Arduino firmware
└── images/                            # Captured TIFFs (auto-created)
    └── archive/                       # Previous captures (auto-created)
```


## Installation
 
1. **Upload Arduino firmware**
   - Open `arduino/main/main.ino` in the Arduino IDE
   - Select your board and port
   - Upload
 
2. **Install Spinnaker SDK**
   - Download and install from the [FLIR Spinnaker SDK page](https://www.flir.com/products/spinnaker-sdk/)
   - This installs PySpin — do this before installing Python libraries
 
3. **Install Python dependencies**
   ```sh
   pip install pyserial tifffile numpy
   ```
 
4. **Clone the repository**
   ```sh
   git clone https://github.com/your-org/22753-cultural-heritage-imaging.git
   ```
 
5. **Configure serial port**
   - In `flir_controller.py`, set `serial_port` to match your machine if needed (default: `'COM5'`).

 
## Usage
 
1. **Unplug the power supply** from the light controller before starting (the program will prompt you to confirm this)
2. Connect the Arduino and camera via USB
3. Run the script:
   ```sh
   python main.py
   ```
4. Follow the on-screen prompts to connect power and begin imaging

 
## Commands
 
Once running, the following commands are available at the prompt:
 
| Command | Description                                                                 |
|---------|-----------------------------------------------------------------------------|
| `F`     | Four-capture mode — fires N, S, E, W lights in sequence, one image per light |
| `U`     | Single-capture mode — choose one light direction and capture one image      |
| `M`     | Manual light toggle — turn lights on/off without capturing                  |
| `E`     | Set exposure time interactively (in seconds)                                |
| `P`     | Set PWM brightness value (0–255)                                            |
| `R`     | Reset Arduino                                                               |
| `H`     | Show help                                                                   |
| `Q`     | Quit                                                                        |
 
**Image types** (prompted before F and U captures):
 
| Key | Type            |
|-----|-----------------|
| `A` | Flat-fielding   |
| `B` | Calibration     |
| `C` | Target object   |
 
Output filenames follow the pattern `{type}_{direction}.tiff` (e.g. `target_north.tiff`). If a file already exists, it is moved to `images/archive/` with a timestamp before the new image is saved.
 
After each capture, a live histogram summary is printed showing mean brightness, shadow/highlight percentages, clipping, and a suggested exposure adjustment if needed.
 
## License
 
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
 
## Contact
 
- [Lilli Kelley](mailto:lmk8240@rit.edu)

