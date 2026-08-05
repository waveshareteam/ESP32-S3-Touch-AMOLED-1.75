# 快速入门

**简体中文** | [English](getting-started.md)

本指南介绍 ESP32-S3-Touch-AMOLED-1.75 的 Release 固件、完整工厂镜像、ESP-IDF 源码构建和
Arduino 源码构建。

## 开始前的准备

需要准备：

- 一块 ESP32-S3-Touch-AMOLED-1.75 开发板。
- 一根支持数据传输的 USB 线和稳定的 USB 电源。
- 系统为开发板分配的串口。
- 烧录预编译固件时需要 Python 3。
- 只有从源码构建时才需要 ESP-IDF 或 Arduino 工具。

请只使用面向本开发板的固件和设置。工程、Release 构建产物和工厂镜像均使用 16 MB Flash
布局。不要混用不同构建生成的 Bootloader、分区表、应用程序、模型或文件系统二进制文件。

## 烧录 Release 固件包

Release 固件包由 GitHub Actions 根据对应标签的源码生成。每个包对应一个示例和一个受支持的
工具链；它与 Brookesia 工厂镜像不是同一种交付物。

1. 打开 [Releases 页面](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases)。
2. 下载所需示例及框架版本对应的 `*-combined.zip`。
3. 解压缩该文件。
4. 安装 esptool：

```bash
python -m pip install esptool
```

5. 烧录合并镜像。

Linux 或 macOS：

```bash
./flash_combined.sh /dev/ttyACM0
```

Windows：

```bat
flash_combined.bat COMx
```

请把示例端口替换为开发板实际使用的端口。脚本会把合并二进制文件写入 `0x0`。同一压缩包还
包含拆分二进制文件，以及用于按偏移地址烧录的 `flash.sh` / `flash.bat`；应完整使用同一压缩包
中的一种烧录方式，不要混用两种方式。

如果自动复位无法进入下载模式，请按住 BOOT、短按 RESET，启动烧录命令，并在开始写入后松开
BOOT。

## 烧录工厂镜像

客户工厂镜像为
[`firmware/ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin`](../firmware/ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin)。
它是从 `0x0` 一次性写入的完整 16 MiB 镜像，已经合并 Bootloader、分区表、初始 OTA 数据、
ESP-SR 模型、Brookesia 应用程序和 SPIFFS 文件系统。

在仓库根目录中，把 `COMx` 替换为开发板端口后运行：

```powershell
python -m esptool --chip esp32s3 --port COMx --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 .\firmware\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

正常更新不需要擦除整片 Flash。已发布的校验值、SD 卡素材包和实机验证步骤见中英双语
[固件交付说明](../firmware/README_ZH.md)。

## 使用 ESP-IDF 构建

Release 构建支持 ESP-IDF `v5.5.4` 和 `v6.0.2`。激活所选 ESP-IDF 环境，然后从仓库根目录
构建工程：

```bash
idf.py -C examples/esp-idf/02_lvgl_demo_v9 \
  -B build/02_lvgl_demo_v9 \
  set-target esp32s3 build
```

使用同一个构建目录烧录并监视串口：

```bash
idf.py -C examples/esp-idf/02_lvgl_demo_v9 \
  -B build/02_lvgl_demo_v9 \
  -p PORT flash monitor
```

配置期间，ESP-IDF 组件管理器会下载托管依赖。ESP-Brookesia 示例针对 ESP-IDF v6 额外提供
`sdkconfig.defaults.v6` 覆盖配置，CI 会自动应用该配置。

`firmware/brookesia` 下的客户 Brookesia 工程使用 ESP-IDF `v5.5.4` 维护和验证。首次完整安装
必须同时包含应用程序、分区表、ESP-SR 模型和存储镜像；如果希望单文件安装，请使用随附的完整
工厂镜像。

## 使用 Arduino 构建

已验证的 Arduino-ESP32 Core 版本为 `3.3.10`。使用 ESP32-S3 开发板目标，并选择：

- Flash 大小：16 MB。
- 分区方案：`app3M_fat9M_16MB`。
- 随附库目录：`examples/arduino/libraries`。

Arduino CLI 示例：

```bash
arduino-cli core install esp32:esp32@3.3.10

arduino-cli compile \
  --fqbn "esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB" \
  --libraries examples/arduino/libraries \
  examples/arduino/01_HelloWorld
```

在 Arduino IDE 中，把 `examples/arduino/libraries` 下的文件夹加入 Sketchbook 库目录，或者
直接使用随附副本作为所需版本的来源。上传前请选择相同的 Flash 大小和分区方案。如果 IDE 选择了
不兼容的全局库副本，请删除该重复副本或降低其优先级。

## 示例所需硬件

- `07_LVGL_SD_Test` 需要 FAT/FAT32 microSD 卡。
- `08_ES8311` 测试 ES8311 播放通路和外接扬声器连接。
- `09_LC76G_I2C` 需要 `-G` 版本，或通过 I2C 正确连接的同等 LC76G 硬件。
- `10_Touch_CST9217` 通过串口监视器报告原始触摸坐标，并且有意不初始化显示屏或 LVGL。
- `04_Immersive_block` 使用 QMI8658 IMU 作为运动输入。
- `05_Spec_Analyzer` 通过 ES7210 使用两个板载麦克风。

## 后续步骤

完整源码示例列表见[示例目录](examples_ZH.md)，共享总线和外设分配见
[硬件参考](../HARDWARE_REFERENCE_ZH.md)，烧录与运行故障见[故障排查](troubleshooting_ZH.md)。
工厂固件所需的媒体格式和 FFmpeg 命令见 [SD 卡素材制作指南](../firmware/MEDIA_GUIDE_ZH.md)。
