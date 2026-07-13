# Waveshare ESP32-S3-Touch-AMOLED-1.75

[![Build Examples](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml/badge.svg)](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml)
[![Latest Release](https://img.shields.io/github/v/release/waveshareteam/ESP32-S3-Touch-AMOLED-1.75)](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest)

Example software, documentation, schematics, and recovery firmware for the Waveshare
ESP32-S3-Touch-AMOLED-1.75 development board.

## Hardware Overview

| Feature | Device / interface |
| --- | --- |
| MCU | ESP32-S3, firmware configured for 16 MB flash |
| Display | 1.75-inch 466 x 466 QSPI AMOLED with capacitive touch |
| Power management | AXP2101 |
| Motion sensor | QMI8658 six-axis IMU |
| Real-time clock | PCF85063 |
| Audio | Dual digital microphones and ES8311 codec support |
| Storage | microSD card interface |
| Expansion example | LC76G GNSS module over I2C |

See the [product wiki](https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75) and the files under
[Schematic](Schematic/) for board setup, pin definitions, and hardware details.

## Quick Start

The simplest path is to use a tested firmware package from the
[latest release](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest).

1. Download the `*-combined.zip` asset for the example and framework version you need.
2. Extract the archive and install esptool with `python -m pip install esptool`.
3. Connect the board over USB.
4. Run `flash_combined.bat COMx` on Windows or `./flash_combined.sh /dev/ttyACM0` on Linux.
5. Reset the board after flashing if it does not restart automatically.

The combined image is flashed at offset `0x0`. Split binaries and their original offsets remain in
the same package for advanced use. See [Getting Started](docs/getting-started.md) for source builds,
Arduino IDE settings, boot mode, and troubleshooting.

## Examples

The repository contains 15 first-party examples:

- Five ESP-IDF projects under [examples/esp-idf](examples/esp-idf/).
- Ten Arduino sketches under [examples/arduino](examples/arduino/).
- Bundled Arduino dependencies under `examples/arduino/libraries/`.

The examples cover power management, LVGL, ESP-Brookesia, the QMI8658 IMU, RTC, microSD, ES8311
audio, microphone spectrum analysis, LC76G GNSS, and raw CST9217 touch diagnostics. See the
[example catalog](docs/examples.md) for behavior and hardware requirements.

## Supported Toolchains

The current CI matrix uses:

| Surface | Version | Coverage |
| --- | --- | --- |
| ESP-IDF | `v5.5.4` | All five ESP-IDF projects |
| ESP-IDF | `v6.0.2` | All five ESP-IDF projects |
| Arduino-ESP32 | `3.3.10` | All ten first-party sketches |

GitHub Actions build all 20 framework/example combinations and package each successful build as
flashable firmware. Bundled library examples and factory recovery binaries are intentionally excluded.

The v1.0.1 release predates `10_Touch_CST9217` and contains the original 19 firmware packages.

## Repository Layout

- `examples/esp-idf/`: first-party ESP-IDF projects.
- `examples/arduino/`: first-party Arduino sketches and bundled libraries.
- `firmware/`: released factory recovery image, not generated from CI.
- `releases/`: packaging, artifact download, and release staging tools.
- `docs/`: setup, examples, CI, component, firmware, and troubleshooting guides.
- `Schematic/`: hardware schematic material.
- `.github/`: CI and contribution templates.

See [Repository Structure](docs/repository-structure.md) for discovery boundaries and maintenance
rules.

## Documentation

- [Getting Started](docs/getting-started.md)
- [Example Catalog](docs/examples.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Firmware and Factory Recovery](docs/firmware.md)
- [Continuous Integration](docs/ci.md)
- [Components](docs/components.md)
- [Release Tools](releases/README.md)
- [Changelog](CHANGELOG.md)

## Support And Contributions

Use GitHub issues for reproducible software problems. Include the example path, framework version,
steps to reproduce, expected behavior, actual behavior, and relevant serial logs.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md), and [SECURITY.md](SECURITY.md)
before reporting or submitting changes.

## License

This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
