# Waveshare ESP32-S3-Touch-AMOLED-1.75

Example software and support files for the Waveshare ESP32-S3-Touch-AMOLED-1.75 development board. The board combines an ESP32-S3 module, a 1.75 inch 466x466 QSPI AMOLED touch display, dual digital microphones, power management, sensors, and audio support.

## Repository Layout

- `examples/esp-idf/` contains first-party ESP-IDF projects for this board.
- `examples/arduino/` contains first-party Arduino sketches for this board.
- `examples/arduino/libraries/` contains bundled Arduino libraries used by the sketches.
- `Firmware/` contains released factory flashing and recovery binaries. These are not source build outputs.
- `Schematic/` contains hardware schematic material.
- `docs/` contains repository structure, CI, component, and firmware notes.
- `.github/` contains GitHub Actions workflows and public collaboration templates.

The previous versioned example roots are kept as compatibility notes only:

- `examples/ESP-IDF-v5.5/`
- `examples/Arduino-v3.3.5/`

## ESP-IDF Examples

ESP-IDF projects are under `examples/esp-idf/`:

- `01_AXP2101`
- `02_lvgl_demo_v9`
- `03_esp-brookesia`
- `04_Immersive_block`
- `05_Spec_Analyzer`

Each project is intended to be opened from its own directory with ESP-IDF. CI builds these projects for the selected ESP32-S3 target matrix.

## Arduino Examples

Arduino sketches are under `examples/arduino/`:

- `01_Hello_world`
- `02_GFX_AsciiTable`
- `03_LVGL_PCF85063_simpleTime`
- `04_LVGL_QMI8658_ui`
- `05_LVGL_AXP2101_ADC_Data`
- `06_LVGL_Widgets`
- `07_LVGL_SD_Test`
- `08_ES8311`
- `ESP32-S3-LC76G-I2C`

Use the bundled libraries in `examples/arduino/libraries/` when compiling these sketches.

## CI Validation

GitHub Actions validate first-party examples only. Bundled library examples are intentionally excluded from product CI.

Current CI pins were resolved from upstream release metadata on 2026-07-07:

- ESP-IDF `v5.5.4`
- ESP-IDF `v6.0.2`
- Arduino-ESP32 `3.3.10`

Use workflow dispatch to build all examples, a single directory name, or a repo-relative path. See `docs/ci.md` for details.

## Documentation

- `docs/repository-structure.md` explains the normalized layout and compatibility directories.
- `docs/ci.md` explains CI discovery, matrix selection, and version policy.
- `docs/components.md` records managed component status and local component boundaries.
- `docs/firmware.md` explains the factory binary and source build boundary.

## Support And Contributions

Use GitHub issues for reproducible software problems and include the affected example path, framework version, steps to reproduce, expected behavior, and actual behavior. For product support and order-specific help, contact Waveshare support.

See `CONTRIBUTING.md`, `SUPPORT.md`, and `SECURITY.md` for project contribution, support, and vulnerability reporting guidance.

## License

This repository is licensed under the Apache License 2.0. See `LICENSE` for details.
