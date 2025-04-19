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
    digitalWrite(EN[lightIndex], HIGH);
}

void turnOffLight(int lightIndex) {
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
    analogWrite(PWM, 200);
}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();
        currentLight = 0;

        switch (command) {
            case 'C': // Connection established
                for (int j = 0; j < numLights; j++) {
                  digitalWrite(EN[j], LOW); // Set PWM to 0% DC
                }
                analogWrite(PWM, 200);
                break;

            case 'F': // Four-capture mode
              while (currentLight < numLights) {
                turnOnLight(currentLight);
                Serial.write('A');

                int temp = 0;
                while (temp == 0) {
                  char x = Serial.read();
                  if (x == 'B') {
                    turnOffLight(currentLight);
                    temp++; 
                  } 
                }

                currentLight++;

              }
              
              Serial.write('D');
              imagingComplete = true;
            
            break;

            case 'U': // Single capture mode
              int temp0 = 0;
              while (temp0 == 0) {
                char y = Serial.read();
                
                if (y == 'N') {
                  turnOnLight(0);
                  Serial.write('A');
                  int temp1 = 0;
                  while (temp1 == 0) {
                    char z1 = Serial.read();
                    if (z1 == 'B'){
                      turnOffLight(0);
                      Serial.write('D');
                      temp1++;
                    }                    
                  }
                  temp0++;
                } else if (y == 'E') {
                  turnOnLight(1);
                  Serial.write('A');
                  int temp2 = 0;
                  while (temp2 == 0) {
                    char z2 = Serial.read();
                    if (z2 == 'B'){
                      turnOffLight(1);
                      Serial.write('D');
                      temp2++;
                    }
                  }
                  temp0++;
                } else if (y == 'S') {
                  turnOnLight(2);
                    Serial.write('A');

                    int temp3 = 0;
                    while (temp3 == 0) {
                      char z3 = Serial.read();
                      if (z3 == 'B'){
                        turnOffLight(2);
                        Serial.write('D');
                        temp3++;
                      }
                    }
                  temp0++;
                } else if (y == 'W') {
                  turnOnLight(3);
                    Serial.write('A');

                    int temp4 = 0;
                    while (temp4 == 0) {
                      char z4 = Serial.read();
                      if (z4 == 'B'){
                        turnOffLight(3);
                        Serial.write('D');
                        temp4++;
                      }
                    }
                  temp0++;
                } 
              }
            
            break;
        }
    }
}