# ESP32-S3-Touch-AMOLED-1.75 固件交付说明

[English](README.md)

发布日期：2026-08-05

文件名日期码：`260805`

本目录包含可直接交付给客户的完整工厂固件、SD 卡验证素材包、素材制作说明，
以及用于维护和重新构建固件的 ESP-IDF 工程。

## 交付文件

| 文件或目录 | 用途 |
| --- | --- |
| `ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin` | 16 MiB 完整工厂镜像，从地址 `0x0` 一次性烧录 |
| `SD-Card-Media-260805.zip` | MusicPlayer、Gallery、VideoPlayer 和 Recorder 的 SD 卡目录与项目生成的合成验证素材 |
| [`MEDIA_GUIDE_ZH.md`](MEDIA_GUIDE_ZH.md) | 图片、音频与 AVI 素材制作指南，包含 FFmpeg 与 ffprobe 命令 |
| [`brookesia/`](brookesia/README_ZH.md) | 生成工厂镜像的 ESP-IDF v5.5.4 源码工程 |

## 文档

第一方固件文档均以独立的英文与简体中文文件配对维护：

| 主题 | 简体中文 | English |
| --- | --- | --- |
| 工厂镜像与 SD 素材包 | [固件交付说明](README_ZH.md) | [Firmware Delivery Guide](README.md) |
| 素材转换与校验 | [素材制作指南](MEDIA_GUIDE_ZH.md) | [Media Production Guide](MEDIA_GUIDE.md) |
| Brookesia 源码工程 | [Brookesia 固件](brookesia/README_ZH.md) | [Brookesia Firmware](brookesia/README.md) |
| 设备验收清单 | [硬件验收](brookesia/HARDWARE_VALIDATION_ZH.md) | [Hardware Validation](brookesia/HARDWARE_VALIDATION.md) |
| 本地组件与上游边界 | [组件说明](brookesia/components/README_ZH.md) | [Component Guide](brookesia/components/README.md) |

`managed_components/`、`third_party/` 或嵌入式上游源码树中的文档归其上游项目维护，
本仓库不会重复翻译或改写，以免后续产生内容漂移。

## 工厂固件

- 目标板：ESP32-S3-Touch-AMOLED-1.75
- ESP-IDF：v5.5.4
- Flash 容量：16 MiB
- 烧录地址：`0x0`
- 文件大小：16,777,216 字节
- SHA-256：`0876f10a6f2a693d83d51c417e44131ed2c81b952c78d6cd794b03bfa3e218d2`

该镜像已经合并 Bootloader、分区表、初始 OTA 数据、ESP-SR 模型、Brookesia 主程序和
SPIFFS 文件系统。它是完整镜像，不要再与其他构建生成的分区文件混合烧录。

先校验文件：

```powershell
Get-FileHash .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin -Algorithm SHA256
```

将 `COMx` 替换为设备端口后烧录：

```powershell
python -m esptool --chip esp32s3 --port COMx --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

正常更新不需要执行 `erase-flash`。如果自动复位无法进入下载模式，请按住 BOOT、
短按 RESET，再松开 BOOT 后重试。烧录期间不要拔出 USB 或断电。

## SD 卡素材包

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

带日期的 ZIP 是不可变的交付产物，其中保留一份可独立阅读的中英双语
`MEDIA_GUIDE.md` 快照。为了便于在线浏览，仓库中的说明拆分为
[简体中文](MEDIA_GUIDE_ZH.md)与[英文](MEDIA_GUIDE.md)页面。

也可以在仓库根目录使用安全复制脚本。脚本不会格式化 SD 卡，也不会在未指定
`-Overwrite` 时覆盖同名文件：

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\prepare_sd_card.ps1 -Drive X:
```

请先把 `X:` 替换为实际的 SD 卡盘符，并确认目标盘确实是 SD 卡。卡在电脑读卡器中时，
复制结束后通过 Windows 的“弹出”功能安全移除；卡仍插在设备中时，应先退出媒体应用，
再在 `Settings > Storage > Safe eject` 中卸载，确认完成后才能物理拔卡。

图片、音乐和 AVI 视频的具体格式与 FFmpeg 命令见[素材制作指南](MEDIA_GUIDE_ZH.md)。

> [!IMPORTANT]
> `Waveshare/AIChats` 中的 JSONL 历史可能包含真实对话文本。共享、返修或重新交付
> SD 卡前，请关闭 AIChats 历史记录，并备份或删除这些文件。
> `Waveshare/Diagnostics` 中也可能含有设备、复位、存储、电池和 Wi-Fi 状态信息，
> 应审核后再对外分享。

## 交付前校验

离线校验完整固件、SD ZIP 以及包内 9 个测试素材：

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline
```

激活 ESP-IDF v5.5.4 并连接设备后，去掉 `-Offline` 并通过 `-Port COMx`
指定实际串口，即可同时检查串口、`idf.py` 和 esptool。完整实机验收步骤见
[硬件验收](brookesia/HARDWARE_VALIDATION_ZH.md)。

## 源码工程

[`brookesia/`](brookesia/README_ZH.md) 是本工厂镜像对应的源码工程。它使用本板原生的
466 × 466 CO5300 QSPI AMOLED、CST9217 触摸、ES8311 扬声器编解码器、
ES7210 双麦克风输入、AXP2101 电源管理、QMI8658 IMU、1-bit SDMMC 和
ESP32-S3 原生 Wi-Fi。
