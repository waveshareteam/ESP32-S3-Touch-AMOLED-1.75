# Immersive Block

This ESP-IDF example renders a motion-controlled falling-block scene on the
ESP32-S3-Touch-AMOLED-1.75.

## Hardware

- ESP32-S3-Touch-AMOLED-1.75
- QSPI AMOLED display
- Capacitive touch
- QMI8658 IMU

Tilting the board controls the scene. The example initializes the board display and I2C bus, reads the
QMI8658, and updates the LVGL interface from a dedicated application task.

## Supported Versions

- ESP-IDF `v5.5.4`
- ESP-IDF `v6.0.2`
- Target `esp32s3`

## Build And Flash

From the repository root with ESP-IDF activated:

```bash
idf.py -C examples/esp-idf/04_Immersive_block \
  -B build/04_Immersive_block \
  set-target esp32s3 build

idf.py -C examples/esp-idf/04_Immersive_block \
  -B build/04_Immersive_block \
  -p PORT flash monitor
```

## Runtime Notes

Display updates use bounded lock waits and a fixed frame delay. Long rendering operations yield to
system tasks, and the amount of work performed per frame is capped. Keep these scheduling safeguards
when changing animation density or adding effects; unbounded rendering can trigger the task watchdog.

For a prebuilt image, use the matching `04_Immersive_block` package from the GitHub Release and flash
its combined binary at `0x0`.
