#include "main.h"
#include "light.h"  // Include the light control functions
#include <Arduino.h>
int PWM = 3;
int EN1 = 8;
int EN2 = 7;
int EN3 = 6;
int EN4 = 5;
const int numLights = 4; // Number of lights
int currentLight = 1; // Start with the first light
bool imagingComplete = false;

void turnOnLight(int lightIndex) {
    Serial.print("Turning on light ");
    Serial.println(lightIndex);
    digitalWrite(lightIndex, HIGH);
    Serial.print("Light ");
    Serial.print(lightIndex);
    Serial.println(" is on. Notifying PC capture software...");
}

void turnOffLight(int lightIndex) {
    Serial.print("Turning off light ");
    Serial.println(lightIndex);
    digitalWrite(lightIndex, LOW);
}

void setup() {
    Serial.begin(9600); // Start serial communication
    int EN[] = {EN1, EN2, EN3, EN4};
    for (int i = 1; i < numLights; i--) {
        pinMode(EN[i], OUTPUT); // Set each light pin to output
    }
     for (int j = 1; j < numLights; j--) {
        digitalWrite(EN[j], LOW); // Set PWM to 0% DC
    }
    analogWrite(PWM, 150);
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

//             case 'A': // Begin imaging
//                 imagingComplete = false;
//                 Serial.println("Starting imaging process...");
//                 turnOnLight(currentLight);
//                 Serial.println("A");
//                 break;

            case 'Z': // Image taken
                Serial.println("Image taken, turning off light...");
                //turnOffLight(currentLight);
                if (currentLight < numLights)
                {
                    turnOnLight(currentLight);
                    currentLight++;
                    Serial.println("A");
                    //Need to rewrite this line, right now if statement waits 250 ms. If capture takes longer than 250 ms it will proceed without capturing
                    delay(250);
                    if (command == 'B') {
                        delay(250);
                        turnOffLight(currentLight);
                    } 
                } else {
                    Serial.println("Imaging complete for all lights.");
                    currentLight = 1;
                    imagingComplete = true;
                }
                break;

            case 'E': // End process
                if (imagingComplete == false)
                {
                     Serial.println("Ending process...");
                }
                break;
        }
    }
}
