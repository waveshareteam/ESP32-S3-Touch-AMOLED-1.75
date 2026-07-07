# Components

This repository prefers managed components for reusable BSP, display, touch, sensor, and helper code. Local components should be limited to example-specific glue or temporary compatibility code.

## Registry Snapshot

Component registry metadata checked on 2026-07-07:

| Component | Latest Version | Target / IDF Notes |
| --- | --- | --- |
| `waveshare/esp32_s3_touch_amoled_1_75` | `3.0.1` | `esp32s3`, IDF `>=5.5` |
| `waveshare/qmi8658` | `2.0.0` | IDF `>=5.3.2` |
| `waveshare/esp_lcd_touch_cst9217` | `2.0.0` | IDF `>=4.4.2` |

The current ESP-IDF examples already use managed Waveshare components where practical. Local copies remain where the example has project-specific integration or a broader synchronization task is required.

## Local Components To Review Later

- `examples/esp-idf/01_AXP2101/components/XPowersLib`: local power-management library used by the AXP2101 example.
- `examples/esp-idf/03_esp-brookesia/components/brookesia_core`: local Brookesia source snapshot.
- `examples/esp-idf/03_esp-brookesia/components/brookesia_app_squareline_demo`: local demo app assets and generated UI code.
- `examples/esp-idf/03_esp-brookesia/components/esp32_s3_touch_amoled_1_75`: board component copy tied to the local Brookesia example.
- `examples/esp-idf/05_Spec_Analyzer/components/bsp_extra`: project-specific codec and I2S capture glue used by the spectrum analyzer.

## TODO

- Keep Brookesia AI framework JSON support conditional: IDF v5.5 uses the built-in `json` component, while IDF v6 uses managed `espressif/cjson` when the AI framework is enabled.
- When a shared Waveshare component fix is required, prefer fixing and releasing the shared component first, then updating the product repository dependency range.
- Keep `bsp_extra` local only for example-specific glue that does not belong in the shared component repository.
