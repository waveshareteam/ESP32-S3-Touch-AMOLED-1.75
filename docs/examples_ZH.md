# 示例目录

**简体中文** | [English](examples.md)

CI 只发现下面列出的一级目录自有示例。第三方库内部附带的示例属于依赖或上游样例，不是本产品的
固件构建目标。

v1.0.1 包含的 14 个自有演示已针对该版本完成硬件测试。当前源码新增 `10_Touch_CST9217`，该示例
需要在下个版本发布前完成硬件验证。当前 CI 矩阵使用两个 IDF 版本构建 5 个 ESP-IDF 工程，共生成
10 个包，另外生成 10 个 Arduino 包。

## ESP-IDF 示例

| 示例 | 用途 | 硬件 / 说明 |
| --- | --- | --- |
| `01_AXP2101` | 初始化 AXP2101、配置电源轨和充电参数，并报告电源事件。 | 电源管理和串口监视器。 |
| `02_lvgl_demo_v9` | 启动开发板显示屏并运行 LVGL Benchmark 演示。 | 466 × 466 AMOLED 显示屏和触摸。 |
| `03_esp-brookesia` | 运行 ESP-Brookesia 手机风格 UI 和 SquareLine 演示应用。 | AMOLED 显示屏、触摸和 PSRAM；ESP-IDF v6 使用 CI 覆盖配置。 |
| `04_Immersive_block` | 显示由运动控制的落块场景。 | AMOLED 显示屏、触摸和 QMI8658 IMU。 |
| `05_Spec_Analyzer` | 采集麦克风音频、计算 FFT 并显示频谱柱。 | AMOLED 显示屏，以及通过 ES7210 连接的两个板载麦克风。 |

请在每个工程自己的目录中以 `esp32s3` 为目标进行构建。详见
[快速入门](getting-started_ZH.md#使用-esp-idf-构建)。

## Arduino 示例

| 示例 | 用途 | 硬件 / 说明 |
| --- | --- | --- |
| `01_HelloWorld` | 基础显示初始化和文本输出。 | AMOLED 显示屏。 |
| `02_GFX_AsciiTable` | 使用 Arduino GFX 绘制 ASCII 字符表。 | AMOLED 显示屏。 |
| `03_LVGL_PCF85063_simpleTime` | 通过 LVGL 界面显示 RTC 日期和时间。 | PCF85063 RTC、显示屏和触摸。 |
| `04_LVGL_QMI8658_ui` | 显示实时加速度计和陀螺仪数据。 | QMI8658 IMU、显示屏和触摸。 |
| `05_LVGL_AXP2101_ADC_Data` | 显示电池、VBUS、温度和充电信息。 | AXP2101、显示屏和触摸。 |
| `06_LVGL_Widgets` | 运行 LVGL 音乐演示，并初始化开发板输入和传感器。 | 显示屏、触摸和 QMI8658。 |
| `07_LVGL_SD_Test` | 通过基于 LVGL 的开发板应用测试 microSD 访问。 | FAT/FAT32 microSD 卡。 |
| `08_ES8311` | 初始化 ES8311 音频并运行 LVGL Widgets 界面。 | ES8311 播放通路、外接扬声器、显示屏和触摸。 |
| `09_LC76G_I2C` | 通过 I2C 与 LC76G GNSS 通信。 | `-G` 版本板载该模块；其他版本需要兼容的 LC76G 硬件和适用天线。 |
| `10_Touch_CST9217` | 通过串口报告中断驱动的单点和双点原始触摸坐标。 | CST9217 触摸控制器；有意不初始化显示屏和 LVGL。 |

请使用 Arduino-ESP32 `3.3.10`、16 MB Flash、`app3M_fat9M_16MB` 分区方案和随附库进行
编译。详见[快速入门](getting-started_ZH.md#使用-arduino-构建)。

## Brookesia 工厂固件应用套件

`firmware/brookesia` 下维护的客户固件是独立的产品应用，不是单示例 CI 构建目标。其启动器包含：

| 应用 | 主要功能 | 硬件 / 数据通路 |
| --- | --- | --- |
| SquareLine | 演示可复用的 SquareLine/LVGL 界面。 | AMOLED 显示屏和触摸。 |
| Calculator | 提供触摸计算器。 | AMOLED 显示屏和触摸。 |
| DrawPanel | 提供白色绘图画布和触摸绘图工具。 | AMOLED 显示屏和触摸。 |
| SpecAnalyzer | 显示实时音频频谱。 | 通过 ES7210 连接的两个板载麦克风。 |
| MusicPlayer | 播放 MP3/WAV，并提供上一首、播放/暂停和下一首控制。 | ES8311 扬声器通路和 `/sdcard/music`，另有 SPIFFS 回退素材。 |
| Gallery | 显示基线 JPG/JPEG，并提供导航和幻灯片控制。 | `/sdcard/photos`；异步图片解码。 |
| VideoPlayer | 播放特意限制为低帧率的 MJPEG/PCM AVI。 | `/sdcard/video`；显示和共享音频服务。 |
| Recorder | 录制 24 kHz、16-bit 双声道 WAV。 | 两路 ES7210 麦克风和 `/sdcard/Waveshare/Recordings`。 |
| Settings | 控制 Wi-Fi、亮度、音量和存储，并显示电池/充电、RSSI 和 SD 状态。 | 原生 Wi-Fi、AXP2101、显示、音频和 microSD。 |
| AIChats | 提供 WakeNet/VAD/Opus 语音交互和 Xiaozhi 传输支持。 | Wi-Fi 及共享麦克风/扬声器服务；需要远程激活且服务可用。 |
| Gravitysphere | 在圆形屏幕边界内移动小球。 | QMI8658 加速度计。 |
| Crosshair | 显示圆形对准图案和可触摸切换的配色。 | AMOLED 显示屏和触摸。 |

工厂固件烧录、素材目录和硬件验收见中英双语[固件交付说明](../firmware/README.md)和
[SD 卡素材制作指南](../firmware/MEDIA_GUIDE.md)。

## CI 选择规则

Build Examples 工作流可以运行全部示例、一个示例名称或一个仓库相对路径。工作流手动触发选择器
示例包括：

- `all`
- `04_Immersive_block`
- `examples/esp-idf/05_Spec_Analyzer`
- `09_LC76G_I2C`
- `10_Touch_CST9217`

每个成功的源码构建都会生成一个 `*-combined.zip` 固件产物。为单个示例构建的产物不能替代完整
Brookesia 工厂镜像。
