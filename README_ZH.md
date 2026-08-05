<div align="center">
  <h1>ESP32-S3-Touch-AMOLED-1.75</h1>
  <p><strong>搭载 1.75 英寸 466 × 466 QSPI AMOLED 触摸屏的 ESP32-S3 开发板</strong></p>
  <p>
    <a href="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml"><img alt="示例构建" src="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml/badge.svg"></a>
    <a href="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest"><img alt="最新发布" src="https://img.shields.io/github/v/release/waveshareteam/ESP32-S3-Touch-AMOLED-1.75"></a>
    <a href="LICENSE"><img alt="许可证" src="https://img.shields.io/github/license/waveshareteam/ESP32-S3-Touch-AMOLED-1.75"></a>
  </p>
  <p>
    <a href="README.md">English</a> ·
    <a href="https://www.waveshare.net/shop/ESP32-S3-Touch-AMOLED-1.75.htm">🌐 产品页面</a> ·
    <a href="https://docs.waveshare.net/ESP32-S3-Touch-AMOLED-1.75/">📚 产品文档</a> ·
    <a href="https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest">📦 固件发布</a> ·
    <a href="docs/getting-started_ZH.md">🚀 快速开始</a> ·
    <a href="examples/esp-idf/">🧩 ESP-IDF 示例</a> ·
    <a href="examples/arduino/">🔧 Arduino 示例</a>
  </p>
  <img src="assets/ESP32-S3-Touch-AMOLED-1.75-details-1.jpg" alt="ESP32-S3-Touch-AMOLED-1.75" width="500">
</div>

---

## ✨ 概述

本仓库为 Waveshare ESP32-S3-Touch-AMOLED-1.75 提供示例源码、可复现的发布固件、通过源码维护的
Brookesia 应用固件、完整工厂恢复镜像、原理图以及中英双语用户文档。

本开发板采用 ESP32-S3R8，在紧凑尺寸中集成高分辨率圆形 AMOLED 屏、双点电容触摸、运动传感、
电源与电池管理、实时时钟、双麦克风音频、扬声器输出和 microSD 存储。

### 产品型号

| SKU | 产品名称 |
| --- | --- |
| `31261` | ESP32-S3-Touch-AMOLED-1.75，标准开发板 |
| `31262` | ESP32-S3-Touch-AMOLED-1.75-B，带外壳版本 |
| `31264` | ESP32-S3-Touch-AMOLED-1.75-G，LC76G GNSS 版本 |

各型号的随附内容与选配功能以官方产品页面为准。需要 GNSS 的示例不适用于标准版或 `-B` 版。

## 🖥️ 硬件概览

