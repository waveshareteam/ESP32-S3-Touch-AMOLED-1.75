# Brookesia firmware

[简体中文](README_ZH.md)

Customer-facing delivery and media-production instructions are in
[`../README.md`](../README.md) and
[`../MEDIA_GUIDE.md`](../MEDIA_GUIDE.md). Local application, service, and
safe-override boundaries are documented in the
[Component Guide](components/README.md).

This project ports the reusable application layer from the
ESP32-P4-WIFI6-Touch-LCD-4B Brookesia firmware to the
ESP32-S3-Touch-AMOLED-1.75.

The firmware deliberately uses the target board's native BSP for the 466 x 466
CO5300 QSPI AMOLED, CST9217 touch controller, ES8311/ES7210 audio devices, and
native ESP32-S3 Wi-Fi. P4-only MIPI DSI, PPA, ESP-Hosted/C6, camera, Ethernet,
relay, and RS485 code is not included.

Included applications:

- SquareLine demo
- Calculator
- DrawPanel
- SpecAnalyzer with live dual-microphone FFT through ES7210
- MusicPlayer with MP3/WAV playback from `/sdcard/music` and a
  `/spiffs/music` fallback
- Gallery for baseline JPG/JPEG images from `/sdcard/photos`, with asynchronous
  decode, previous/next controls, and a slideshow mode
- VideoPlayer for deliberately low-frame-rate MJPEG/PCM AVI files from
  `/sdcard/video`
- Recorder for 24 kHz, 16-bit stereo WAV capture from the two front ES7210
  microphones to `/sdcard/Waveshare/Recordings`; it checkpoints a temporary
  `.wav.partial` every five seconds and publishes the final `.wav` only after
  a synchronized close
- Settings with native Wi-Fi, AMOLED brightness, volume, AXP2101 battery
  telemetry, charging state, Wi-Fi RSSI, SD card information, a CRC benchmark,
  diagnostic export, and safe eject
- AIChats with WakeNet, VAD, Opus audio, activation, and Xiaozhi transports
- Gravitysphere driven by live QMI8658 accelerometer data, with the ball and
  its glow constrained to the panel's true circular boundary
- Crosshair, a full-screen circular alignment target with concentric rings,
  cardinal ticks, center axes, and touch-selectable contrast palettes

## SD card layout

The card is mounted on demand as FAT/FAT32 at `/sdcard` over the board's 1-bit
SDMMC connection. Long UTF-8 filenames are enabled. Use these directories:

| Directory | Purpose and format |
| --- | --- |
| `/sdcard/music` | MP3 and WAV tracks; `/sdcard/Music` is accepted for compatibility |
| `/sdcard/photos` | Baseline JPG/JPEG, up to 4 MiB per file and 128 indexed photos |
| `/sdcard/video` | MJPEG AVI; optional audio must be 16-bit PCM mono/stereo |
| `/sdcard/Waveshare/Recordings` | Stereo WAV files created by Recorder |
| `/sdcard/Waveshare/AIChats` | Optional text-only JSONL chat history |
| `/sdcard/Waveshare/Diagnostics` | Device/SD/battery/Wi-Fi diagnostic snapshots |

Video playback is intentionally capped at 10 displayed frames per second. For
this 466 x 466 QSPI panel, encode MJPEG at about 320 x 240 or 360 x 360, 10 fps,
and keep every frame at or below 466 x 466. PCM audio may use 8, 12, 16, 24,
32, 44.1, or 48 kHz. H.264 and compressed AVI audio are not supported.

The first storage lease after an idle interval probes the mounted card. If a
card was removed unexpectedly and then reinserted, the service discards the
stale mount and remounts it before handing the filesystem to an application.
Safe eject remains latched until the user explicitly chooses **Rescan card**.

Copyright-free WAV, baseline JPEG, and MJPEG/PCM AVI fixtures are provided in
`firmware/SD-Card-Media-260805.zip`. The six WAV tracks also cover
MusicPlayer's second list page. `tools/prepare_sd_card.ps1` reads the ZIP
directly and copies the fixtures to a FAT/FAT32 removable card without
formatting it or replacing existing files.
The ZIP also contains a bilingual `README.txt` and the complete bilingual
`MEDIA_GUIDE.md`, including the firmware-specific FFmpeg and ffprobe recipes.
The complete COM-port, UI, storage, audio-ownership, safe-eject, and soak procedure is in
[`HARDWARE_VALIDATION.md`](HARDWARE_VALIDATION.md).
Run `tools/hardware_preflight.ps1 -Offline` to verify the release hashes and
fixture manifest now; rerun it without `-Offline` after activating ESP-IDF and
connecting the target board.

The Phone status bar is also hardware-backed: the battery icon and percentage
follow the AXP2101 fuel gauge and charging state, while the Wi-Fi icon follows
the station connection and actual RSSI level. The resident status service uses
the official board example's safe charge profile (TS measurement off, 50 mA
precharge, 400 mA constant current, 25 mA termination, and 4.2 V target),
restores the persisted Wi-Fi switch at boot, and reconnects even when Settings
is closed. A board-specific round-screen
stylesheet moves these widgets into the visible top chord instead of the
nonexistent rectangular corners. The launcher uses a centered 2 x 2 safe grid
per page and preserves each 112 x 112 icon instead of shrinking it into the
generic rectangular-phone layout.

The Crosshair launcher icon is kept as a 112 x 112 rounded PNG and converted
to `ARGB8888` C data with the official LVGL v9 `scripts/LVGLImage.py` tool from
the managed `lvgl` component. After dependencies are resolved, it can be
regenerated with:

```text
python managed_components/lvgl__lvgl/scripts/LVGLImage.py --ofmt C --cf ARGB8888 --name img_app_crosshair --output components/Crosshair/assets components/Crosshair/assets/img_app_crosshair.png
```

## Build

Use ESP-IDF 5.5 and build for `esp32s3`:

```text
idf.py -C firmware/brookesia set-target esp32s3 build
```

The project uses the Brookesia core and SquareLine component already maintained
under `examples/esp-idf/03_esp-brookesia/components/`; it does not duplicate
those large source trees.

The 16 MB partition table reserves an 8 MB application, a 6 MB `storage`
SPIFFS partition, and a 960 KB ESP-SR model partition. The build generates and
flashes the selected WakeNet model and stages the AIChats font from the managed
`xiaozhi-fonts` component. The generated SPIFFS image contains no third-party
music or prompt audio.

Use `idf.py -C firmware/brookesia flash monitor` for a complete flash. A full
flash is required when installing AIChats for the first time because the
partition table, `srmodels.bin`, application, and `storage.bin` must all match.

## Hardware validation

A successful ESP-IDF v5.5.4 build verifies that all twelve applications, the
storage image, and the ESP-SR model image compile and package together. The
current dated factory image and its delivery checks are documented in
[`../README.md`](../README.md). After any source change, a regenerated factory
candidate must repeat the target-board checks in
[`HARDWARE_VALIDATION.md`](HARDWARE_VALIDATION.md), including display, touch,
AXP2101 fuel-gauge behavior, QMI8658 orientation, Wi-Fi, microphone/speaker
audio, storage, and long-running application switching, before it replaces the
published factory image.
