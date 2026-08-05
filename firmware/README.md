# ESP32-S3-Touch-AMOLED-1.75 Firmware Delivery Guide

[简体中文](README_ZH.md)

Release date: 2026-08-05

Filename date code: `260805`

This directory contains the complete customer factory image, an SD-card validation
media package, media-production instructions, and the ESP-IDF project used to
maintain and rebuild the firmware.

## Delivered files

| File or directory | Purpose |
| --- | --- |
| `ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin` | Complete 16 MiB factory image, written once at offset `0x0` |
| `SD-Card-Media-260805.zip` | SD directory structure and project-generated synthetic validation fixtures for MusicPlayer, Gallery, VideoPlayer, and Recorder |
| [`MEDIA_GUIDE.md`](MEDIA_GUIDE.md) | Image, audio, and AVI production guide with FFmpeg and ffprobe commands |
| [`brookesia/`](brookesia/README.md) | ESP-IDF v5.5.4 source project used to produce the factory image |

## Documentation

First-party firmware documentation is maintained as explicit English and Simplified
Chinese pairs:

| Topic | English | 简体中文 |
| --- | --- | --- |
| Factory image and SD package | [Firmware Delivery Guide](README.md) | [固件交付说明](README_ZH.md) |
| Media conversion and validation | [Media Production Guide](MEDIA_GUIDE.md) | [素材制作指南](MEDIA_GUIDE_ZH.md) |
| Brookesia source project | [Brookesia Firmware](brookesia/README.md) | [Brookesia 固件](brookesia/README_ZH.md) |
| Device acceptance checklist | [Hardware Validation](brookesia/HARDWARE_VALIDATION.md) | [硬件验收](brookesia/HARDWARE_VALIDATION_ZH.md) |
| Local components and upstream boundary | [Component Guide](brookesia/components/README.md) | [组件说明](brookesia/components/README_ZH.md) |

Documentation inside `managed_components/`, `third_party/`, or an embedded
upstream source tree belongs to its upstream project and is intentionally not
duplicated or translated here.

## Factory firmware

- Target: ESP32-S3-Touch-AMOLED-1.75
- ESP-IDF: v5.5.4
- Flash size: 16 MiB
- Flash offset: `0x0`
- File size: 16,777,216 bytes
- SHA-256: `0876f10a6f2a693d83d51c417e44131ed2c81b952c78d6cd794b03bfa3e218d2`

The image already combines the bootloader, partition table, initial OTA data,
ESP-SR models, Brookesia application, and SPIFFS filesystem. It is a complete
image; do not mix it with offset binaries from another build.

Verify the file first:

```powershell
Get-FileHash .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin -Algorithm SHA256
```

Replace `COMx` with the device port, then flash the image:

```powershell
python -m esptool --chip esp32s3 --port COMx --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 .\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

A normal update does not require `erase-flash`. If automatic reset cannot enter
download mode, hold BOOT, tap RESET, release BOOT, and retry. Do not disconnect
USB or power while flashing.

## SD-card media package

- File: `SD-Card-Media-260805.zip`
- SHA-256: `ab92e1974f395091c62ac58f71cc8185e43f5db2ed89d96940bed735d0884f74`
- Filesystem: FAT or FAT32; do not use exFAT or NTFS

Extract the ZIP contents directly to the SD-card root. Do not put them inside an
additional package directory. The expected layout is:

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

The dated ZIP remains an immutable delivery artifact and contains a self-contained
bilingual `MEDIA_GUIDE.md` snapshot. The repository documentation is separated
into [English](MEDIA_GUIDE.md) and [Simplified Chinese](MEDIA_GUIDE_ZH.md) pages
for clearer online navigation.

The safe copy helper can be run from the repository root. It does not format the
card and does not replace existing files unless `-Overwrite` is supplied:

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\prepare_sd_card.ps1 -Drive X:
```

Replace `X:` with the actual SD-card drive and confirm the target really is the
SD card before running the command. When the card is in a PC reader, eject it
through Windows after copying. When it is installed in the device, leave all
media applications, choose `Settings > Storage > Safe eject`, wait for unmount
confirmation, and only then remove it physically.

See the [Media Production Guide](MEDIA_GUIDE.md) for exact image, music, and AVI
requirements and the recommended FFmpeg recipes.

> [!IMPORTANT]
> JSONL history under `Waveshare/AIChats` may contain real conversation text.
> Before sharing, servicing, or redelivering an SD card, disable AIChats history
> and back up or delete those files. Files under `Waveshare/Diagnostics` may
> also contain device, reset, storage, battery, and Wi-Fi state and should be
> reviewed before external sharing.

## Delivery preflight

Verify the complete firmware, SD ZIP, and all nine packaged media fixtures
offline:

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline
```

After activating ESP-IDF v5.5.4 and connecting the board, omit `-Offline` and
provide the actual serial port with `-Port COMx` to check the port, `idf.py`,
and esptool together. Follow the complete
[Hardware Validation](brookesia/HARDWARE_VALIDATION.md) procedure for device
acceptance.

## Source project

[`brookesia/`](brookesia/README.md) is the source project corresponding to this
factory image. It uses the board-native 466 × 466 CO5300 QSPI AMOLED, CST9217
touch controller, ES8311 speaker codec, ES7210 dual-microphone input, AXP2101
power management, QMI8658 IMU, 1-bit SDMMC, and native ESP32-S3 Wi-Fi.
