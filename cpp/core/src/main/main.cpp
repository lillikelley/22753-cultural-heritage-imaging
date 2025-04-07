#include "main.h"
#include "light.h"  // Include the light control functions
#include <Arduino.h>

const int numLights = 4; // Number of lights
int currentLight = 0; // Start with the first light
bool imagingComplete = false;

void setup() {
    Serial.begin(9600); // Start serial communication
    for (int i = 0; i < numLights; i++) {
        pinMode(i, OUTPUT); // Set each light pin to output
    }
    Serial.println("System Powered On. Awaiting connection...");
}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();

        switch (command) {
            case 'C': // Connection established
                Serial.println("Connection acknowledged.");
                Serial.println("Awaiting prompt to begin imaging...");
                break;

            case 'I': // Begin imaging
                imagingComplete = false;
                Serial.println("Starting imaging process...");
                turnOnLight(currentLight);
                break;

            case 'T': // Image taken
                Serial.println("Image taken, turning off light...");
                turnOffLight(currentLight);
                currentLight++;
                if (currentLight < numLights) {
                    turnOnLight(currentLight);
                } else {
                    Serial.println("Imaging complete for all lights.");
                    currentLight = 0;
                    imagingComplete = true;
                }
                break;

            case 'E': // End process
                Serial.println("Ending process...");
                for (int i = 0; i < numLights; i++) {
                    turnOffLight(i);
                }
                break;
        }
    }
}
