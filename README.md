<div align="center">
  <h1>ESP32-S3-Touch-AMOLED-1.75</h1>
  <p><strong>ESP32-S3 1.75-inch 466 x 466 QSPI AMOLED touch development board</strong></p>
  <p>
    <a href="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml"><img alt="Build Examples" src="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml/badge.svg"></a>
    <a href="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest"><img alt="Latest Release" src="https://img.shields.io/github/v/release/waveshareteam/ESP32-S3-Touch-AMOLED-1.75"></a>
    <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/waveshareteam/ESP32-S3-Touch-AMOLED-1.75"></a>
  </p>
  <p>
    <a href="https://www.waveshare.com/esp32-s3-touch-amoled-1.75.htm">🌐 Product Page</a> ·
    <a href="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest">📦 Firmware Releases</a> ·
    <a href="examples/esp-idf/">🧩 ESP-IDF Examples</a> ·
    <a href="examples/arduino/">🔧 Arduino Examples</a> ·
    <a href="docs/">📚 Documentation</a>
  </p>
</div>

---

## ✨ Overview

This repository provides example software, source-built firmware packages,
factory recovery firmware, schematics, and documentation for the Waveshare
ESP32-S3-Touch-AMOLED-1.75.

The board combines an ESP32-S3 with a high-resolution AMOLED display,
capacitive touch, motion sensing, power management, real-time clock, audio,
and storage interfaces in a compact development platform.

## 🖥️ Hardware Overview

| Feature | Device / interface |
| --- | --- |
| MCU | ESP32-S3 with 16 MB flash |
| Display | 1.75-inch 466 x 466 QSPI AMOLED |
| Touch | CST9217 capacitive touch controller with two-point support |
| Power management | AXP2101 |
| Motion sensor | QMI8658 six-axis IMU |
| Real-time clock | PCF85063 |
| Audio | Dual onboard digital microphones and ES8311 codec support |
| Storage | microSD card interface |
| Expansion example | External LC76G GNSS module over I2C |
| Board support | Managed component: `waveshare/esp32_s3_touch_amoled_1_75` |
| Hardware files | [Product wiki](https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75) and [schematics](Schematic/) |

## 📦 Firmware Releases

The fastest way to try an example is to use a ready-to-flash package from the
[latest release](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest).

1. Download the `*-combined.zip` package for the example and framework version
   you need.
2. Extract the archive and install esptool with
   `python -m pip install esptool`.
3. Connect the board over USB.
4. Run `flash_combined.bat COMx` on Windows or
   `./flash_combined.sh /dev/ttyACM0` on Linux.
5. Reset the board if it does not restart automatically.

> [!NOTE]
> Combined images are flashed at offset `0x0`. Each package also contains the
> original split binaries, flash arguments, helper scripts, and checksums.

The [firmware](firmware/) directory contains the source-maintained Brookesia
port and a separate factory recovery image; neither is a CI-generated example
package. See
[Firmware and Factory Recovery](docs/firmware.md) for details.

The Brookesia source firmware provides twelve applications, including live
dual-microphone spectrum analysis through ES7210, SD music/photo/video media,
stereo WAV recording, AIChats, AXP2101-backed power status, native Wi-Fi status,
circular QMI8658-driven Gravitysphere motion, and a full-screen Crosshair
panel-alignment target.

## 🧪 Examples

### ESP-IDF

| Example | Focus |
| --- | --- |
| [01_AXP2101](examples/esp-idf/01_AXP2101/) | Power management, charging, and battery telemetry |
| [02_lvgl_demo_v9](examples/esp-idf/02_lvgl_demo_v9/) | LVGL 9 display benchmark |
| [03_esp-brookesia](examples/esp-idf/03_esp-brookesia/) | ESP-Brookesia phone-style application UI |
| [04_Immersive_block](examples/esp-idf/04_Immersive_block/) | Motion-controlled falling-block demo |
| [05_Spec_Analyzer](examples/esp-idf/05_Spec_Analyzer/) | Microphone FFT spectrum analyzer |

