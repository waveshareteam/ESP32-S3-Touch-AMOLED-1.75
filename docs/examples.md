# Example Catalog

[简体中文](examples_ZH.md) | **English**

CI discovers only the direct first-party examples listed below. Examples bundled inside third-party
libraries are dependencies or upstream samples and are not product firmware targets.

The 14 first-party demos included in v1.0.1 were hardware-tested for that release. The current source
adds `10_Touch_CST9217`, which must be hardware-validated before the next release. The current CI
matrix builds the five ESP-IDF projects with two IDF versions for 10 packages, plus 10 Arduino
packages.

## ESP-IDF Examples

| Example | Purpose | Hardware / notes |
| --- | --- | --- |
| `01_AXP2101` | Initializes the AXP2101, configures rails and charging, and reports power events. | Power management and serial monitor. |
| `02_lvgl_demo_v9` | Starts the board display and runs the LVGL benchmark demo. | 466 × 466 AMOLED display and touch. |
| `03_esp-brookesia` | Runs an ESP-Brookesia phone-style UI and SquareLine demo application. | AMOLED display, touch, and PSRAM; ESP-IDF v6 uses the CI config overlay. |
| `04_Immersive_block` | Renders a motion-controlled falling-block scene. | AMOLED display, touch, and QMI8658 IMU. |
| `05_Spec_Analyzer` | Captures microphone audio, computes an FFT, and displays spectrum bars. | AMOLED display and two onboard microphones through ES7210. |

Build each project from its own directory with target `esp32s3`. See
[Getting Started](getting-started.md#build-with-esp-idf).

## Arduino Examples

| Example | Purpose | Hardware / notes |
| --- | --- | --- |
| `01_HelloWorld` | Basic display initialization and text output. | AMOLED display. |
| `02_GFX_AsciiTable` | Draws an ASCII character table with Arduino GFX. | AMOLED display. |
| `03_LVGL_PCF85063_simpleTime` | Shows RTC date and time through an LVGL interface. | PCF85063 RTC, display, and touch. |
| `04_LVGL_QMI8658_ui` | Displays live accelerometer and gyroscope data. | QMI8658 IMU, display, and touch. |
| `05_LVGL_AXP2101_ADC_Data` | Displays battery, VBUS, temperature, and charge information. | AXP2101, display, and touch. |
| `06_LVGL_Widgets` | Runs the LVGL music demo with board input and sensor initialization. | Display, touch, and QMI8658. |
| `07_LVGL_SD_Test` | Exercises microSD access through an LVGL-based board application. | FAT/FAT32 microSD card. |
| `08_ES8311` | Initializes ES8311 audio and runs an LVGL widgets interface. | ES8311 playback path, external speaker, display, and touch. |
| `09_LC76G_I2C` | Communicates with LC76G GNSS over I2C. | The `-G` variant has the onboard module; other variants require compatible LC76G hardware and a suitable antenna. |
| `10_Touch_CST9217` | Reports raw interrupt-driven single- and two-point touch coordinates over serial. | CST9217 touch controller; display and LVGL are intentionally not initialized. |

Compile with Arduino-ESP32 `3.3.10`, 16 MB flash, the
`app3M_fat9M_16MB` partition scheme, and the bundled libraries. See
[Getting Started](getting-started.md#build-with-arduino).

## Factory Brookesia Application Suite

The maintained customer firmware under `firmware/brookesia` is a separate product application, not a
single-example CI target. Its launcher contains:

| Application | Main capability | Hardware / data path |
| --- | --- | --- |
| SquareLine | Demonstrates the reusable SquareLine/LVGL interface. | AMOLED display and touch. |
| Calculator | Provides a touch calculator. | AMOLED display and touch. |
| DrawPanel | Provides a white drawing canvas and touch drawing tools. | AMOLED display and touch. |
| SpecAnalyzer | Displays a live audio spectrum. | Two onboard microphones through ES7210. |
| MusicPlayer | Plays MP3/WAV files and exposes previous, play/pause, and next controls. | ES8311 speaker path and `/sdcard/music`, with a SPIFFS fallback. |
| Gallery | Displays baseline JPG/JPEG files with navigation and slideshow controls. | `/sdcard/photos`; asynchronous image decoding. |
| VideoPlayer | Plays deliberately low-rate MJPEG/PCM AVI files. | `/sdcard/video`; display and shared audio service. |
| Recorder | Records 24 kHz, 16-bit stereo WAV files. | Two ES7210 microphone channels and `/sdcard/Waveshare/Recordings`. |
| Settings | Controls Wi-Fi, brightness, volume, and storage, and reports battery/charging, RSSI, and SD status. | Native Wi-Fi, AXP2101, display, audio, and microSD. |
| AIChats | Provides WakeNet/VAD/Opus voice interaction and Xiaozhi transport support. | Wi-Fi plus shared microphone and speaker services; remote activation/service availability is required. |
| Gravitysphere | Moves a ball inside the circular display boundary. | QMI8658 accelerometer. |
| Crosshair | Shows circular alignment targets and touch-selectable palettes. | AMOLED display and touch. |

Factory-firmware flashing, media layout, and hardware acceptance are documented in the bilingual
[Firmware Delivery Guide](../firmware/README.md) and [SD-card Media Guide](../firmware/MEDIA_GUIDE.md).

## CI Selection

The Build Examples workflow can run all examples, one example name, or a repository-relative path.
Workflow-dispatch selectors include:

- `all`
- `04_Immersive_block`
- `examples/esp-idf/05_Spec_Analyzer`
- `09_LC76G_I2C`
- `10_Touch_CST9217`

Every successful source build produces a `*-combined.zip` firmware artifact. An artifact built for a
single example is not interchangeable with the complete Brookesia factory image.
