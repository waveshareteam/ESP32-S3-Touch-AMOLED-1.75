# 组件说明

[English](components.md)

本仓库优先使用 managed components 管理可复用的 BSP、显示、触摸、传感器与辅助代码。本地组件
应仅用于示例专属粘合代码或临时兼容实现。

## 组件注册表快照

以下组件注册表元数据核对于 2026-07-07：

| 组件 | 最新版本 | 目标 / ESP-IDF 说明 |
| --- | --- | --- |
| `waveshare/esp32_s3_touch_amoled_1_75` | `3.0.1` | `esp32s3`，ESP-IDF `>=5.5` |
| `waveshare/qmi8658` | `2.0.0` | ESP-IDF `>=5.3.2` |
| `waveshare/esp_lcd_touch_cst9217` | `2.0.0` | ESP-IDF `>=4.4.2` |

当前 ESP-IDF 示例已在适合的位置使用 Waveshare managed components。若示例需要项目专属集成，
或仍需进行更广范围的同步，则保留本地副本。

## 后续需要评估的本地组件

- `examples/esp-idf/01_AXP2101/components/XPowersLib`：AXP2101 示例使用的本地电源管理库。
- `examples/esp-idf/03_esp-brookesia/components/brookesia_core`：本地 Brookesia 源码快照。
- `examples/esp-idf/03_esp-brookesia/components/brookesia_app_squareline_demo`：本地演示应用资源与生成的 UI 代码。
- `examples/esp-idf/03_esp-brookesia/components/esp32_s3_touch_amoled_1_75`：与本地 Brookesia 示例绑定的板级组件副本。
- `examples/esp-idf/05_Spec_Analyzer/components/bsp_extra`：频谱分析器使用的编解码器与 I2S 采集粘合代码。

## 待办事项

- 保持 Brookesia AI framework 的 JSON 支持为条件配置：ESP-IDF v5.5 使用内置 `json` 组件；
  ESP-IDF v6 在启用 AI framework 时使用 managed component `espressif/cjson`。
- 默认 manifest 不包含 Brookesia AI framework 的 managed dependencies，因为
  `CONFIG_ESP_BROOKESIA_ENABLE_AI_FRAMEWORK` 默认关闭；启用 AI CI 前必须补入并验证
  GMF、Coze、ESP-SR 依赖链。
- 如果共享 Waveshare 组件需要修复，应优先修复并发布共享组件，再更新产品仓库的依赖范围。
- `bsp_extra` 仅用于不适合进入共享组件仓库的示例专属粘合代码。
