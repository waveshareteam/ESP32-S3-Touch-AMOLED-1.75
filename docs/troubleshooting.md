# Troubleshooting

## Board Does Not Enter Download Mode

Confirm that the USB cable carries data and that no other serial monitor owns the port. If automatic
reset fails, hold BOOT, tap RESET, start the flash command, and release BOOT when writing begins.

Lower the baud rate in the generated flash command if the USB connection is unstable.

## Flash Size Header Error

A message similar to the following means the image header and detected flash size do not agree:

```text
Detected size(16384k) smaller than the size in the binary image header(32768k)
```

Use the v1.0.1 or newer package built for this board's 16 MB flash layout. Do not combine a bootloader,
partition table, and application from different artifacts. Erase the old image before retrying if a
previous 32 MB image or partition table remains:

```bash
python -m esptool --chip esp32s3 --port PORT erase_flash
```

Then flash the complete `*-combined.bin` at `0x0` with the packaged script.

## Watchdog Reset In Display Demos

Use the v1.0.1 or newer `04_Immersive_block` package. The demo now bounds display-lock waits, limits
per-frame rendering work, delays between frames, and yields during long operations. These changes
avoid starving system tasks under both supported ESP-IDF versions.

If resets continue, capture the complete boot log and backtrace. Confirm that the firmware package,
board model, and framework version match, then report the example path and release asset filename.

## Blank Or Unresponsive Display

- Confirm the firmware targets ESP32-S3-Touch-AMOLED-1.75.
- Reset the board after flashing.
- Flash the entire combined image instead of only the application binary.
- Do not mix binaries from different examples or framework versions.
- Use a stable USB power source.

For source builds, preserve the project's `sdkconfig.defaults` and partition table.

## ESP-Brookesia Build Or Startup Issues

Use the supported ESP-IDF versions and keep `sdkconfig.defaults.v6` enabled for ESP-IDF v6. The
repository carries a synchronized local Brookesia snapshot and compatibility configuration; replacing
individual components without updating the dependency set can break the build or runtime.

## Arduino Library Conflicts

Use the bundled libraries under `examples/arduino/libraries`. Remove duplicate global copies or make
sure the bundled path takes precedence. Confirm Arduino-ESP32 `3.3.10`, 16 MB flash, and the
`app3M_fat9M_16MB` partition scheme.

## Peripheral Examples

- Format the microSD card with a supported FAT filesystem for `07_LVGL_SD_Test`.
- Check the audio path and connections for `08_ES8311`.
- Verify LC76G power, I2C wiring, address, and antenna for `09_LC76G_I2C`.
- Keep the board still during initial IMU checks if motion values appear unstable.

For unresolved problems, follow [SUPPORT.md](../SUPPORT.md) and include full serial logs.
