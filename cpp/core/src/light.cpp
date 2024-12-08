#include "light.h"
#include <Arduino.h>

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
