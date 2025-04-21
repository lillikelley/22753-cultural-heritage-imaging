int PWM = 3; // PWM pin for light brightness
int EN1 = 8; // Enable pin for light 1 (North)
int EN2 = 7; // Enable pin for light 2 (East)
int EN3 = 6; // Enable pin for light 3 (South)
int EN4 = 5; // Enable pin for light 4 (West)
int EN[] = {EN1, EN2, EN3, EN4}; // Array of enable pins
const int numLights = 4; // Number of lights
int currentLight = 0; // Current light index for F mode
const unsigned long timeout = 5000; // Timeout in milliseconds for serial reads
int pwmValue = 200; // Default PWM value (~78% duty cycle)

void turnOnLight(int lightIndex) {
    digitalWrite(EN[lightIndex], HIGH);
    Serial.print("DEBUG: Turning on light ");
    Serial.println(lightIndex);
    Serial.write('L'); // Send light confirmation
    Serial.write(lightIndex); // Send light index (0-3)
}

void turnOffLight(int lightIndex) {
    digitalWrite(EN[lightIndex], LOW);
    Serial.print("DEBUG: Turning off light ");
    Serial.println(lightIndex);
}

void resetState() {
    for (int i = 0; i < numLights; i++) {
        digitalWrite(EN[i], LOW);
    }
    currentLight = 0;
    Serial.println("DEBUG: Reset state - all lights off, currentLight = 0");
}

void setup() {
    Serial.begin(9600); // Start serial communication at 9600 baud
    for (int i = 0; i < numLights; i++) {
        pinMode(EN[i], OUTPUT); // Set each light pin to output
        digitalWrite(EN[i], LOW); // Ensure lights are off
    }
    analogWrite(PWM, pwmValue); // Set initial PWM value
    Serial.println("DEBUG: Setup complete, PWM set to 200");
}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();
        Serial.print("DEBUG: Received command: ");
        Serial.println(command);

        unsigned long startTime; // Declare startTime for switch scope
        bool receivedB; // Declare receivedB for switch scope

        switch (command) {
            case 'C': // Connection established
                resetState();
                break;

            case 'P': // Set PWM value
                while (Serial.available() == 0 && millis() < timeout) {} // Wait for PWM value
                if (Serial.available() > 0) {
                    pwmValue = Serial.read(); // Read PWM value (0-255)
                    analogWrite(PWM, pwmValue);
                    Serial.print("DEBUG: Set PWM to ");
                    Serial.println(pwmValue);
                } else {
                    Serial.println("DEBUG: Error: Timeout waiting for PWM value");
                    Serial.write('E');
                }
                break;

            case 'R': // Reset state
                resetState();
                break;

            case 'F': // Four-capture mode
                currentLight = 0; // Reset currentLight
                while (currentLight < numLights) {
                    turnOnLight(currentLight);
                    Serial.write('A');

                    startTime = millis();
                    receivedB = false;
                    while (!receivedB && (millis() - startTime < timeout)) {
                        if (Serial.available() > 0) {
                            char x = Serial.read();
                            if (x == 'B') {
                                turnOffLight(currentLight);
                                receivedB = true;
                            }
                        }
                    }

                    if (!receivedB) {
                        Serial.println("DEBUG: Error: Timeout waiting for B");
                        Serial.write('E');
                        turnOffLight(currentLight);
                        return;
                    }

                    currentLight++;
                }
                Serial.println("DEBUG: Four-capture mode complete");
                Serial.write('D');
                break;

            case 'U': // Single capture mode
                startTime = millis();
                bool validLight = false;
                int lightIndex = -1;

                // Map light directions to indices: N=0, E=1, S=2, W=3
                while (!validLight && (millis() - startTime < timeout)) {
                    if (Serial.available() > 0) {
                        char direction = Serial.read();
                        Serial.print("DEBUG: Received direction: ");
                        Serial.println(direction);
                        switch (direction) {
                            case 'N': lightIndex = 0; break;
                            case 'E': lightIndex = 1; break;
                            case 'S': lightIndex = 2; break;
                            case 'W': lightIndex = 3; break;
                            default: continue;
                        }
                        validLight = true;
                    }
                }

                if (!validLight) {
                    Serial.println("DEBUG: Error: Timeout or no valid direction");
                    Serial.write('E');
                    return;
                }

                turnOnLight(lightIndex);
                Serial.write('A');

                startTime = millis();
                receivedB = false;
                while (!receivedB && (millis() - startTime < timeout)) {
                    if (Serial.available() > 0) {
                        char x = Serial.read();
                        if (x == 'B') {
                            turnOffLight(lightIndex);
                            receivedB = true;
                        }
                    }
                }

                if (!receivedB) {
                    Serial.println("DEBUG: Error: Timeout waiting for B");
                    Serial.write('E');
                    turnOffLight(lightIndex);
                    return;
                }

                Serial.println("DEBUG: Single capture mode complete");
                Serial.write('D');
                break;

            default:
                Serial.print("DEBUG: Error: Invalid command: ");
                Serial.println(command);
                Serial.write('E');
                break;
        }
    }
}