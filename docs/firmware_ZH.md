# 固件产物

[English](firmware.md)

## 客户文档

带日期的工厂固件与 SD 卡素材包说明见[固件交付说明](../firmware/README_ZH.md)。图片、WAV、MP3
以及 MJPEG/PCM AVI 的固件专用制作命令见[素材制作指南](../firmware/MEDIA_GUIDE_ZH.md)。带日期的
SD ZIP 中保留一份可独立阅读的双语素材指南与双语快速说明快照。

本仓库包含三种相互独立的固件形式：由标签触发的 CI 构建、通过源码维护的 Brookesia 移植工程，
以及工厂恢复镜像。

## 发布固件

GitHub Actions 会从以下目录构建由源码维护的示例：

- `examples/esp-idf/`
- `examples/arduino/`

每个发布产物都是一个 `*-combined.zip` 包，其中同时包含：

- 可从偏移地址 `0x0` 一次性烧录的 `*-combined.bin`。
- 原始 Bootloader、分区表、应用程序以及其他需要按指定偏移地址烧录的二进制文件。

正常安装请使用 `flash_combined.sh` 或 `flash_combined.bat`。只有明确需要原始烧录布局时才使用
分区镜像脚本；两种烧录方式的命令也会记录在文本文件中。

包内 manifest 会记录源码 Git SHA、框架版本、目标芯片、二进制偏移地址、大小和 SHA-256。
GitHub Release 中的 `manifest-combined-assets.json` 则记录全部已发布 ZIP 的校验值。

## Brookesia 源码固件

`firmware/brookesia/` 是面向本 ESP32-S3 硬件的 ESP-IDF 5.5 工程。它移植了 ESP32-P4
Brookesia 固件的可复用应用层，同时使用本板原生的显示、触摸、音频和 Wi-Fi 通路。构建方法与
支持的应用范围见[Brookesia 源码固件说明](../firmware/brookesia/README_ZH.md)。

源码工程包含 SquareLine、Calculator、DrawPanel、SpecAnalyzer、MusicPlayer、Gallery、
VideoPlayer、Recorder、Settings、AIChats、Gravitysphere、Crosshair 和 Button Test。Settings 与
Phone 状态栏使用实时 AXP2101 电池数据及原生 Wi-Fi 状态。Settings 还提供 SD 卡信息、CRC 读写
基准测试、诊断导出、AIChats 文本历史控制和安全弹出。状态组件与应用布局使用圆屏安全区域；
Gravitysphere 将 QMI8658 驱动的小球限制在真实圆形边界内，Crosshair 则提供全屏光学对准图案，
用于检查面板旋转和贴合效果。Button Test 直接从 TCA9554 EXIO4 读取 PWR、从 GPIO0 读取 BOOT，
不使用 AXP2101 按键寄存器。

该工程是源码固件，不是工厂镜像，也不属于示例发现 CI 矩阵。在把其输出作为恢复镜像之前，必须在
目标板上完成构建和实机验证。

## 工厂恢复固件

`firmware/ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin` 是当前用于工厂烧录和恢复的镜像，
生成日期为 2026-08-05。它不是由 CI 生成，也不是源码示例构建产物，并且不会被重新包装为发布
示例。配套客户 SD 素材另行提供为 `firmware/SD-Card-Media-260805.zip`。

该镜像仅用于恢复工厂演示固件；若需要可复现的示例固件，请使用带标签的 Release 包。

## 烧录布局安全

本板和源码工程使用 16 MiB Flash 布局。不要混用不同软件包中的 Bootloader、分区表或应用程序。
旧的 32 MiB 镜像头可能在本板上造成 Flash 探测错误；只有确认出现这一特定情况时，才清除 Flash
并安装完整的 v1.0.1 或更新版合并包。

## 生成文件

- CI 打包输出：`release-artifacts/`
- 本地打包输出：`releases/dist/`
- 下载的 CI 产物：`releases/downloads/`

上述路径以及 ESP-IDF 构建目录、managed components、自动生成的依赖锁和 sdkconfig 文件均被 Git
忽略，不应提交。发布产物会在标签工作流成功并通过发布暂存脚本验证后上传到 GitHub。
