# ESP32-S3-Touch-AMOLED-1.75 固件交付说明 / Firmware Delivery Guide

版本日期 / Release date: 2026-08-05

命名日期码 / Filename date code: `260805`

---

## 中文说明

本目录包含可直接交付给客户的完整工厂固件、SD 卡示例素材、双语素材制作指南，以及用于维护和重新构建固件的 ESP-IDF 工程。

### 交付文件

| 文件或目录 | 用途 |
| --- | --- |
| `ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin` | 16 MiB 完整工厂镜像，从地址 `0x0` 一次性烧录 |
| `SD-Card-Media-260805.zip` | MusicPlayer、Gallery、VideoPlayer 和 Recorder 的 SD 卡测试目录与项目生成的合成测试素材 |
| [`MEDIA_GUIDE.md`](MEDIA_GUIDE.md) | 中英双语素材制作指南，包含 FFmpeg 转换和 ffprobe 检查命令 |
| `brookesia/` | 生成本次工厂镜像的 ESP-IDF v5.5.4 源码工程 |

### 工厂固件

- 目标板：ESP32-S3-Touch-AMOLED-1.75
- ESP-IDF：v5.5.4
- Flash 容量：16 MiB
- 烧录地址：`0x0`
- 文件大小：16,777,216 字节
- SHA-256：`0876f10a6f2a693d83d51c417e44131ed2c81b952c78d6cd794b03bfa3e218d2`

该文件已经合并 Bootloader、分区表、初始 OTA 数据、ESP-SR 模型、Brookesia 主程序和 SPIFFS 文件系统。它是完整镜像，不要再与其他构建生成的分区文件混合烧录。

先校验文件：

```powershell
Get-FileHash .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin -Algorithm SHA256
```

将 `COMx` 替换为设备端口后烧录：

```powershell
python -m esptool --chip esp32s3 --port COMx --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

正常更新不需要执行 `erase-flash`。如果自动复位无法进入下载模式，请按住 BOOT、短按 RESET，再松开 BOOT 后重试。烧录期间不要拔出 USB 或断电。

### SD 卡素材包

- 文件：`SD-Card-Media-260805.zip`
- SHA-256：`ab92e1974f395091c62ac58f71cc8185e43f5db2ed89d96940bed735d0884f74`
- 文件系统：FAT 或 FAT32；不要使用 exFAT 或 NTFS

把 ZIP 内的内容直接解压到 SD 卡根目录，而不是再套一层同名目录。正确结构如下：

```text
SD card root
├─ music\
├─ photos\
├─ video\
├─ Waveshare\
│  ├─ Recordings\
│  ├─ AIChats\
│  └─ Diagnostics\
├─ README.txt
├─ MEDIA_GUIDE.md
└─ media_manifest.json
```

也可以在仓库根目录使用安全复制脚本。脚本不会格式化 SD 卡，也不会在未指定 `-Overwrite` 时覆盖同名文件：

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\prepare_sd_card.ps1 -Drive X:
```

请先把示例中的 `X:` 替换为实际的 SD 卡盘符，并确认目标盘确实是 SD 卡。卡在电脑读卡器中时，复制结束后通过 Windows 的“弹出”功能安全移除；卡仍插在设备中时，应先退出媒体应用，再在 `Settings > Storage > Safe eject` 中卸载，然后才能物理拔卡。图片、音乐和 AVI 视频的具体格式与 FFmpeg 命令见 [`MEDIA_GUIDE.md`](MEDIA_GUIDE.md)。

隐私提示：`Waveshare/AIChats` 中的 JSONL 历史可能包含真实对话文本。共享、返修或重新交付 SD 卡前，请关闭 AIChats 历史记录，并备份或删除这些文件。`Waveshare/Diagnostics` 中也可能含有设备、复位、存储、电池和 Wi-Fi 状态信息，应审核后再对外分享。

### 交付前校验

