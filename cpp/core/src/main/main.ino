int PWM = 3;
int EN1 = 8;
int EN2 = 7;
int EN3 = 6;
int EN4 = 5;
int EN[] = {EN1, EN2, EN3, EN4};
const int numLights = 4; // Number of lights
int currentLight = 0; // Start with the first light
bool imagingComplete = false;

void turnOnLight(int lightIndex) {
    Serial.print("Turning on light ");
    Serial.println(lightIndex);
    digitalWrite(EN[lightIndex], HIGH);
    Serial.print("Light ");
    Serial.print(lightIndex);
    Serial.println(" is on. Notifying PC capture software...");
}

void turnOffLight(int lightIndex) {
    Serial.print("Turning off light ");
    Serial.println(lightIndex);
    digitalWrite(EN[lightIndex], LOW);
}

void setup() {
    Serial.begin(9600); // Start serial communication
    for (int i = 0; i < numLights; i++) {
        pinMode(EN[i], OUTPUT); // Set each light pin to output
    }
     for (int j = 0; j < numLights; j++) {
        digitalWrite(EN[j], LOW); // Set PWM to 0% DC
    }
    analogWrite(PWM, 150);
    Serial.println("System Powered On. Awaiting connection...");
}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();
// user cmds C, Z, A, B, E
// youll get Z from the script
// turn on the light , A tells the script that the light is on and its time to take the picture
// B pictures finished lights off
        switch (command) {
            case 'C': // Connection established
                Serial.println("Connection acknowledged.");
                Serial.println("Awaiting prompt to begin imaging...");
                break;

            case 'Z': // Image taken
                if (currentLight < numLights)
                {
                    turnOnLight(currentLight);
                    Serial.write("A");
                    // Need to rewrite this line, right now if statement waits 250 ms. If capture takes longer than 250 ms it will proceed without capturing
                    int temp = 0;

                    while (temp == 0) {
                      char x = Serial.read();
                      if (x == 'B') {
                        turnOffLight(currentLight);
                        delay(250);
                        temp++; 
                      } 
                    }

                    currentLight++;

                } else {
                    Serial.println("Imaging complete for all lights.");
                    currentLight = 0;
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