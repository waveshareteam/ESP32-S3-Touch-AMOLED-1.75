#include <Arduino.h>
#include <Wire.h>

#include "TouchDrvCSTXXX.hpp"
#include "pin_config.h"

namespace {

constexpr uint8_t kTouchAddress = CST92XX_SLAVE_ADDRESS;
constexpr uint8_t kMaxTouchPoints = 2;

TouchDrvCST92xx touch;
int16_t touchX[kMaxTouchPoints] = {};
int16_t touchY[kMaxTouchPoints] = {};
volatile bool touchPending = false;

void IRAM_ATTR onTouchInterrupt()
{
    touchPending = true;
}

bool takeTouchInterrupt()
{
    noInterrupts();
    const bool pending = touchPending;
    touchPending = false;
    interrupts();
    return pending;
}

}  // namespace

void setup()
{
    Serial.begin(115200);
    delay(1000);

    touch.setPins(TP_RESET, TP_INT);
    if (!touch.begin(Wire, kTouchAddress, IIC_SDA, IIC_SCL)) {
        Serial.println("CST9217 initialization failed.");
        while (true) {
            delay(1000);
        }
    }

    const uint8_t supportedPoints = touch.getSupportTouchPoint();
    Serial.printf("Touch controller: %s\n", touch.getModelName());
    Serial.printf(
        "Supported touch points: %u\n", static_cast<unsigned>(supportedPoints));
    Serial.println("Reporting raw controller coordinates.");

    pinMode(TP_INT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(TP_INT), onTouchInterrupt, FALLING);
}

void loop()
{
    if (!takeTouchInterrupt()) {
        delay(1);
        return;
    }

    const uint8_t supportedPoints = touch.getSupportTouchPoint();
    const uint8_t pointLimit =
        supportedPoints < kMaxTouchPoints ? supportedPoints : kMaxTouchPoints;
    const uint8_t touchedPoints = touch.getPoint(touchX, touchY, pointLimit);

    if (touchedPoints == 0) {
        return;
    }

    Serial.printf("Touch points: %u\n", static_cast<unsigned>(touchedPoints));
    for (uint8_t index = 0; index < touchedPoints; ++index) {
        Serial.printf(
            "  Point %u: raw_x=%d raw_y=%d\n",
            static_cast<unsigned>(index + 1),
            touchX[index],
            touchY[index]);
    }
}
