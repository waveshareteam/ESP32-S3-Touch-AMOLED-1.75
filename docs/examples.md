# Example Catalog

CI discovers only the direct first-party examples listed below. Examples bundled inside third-party
libraries are dependencies or upstream samples and are not product firmware targets.

The 14 first-party demos included in v1.0.1 were hardware-tested for that release. The current source
adds `10_Touch_CST9217`, which must be hardware-validated before the next release. ESP-IDF projects
produce 10 firmware packages and Arduino produces 10 packages.

## ESP-IDF

| Example | Purpose | Hardware / notes |
| --- | --- | --- |
| `01_AXP2101` | Initializes the AXP2101, configures rails and charging, and reports power events. | Power management and serial monitor. |
| `02_lvgl_demo_v9` | Starts the board display and runs the LVGL benchmark demo. | AMOLED display and touch. |
| `03_esp-brookesia` | Runs an ESP-Brookesia phone-style UI and SquareLine demo application. | AMOLED display, touch, and PSRAM; v6 uses the CI config overlay. |
| `04_Immersive_block` | Renders a motion-controlled falling-block scene. | AMOLED display, touch, and QMI8658 IMU. |
| `05_Spec_Analyzer` | Captures microphone audio, computes an FFT, and displays spectrum bars. | AMOLED display and onboard digital microphones. |

Build each project from its own directory with target `esp32s3`. See
[Getting Started](getting-started.md#build-with-esp-idf).

## Arduino

| Example | Purpose | Hardware / notes |
| --- | --- | --- |
| `01_HelloWorld` | Basic display initialization and text output. | AMOLED display. |
| `02_GFX_AsciiTable` | Draws an ASCII character table with Arduino GFX. | AMOLED display. |
| `03_LVGL_PCF85063_simpleTime` | Shows RTC date and time through an LVGL interface. | PCF85063 RTC, display, and touch. |
| `04_LVGL_QMI8658_ui` | Displays live accelerometer and gyroscope data. | QMI8658 IMU, display, and touch. |
| `05_LVGL_AXP2101_ADC_Data` | Displays battery, VBUS, temperature, and charge information. | AXP2101, display, and touch. |
| `06_LVGL_Widgets` | Runs the LVGL music demo with board input and sensor initialization. | Display, touch, and QMI8658. |
| `07_LVGL_SD_Test` | Exercises microSD access through an LVGL-based board application. | Compatible microSD card. |
| `08_ES8311` | Initializes ES8311 audio and runs an LVGL widgets interface. | ES8311 audio path, display, and touch. |
| `09_LC76G_I2C` | Communicates with an external LC76G GNSS module over I2C. | External LC76G module and suitable antenna. |
| `10_Touch_CST9217` | Reports raw interrupt-driven single- and two-point touch coordinates over serial. | CST9217 touch controller; display and LVGL are intentionally not initialized. |

Compile with Arduino-ESP32 `3.3.10`, 16 MB flash, the
`app3M_fat9M_16MB` partition scheme, and the bundled libraries. See
[Getting Started](getting-started.md#build-with-arduino).

## CI Selection

The Build Examples workflow can run all examples, one example name, or a repository-relative path.
For example, workflow dispatch selectors include:

- `all`
- `04_Immersive_block`
- `examples/esp-idf/05_Spec_Analyzer`
- `09_LC76G_I2C`
- `10_Touch_CST9217`

Every successful source build produces a `*-combined.zip` firmware artifact.
