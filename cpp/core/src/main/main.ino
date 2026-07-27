int PWM = 9;
int EN1 = 6;    // East (physically on pin 6)
int EN2 = 5;    // West (physically on pin 5)
int EN3 = 8;    // North (physically on pin 8)
int EN4 = 7;    // South (physically on pin 7)
int EN[] = {EN1, EN2, EN3, EN4};

const int numLights = 4;
int currentLight = 0;
bool imagingComplete = false;

// Index i in EN[]/the F-loop maps to this letter. Must stay in sync
// with the Python side: arduino_controller lights = ['E','W','N','S'].
const char LIGHT_LETTER[] = {'E', 'W', 'N', 'S'};

void turnOnLight(int lightIndex) {
    digitalWrite(EN[lightIndex], HIGH);
}

void turnOffLight(int lightIndex) {
    digitalWrite(EN[lightIndex], LOW);
}

// Block until at least one byte is available, then return it.
// Replaces bare Serial.read(), which returns -1 on an empty buffer.
char readBlocking() {
    while (Serial.available() < 1) {
        // spin
    }
    return Serial.read();
}

void setup() {
    Serial.begin(9600);

    for (int i = 0; i < numLights; i++) {
        pinMode(EN[i], OUTPUT);
    }

    for (int j = 0; j < numLights; j++) {
        digitalWrite(EN[j], LOW);
    }

    //Raise PWM frequency on Timer 2 (Pin 3) to ~31 kHz
    //TCCR2B = (TCCR2B & 0b11111000) | 0x01;

    pinMode(PWM, OUTPUT);
    analogWrite(PWM, 100);
    // digitalWrite(3, LOW);

}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();
        currentLight = 0;

        switch (command) {

            //  RESET (lights off, PWM back to default)
            case 'R': {
                for (int j = 0; j < numLights; j++) {
                    digitalWrite(EN[j], LOW);
                }
                analogWrite(PWM, 100);
            }
            break;

            //  PWM BRIGHTNESS
            case 'P': {
                // Wait for the value byte to actually arrive before
                // reading it. Without this, Serial.read() can return
                // -1 and analogWrite gets garbage.
                int value = readBlocking();
                analogWrite(PWM, value);
            }
            break;

            //  FOUR-CAPTURE MODE
            case 'F': {
                for (int i = 0; i < numLights; i++) {
                    // Turn on the correct light
                    turnOnLight(i);

                    // Allow LED to reach full brightness
                    delay(1500);

                    // Tell Python "ready to capture", then echo which
                    // light is lit so the host can verify phase.
                    Serial.write('A');
                    Serial.write(LIGHT_LETTER[i]);

                    // Wait for Python to send 'B'
                    while (true) {
                        if (Serial.available() > 0) {
                            char incoming = Serial.read();
                            if (incoming == 'B') {
                                break;
                            }
                        }
                    }

                    // Turn off the light
                    turnOffLight(i);

                }

                // Tell Python the whole sequence is done
                Serial.write('D');

                imagingComplete = true;
            }
            break;

            //  SINGLE-CAPTURE MODE
            case 'U': {

                // Wait for Python to send E/W/N/S
                char dir = 0;
                while (true) {
                    if (Serial.available() > 0) {
                        char incoming = Serial.read();
                        if (incoming == 'E' || incoming == 'W' ||
                            incoming == 'N' || incoming == 'S') {
                            dir = incoming;
                            break;
                        }
                    }
                }

                // Map direction to light index
                int idx = -1;
                if (dir == 'E') idx = 0;
                else if (dir == 'W') idx = 1;
                else if (dir == 'N') idx = 2;
                else if (dir == 'S') idx = 3;

                // Turn on selected light
                turnOnLight(idx);

                // Allow LED to reach full brightness
                delay(100);

                // Tell Python "ready", then echo the lit light so the
                // host can verify phase (framed handshake).
                Serial.write('A');
                Serial.write(dir);

                // Wait for Python to send 'B'
                while (true) {
                    if (Serial.available() > 0) {
                        char incoming = Serial.read();
                        if (incoming == 'B') {
                            break;
                        }
                    }
                }

                // Turn off light
                turnOffLight(idx);

                // Tell Python "done"
                Serial.write('D');
            }
            break;
        }
    }
}