| 功能 | 器件 / 接口 |
| --- | --- |
| 主控 | ESP32-S3R8，双核 Xtensa LX7，最高 240 MHz |
| 存储 | 8 MB PSRAM、16 MB 外部 Flash |
| 无线 | 2.4 GHz Wi-Fi 802.11 b/g/n、Bluetooth 5 LE |
| 显示 | 1.75 英寸 CO5300 QSPI AMOLED，466 × 466，1670 万色 |
| 触摸 | CST9217 I2C 电容触控，支持双点触摸 |
| 电源管理 | AXP2101 PMIC、3.7 V 电池接口、充电与电池遥测 |
| 运动传感器 | QMI8658 六轴 IMU |
| 实时时钟 | PCF85063 RTC，通过电源子系统提供后备供电 |
| 音频输入 | ES7210 与两颗板载麦克风 |
| 音频输出 | ES8311 编解码器、功放扬声器通路与 MX1.25 扬声器接口 |
| 存储扩展 | 采用 1-bit SDMMC 的 microSD 卡槽 |
| USB 与按键 | USB-C 原生 USB、PWR 与 BOOT 按键 |
| 扩展接口 | 8-pin 2.54 mm 排母，引出电源、UART0、GPIO16/GPIO17/GPIO18 |
| 板级支持 | Managed component：[`waveshare/esp32_s3_touch_amoled_1_75`](https://components.espressif.com/components/waveshare/esp32_s3_touch_amoled_1_75) |
| 硬件资料 | [硬件参考](HARDWARE_REFERENCE_ZH.md)、[原理图](Schematic/)与[官方文档](https://docs.waveshare.net/ESP32-S3-Touch-AMOLED-1.75/) |

GPIO 映射、I2C 地址、音频与 SD 总线、扩展排针和共享资源注意事项见[硬件参考](HARDWARE_REFERENCE_ZH.md)。

## 📦 固件快速开始

请根据用途选择正确的固件形式：

| 固件形式 | 用途 | 位置 |
| --- | --- | --- |
| CI 发布包 | 可复现地测试单个 ESP-IDF 或 Arduino 示例 | [GitHub Releases](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/latest) |
| 工厂恢复镜像 | 从 `0x0` 恢复完整客户演示系统 | [`firmware/ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin`](firmware/ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin) |
| Brookesia 源码 | 使用 ESP-IDF v5.5.4 维护或重新构建应用套件 | [`firmware/brookesia/README_ZH.md`](firmware/brookesia/README_ZH.md) |
| SD 素材包 | 验证 MusicPlayer、Gallery、VideoPlayer 和 Recorder | [`firmware/SD-Card-Media-260805.zip`](firmware/SD-Card-Media-260805.zip) |

### 烧录发布示例

1. 从最新 Release 下载所需的 `*-combined.zip`。
2. 解压并运行 `python -m pip install esptool` 安装 esptool。
3. 使用带数据传输功能的 USB 线连接开发板。
4. Windows 运行 `flash_combined.bat COMx`，Linux 运行 `./flash_combined.sh /dev/ttyACM0`。
5. 如果开发板未自动重启，请手动复位。

> [!NOTE]
> 合并镜像从偏移地址 `0x0` 写入。每个压缩包还包含原始分区镜像、烧录脚本、命令文件、manifest
> 与校验值。

不要混用发布示例、工厂镜像，或来自不同软件包的分区镜像。工厂镜像的校验值与专用烧录命令见
[固件交付说明](firmware/README_ZH.md)。正常更新不需要清除 Flash。

## 📱 Brookesia 应用固件

通过源码维护的工厂应用包含 13 个适配圆形屏幕的应用：

- SquareLine、Calculator、DrawPanel 与 Crosshair。
- 使用 ES7210 双麦克风输入的 SpecAnalyzer 与 Recorder。
- 使用 microSD 卡的 MusicPlayer、Gallery 与 VideoPlayer。
- Settings：显示实时 AXP2101 电池信息、原生 Wi-Fi 状态、存储诊断并支持安全弹出。
- AIChats：可选保存文本历史；Gravitysphere：由 QMI8658 IMU 驱动。
- Button Test：直接读取 PWR/EXIO4 与 BOOT/GPIO0 的电平并完成按键诊断。

状态栏会跟随真实电池和 Wi-Fi 状态。媒体应用、合成测试素材格式、FFmpeg 命令、隐私提示与 SD 卡
目录结构见[素材制作指南](firmware/MEDIA_GUIDE_ZH.md)。

## 🧪 示例

### ESP-IDF

| 示例 | 主要功能 |
| --- | --- |
| [01_AXP2101](examples/esp-idf/01_AXP2101/) | 电源管理、充电与电池遥测 |
| [02_lvgl_demo_v9](examples/esp-idf/02_lvgl_demo_v9/) | LVGL 9 显示性能测试 |
| [03_esp-brookesia](examples/esp-idf/03_esp-brookesia/) | ESP-Brookesia 手机风格应用界面 |
| [04_Immersive_block](examples/esp-idf/04_Immersive_block/) | 运动控制的方块场景 |
| [05_Spec_Analyzer](examples/esp-idf/05_Spec_Analyzer/) | 麦克风 FFT 频谱分析 |

### Arduino

| 示例 | 主要功能 |
| --- | --- |
| [01_HelloWorld](examples/arduino/01_HelloWorld/) | 显示初始化与文字输出 |
| [02_GFX_AsciiTable](examples/arduino/02_GFX_AsciiTable/) | GFX 文字与字符渲染 |
| [03_LVGL_PCF85063_simpleTime](examples/arduino/03_LVGL_PCF85063_simpleTime/) | LVGL 实时时钟界面 |
| [04_LVGL_QMI8658_ui](examples/arduino/04_LVGL_QMI8658_ui/) | LVGL 加速度计与陀螺仪界面 |
| [05_LVGL_AXP2101_ADC_Data](examples/arduino/05_LVGL_AXP2101_ADC_Data/) | LVGL 电源与电池遥测 |
| [06_LVGL_Widgets](examples/arduino/06_LVGL_Widgets/) | LVGL 音乐界面、触摸与 IMU 集成 |
| [07_LVGL_SD_Test](examples/arduino/07_LVGL_SD_Test/) | LVGL 应用中的 microSD 访问 |
| [08_ES8311](examples/arduino/08_ES8311/) | ES8311 音频输出与 LVGL 界面 |
| [09_LC76G_I2C](examples/arduino/09_LC76G_I2C/) | 兼容硬件上的 LC76G I2C GNSS |
| [10_Touch_CST9217](examples/arduino/10_Touch_CST9217/) | 中断驱动的单点、双点原始触摸诊断 |

Arduino 捆绑库位于 [`examples/arduino/libraries`](examples/arduino/libraries/)。其中的上游示例仅作为
依赖，不属于第一方产品固件目标。完整说明见[示例目录](docs/examples_ZH.md)。

## 🛠️ 支持的工具链

| 范围 | 已验证版本 | 工程数 | 固件构建数 |
| --- | --- | ---: | ---: |
| ESP-IDF 示例 | `v5.5.4` | 5 | 5 |
| ESP-IDF 示例 | `v6.0.2` | 5 | 5 |
| Arduino-ESP32 示例 | `3.3.10` | 10 | 10 |
| Brookesia 源码固件 | ESP-IDF `v5.5.4` | 1 | 不属于示例矩阵 |

[Build Examples 工作流](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/actions/workflows/examples.yml)
针对当前源码树运行 2 个发现任务和 20 个构建/打包任务。历史 v1.0.1 发布早于
`10_Touch_CST9217`，因此包含 19 个固件包。矩阵与发布门禁见[持续集成](docs/ci_ZH.md)。

## 🗂️ 仓库结构

| 路径 | 用途 |
| --- | --- |
| [`README.md`](README.md) | 完整英文仓库说明 |
| [`HARDWARE_REFERENCE.md`](HARDWARE_REFERENCE.md) / [`HARDWARE_REFERENCE_ZH.md`](HARDWARE_REFERENCE_ZH.md) | 中英双语板级硬件参考 |
| [`assets/`](assets/) | 文档所用的官方产品图片 |
| [`examples/esp-idf/`](examples/esp-idf/) | 第一方 ESP-IDF 工程 |
| [`examples/arduino/`](examples/arduino/) | 第一方 Arduino 示例与捆绑库 |
| [`firmware/`](firmware/) | Brookesia 源码、工厂恢复镜像、SD 素材与双语交付说明 |
| [`releases/`](releases/) | 打包、产物下载与 Release 工具 |
| [`config/`](config/) | 共用 ESP-IDF 兼容配置 |
| [`docs/`](docs/) | 配置、示例、CI、组件、固件与故障排查文档 |
| [`Schematic/`](Schematic/) | 公开原理图 |
| [`scripts/`](scripts/) | CI 示例发现脚本 |
| [`.github/`](.github/) | GitHub Actions 与公开协作模板 |

## 📚 文档

- [文档中心](docs/README_ZH.md)
- [快速开始](docs/getting-started_ZH.md)
- [硬件参考](HARDWARE_REFERENCE_ZH.md)
- [示例目录](docs/examples_ZH.md)
- [故障排查](docs/troubleshooting_ZH.md)
- [固件与工厂恢复](docs/firmware_ZH.md)
- [固件交付说明](firmware/README_ZH.md)
- [素材制作指南](firmware/MEDIA_GUIDE_ZH.md)
- [Brookesia 源码固件](firmware/brookesia/README_ZH.md)
- [硬件验收](firmware/brookesia/HARDWARE_VALIDATION_ZH.md)
- [固件组件说明](firmware/brookesia/components/README_ZH.md)
- [仓库结构](docs/repository-structure_ZH.md)
- [持续集成](docs/ci_ZH.md)
- [组件说明](docs/components_ZH.md)
- [发布工具](releases/README_ZH.md)
- [变更记录](CHANGELOG_ZH.md)
- [官方产品文档](https://docs.waveshare.net/ESP32-S3-Touch-AMOLED-1.75/)
- [官方相关资料](https://docs.waveshare.net/ESP32-S3-Touch-AMOLED-1.75/Resources-And-Documents/)
- [官方 FAQ](https://docs.waveshare.net/ESP32-S3-Touch-AMOLED-1.75/FAQ/)
- [官方技术支持](https://docs.waveshare.net/ESP32-S3-Touch-AMOLED-1.75/Technical-Support/)

## 🤝 支持与贡献

欢迎提交贡献和可复现的问题报告。请提供开发板型号、示例路径、框架版本、复现步骤、预期结果、
实际结果和最小必要日志片段。公开日志或截图前，请移除 Wi-Fi 凭据、Token、对话内容、本机路径、
序列号、MAC 地址以及其他隐私或客户专属数据。

- [贡献指南](CONTRIBUTING_ZH.md) / [Contributing Guide](CONTRIBUTING.md)
- [技术支持](SUPPORT_ZH.md) / [Support](SUPPORT.md)
- [安全策略](SECURITY_ZH.md) / [Security Policy](SECURITY.md)
- [提交 Issue](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/issues/new/choose)

## 📄 许可证

本仓库采用 Apache License 2.0，详见 [LICENSE](LICENSE)。