离线校验完整固件、SD ZIP 以及包内 9 个测试素材：

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline
```

激活 ESP-IDF v5.5.4 并连接设备后，去掉 `-Offline` 并通过 `-Port COMx` 指定实际串口，即可同时检查串口、`idf.py` 和 esptool。完整实机验收步骤见 [`brookesia/HARDWARE_VALIDATION.md`](brookesia/HARDWARE_VALIDATION.md)。

### 源码说明

`brookesia/` 是本工厂镜像对应的源码工程。它使用本板原生的 466 × 466 CO5300 QSPI AMOLED、CST9217 触摸、ES8311 扬声器编解码器、ES7210 双麦克风输入、AXP2101 电源管理、QMI8658 IMU、1-bit SDMMC 和 ESP32-S3 原生 Wi-Fi。

---

## English

This directory contains the complete customer factory image, an SD-card validation media package, a bilingual media-production guide, and the ESP-IDF project used to maintain and rebuild the firmware.

### Delivered files

| File or directory | Purpose |
| --- | --- |
| `ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin` | Complete 16 MiB factory image, written once at offset `0x0` |
| `SD-Card-Media-260805.zip` | SD directory structure and project-generated synthetic validation fixtures for MusicPlayer, Gallery, VideoPlayer, and Recorder |
| [`MEDIA_GUIDE.md`](MEDIA_GUIDE.md) | Bilingual media guide with FFmpeg conversion and ffprobe validation commands |
| `brookesia/` | ESP-IDF v5.5.4 source project used to produce this factory image |

### Factory firmware

- Target: ESP32-S3-Touch-AMOLED-1.75
- ESP-IDF: v5.5.4
- Flash size: 16 MiB
- Flash offset: `0x0`
- File size: 16,777,216 bytes
- SHA-256: `0876f10a6f2a693d83d51c417e44131ed2c81b952c78d6cd794b03bfa3e218d2`

The image already combines the bootloader, partition table, initial OTA data, ESP-SR models, Brookesia application, and SPIFFS filesystem. It is a complete image; do not mix it with offset binaries from another build.

Verify the file first:

```powershell
Get-FileHash .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin -Algorithm SHA256
```

Replace `COMx` with the device port, then flash the image:

```powershell
python -m esptool --chip esp32s3 --port COMx --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

A normal update does not require `erase-flash`. If automatic reset cannot enter download mode, hold BOOT, tap RESET, release BOOT, and retry. Do not disconnect USB or power while flashing.

### SD-card media package

- File: `SD-Card-Media-260805.zip`
- SHA-256: `ab92e1974f395091c62ac58f71cc8185e43f5db2ed89d96940bed735d0884f74`
- Filesystem: FAT or FAT32; do not use exFAT or NTFS

Extract the contents of the ZIP directly to the root of the SD card. Do not place them inside an additional package directory. The expected layout is:

```text
SD card root
├─ music\
├─ photos\
├─ video\
├─ Waveshare\
│  ├─ Recordings\
│  ├─ AIChats\
│  └─ Diagnostics\
├─ README.txt
├─ MEDIA_GUIDE.md
└─ media_manifest.json
```

The safe copy helper can also be run from the repository root. It does not format the card and does not replace existing files unless `-Overwrite` is supplied:

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\prepare_sd_card.ps1 -Drive X:
```

Replace `X:` with the actual SD-card drive and confirm the target really is the SD card before running the command. When the card is in a PC reader, eject it through Windows after copying. When it is still installed in the device, leave all media applications, choose `Settings > Storage > Safe eject`, wait for unmount confirmation, and only then remove it physically. See [`MEDIA_GUIDE.md`](MEDIA_GUIDE.md) for the exact image, music, and AVI requirements and the recommended FFmpeg recipes.

Privacy notice: JSONL history under `Waveshare/AIChats` may contain real conversation text. Before sharing, servicing, or redelivering an SD card, disable AIChats history and back up or delete those files. Files under `Waveshare/Diagnostics` may also contain device, reset, storage, battery, and Wi-Fi state and should be reviewed before external sharing.

### Delivery preflight

Verify the complete firmware, SD ZIP, and all nine packaged media fixtures offline:

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline
```

After activating ESP-IDF v5.5.4 and connecting the board, omit `-Offline` and provide the actual serial port with `-Port COMx` to check the port, `idf.py`, and esptool together. The complete device acceptance procedure is in [`brookesia/HARDWARE_VALIDATION.md`](brookesia/HARDWARE_VALIDATION.md).

### Source project

`brookesia/` is the source project corresponding to this factory image. It uses the board-native 466 × 466 CO5300 QSPI AMOLED, CST9217 touch controller, ES8311 speaker codec, ES7210 dual-microphone input, AXP2101 power management, QMI8658 IMU, 1-bit SDMMC, and native ESP32-S3 Wi-Fi.