### Arduino

| Example | Focus |
| --- | --- |
| [01_HelloWorld](examples/arduino/01_HelloWorld/) | Display bring-up and text output |
| [02_GFX_AsciiTable](examples/arduino/02_GFX_AsciiTable/) | GFX text and character rendering |
| [03_LVGL_PCF85063_simpleTime](examples/arduino/03_LVGL_PCF85063_simpleTime/) | LVGL real-time clock interface |
| [04_LVGL_QMI8658_ui](examples/arduino/04_LVGL_QMI8658_ui/) | LVGL accelerometer and gyroscope interface |
| [05_LVGL_AXP2101_ADC_Data](examples/arduino/05_LVGL_AXP2101_ADC_Data/) | LVGL power and battery telemetry |
| [06_LVGL_Widgets](examples/arduino/06_LVGL_Widgets/) | LVGL music UI, touch input, and IMU integration |
| [07_LVGL_SD_Test](examples/arduino/07_LVGL_SD_Test/) | microSD access through an LVGL application |
| [08_ES8311](examples/arduino/08_ES8311/) | ES8311 audio path and LVGL interface |
| [09_LC76G_I2C](examples/arduino/09_LC76G_I2C/) | External LC76G GNSS over I2C |
| [10_Touch_CST9217](examples/arduino/10_Touch_CST9217/) | Raw interrupt-driven single- and two-point touch diagnostics |

Bundled Arduino libraries live under
[`examples/arduino/libraries`](examples/arduino/libraries/). Their upstream
library examples are intentionally excluded from the product CI matrix.

## 🛠️ Supported Toolchains

| Surface | Version | Firmware builds |
| --- | --- | ---: |
| ESP-IDF | `v5.5.4` | 5 |
| ESP-IDF | `v6.0.2` | 5 |
| Arduino-ESP32 | `3.3.10` | 10 |

The [Build Examples workflow](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml)
runs two discovery jobs and 20 firmware build jobs. Each successful build is
packaged as a flashable firmware artifact. Bundled library examples and factory
recovery binaries are intentionally excluded. See
[Continuous Integration](docs/ci.md) for matrix and dispatch details.

The historical v1.0.1 release predates `10_Touch_CST9217` and contains 19
firmware packages.

## 🗂️ Repository Layout

| Path | Purpose |
| --- | --- |
| [`examples/esp-idf/`](examples/esp-idf/) | First-party ESP-IDF projects |
| [`examples/arduino/`](examples/arduino/) | First-party Arduino sketches and bundled libraries |
| [`firmware/`](firmware/) | Brookesia source firmware and factory recovery binary |
| [`releases/`](releases/) | Packaging, artifact download, and release tools |
| [`config/`](config/) | Shared ESP-IDF compatibility overlays |
| [`docs/`](docs/) | Setup, example, CI, component, firmware, and troubleshooting notes |
| [`Schematic/`](Schematic/) | Public schematic files |
| [`scripts/`](scripts/) | CI example discovery helpers |
| [`.github/`](.github/) | GitHub Actions and contribution templates |

## 📚 Documentation

- [Getting Started](docs/getting-started.md)
- [Example Catalog](docs/examples.md)
- [Repository Structure](docs/repository-structure.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Firmware and Factory Recovery](docs/firmware.md)
- [Continuous Integration](docs/ci.md)
- [Components](docs/components.md)
- [Release Tools](releases/README.md)
- [Changelog](CHANGELOG.md)

## 🤝 Support and Contributions

Contributions and reproducible issue reports are welcome. Include the example
path, framework version, reproduction steps, expected behavior, actual
behavior, and relevant serial logs.

- [Contributing Guide](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Security Policy](SECURITY.md)
- [Open an Issue](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/issues/new/choose)

## 📄 License

This repository is licensed under the Apache License 2.0. See
[LICENSE](LICENSE).
