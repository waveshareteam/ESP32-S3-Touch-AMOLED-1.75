# CST9217 Touch Diagnostic

This Arduino example reports raw CST9217 touch coordinates over the serial monitor without starting
the AMOLED display or LVGL. It isolates the touch controller, I2C bus, reset pin, and interrupt line
from the rest of the graphics stack.

## Hardware

- ESP32-S3-Touch-AMOLED-1.75
- Onboard CST9217 touch controller
- USB serial connection at 115200 baud

The CST9217 driver used by this board supports up to two simultaneous touch points.

## Build

Use Arduino-ESP32 `3.3.10`, 16 MB flash, the `app3M_fat9M_16MB` partition scheme, and the bundled
libraries:

```bash
arduino-cli compile \
  --fqbn "esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB" \
  --libraries examples/arduino/libraries \
  examples/arduino/10_Touch_CST9217
```

## Expected Output

After initialization, touching the panel prints the active point count and raw coordinates:

```text
Touch controller: CST9217
Supported touch points: 2
Reporting raw controller coordinates.
Touch points: 2
  Point 1: raw_x=120 raw_y=210
  Point 2: raw_x=338 raw_y=275
```

These are raw controller coordinates. LVGL examples apply the board's `466 x 466` bounds and XY
mirroring before using touch input, so their displayed coordinates can differ.

## Hardware Validation

Before release, verify:

- Repeated single-finger taps across all panel edges.
- Two-finger detection and coordinate stability.
- Long presses and rapid successive touches.
- Stable interrupt handling over an extended run.
