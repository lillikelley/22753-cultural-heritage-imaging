#include "main.h"
#include "light.h"

void setup() 
{
    Serial.begin(9600); // Start serial communication
    for (int i = 0; i < 4; i++) 
	{ // Assuming 4 lights for this example
        pinMode(i, OUTPUT); // Set each light pin to output
    }
}

void loop() 
{
    // Example usage
    turnOnLight(0);
    delay(1000); // Keep the light on for a second
    turnOffLight(0);
    delay(1000); // Keep the light off for a second
}
