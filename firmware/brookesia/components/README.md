# Brookesia firmware components

[简体中文](README_ZH.md)

This directory contains product applications, shared services, board-local
integration, and deliberately pinned safety overrides for the
ESP32-S3-Touch-AMOLED-1.75 firmware. It is not a collection of interchangeable
upstream libraries: each category below has a different maintenance boundary.

The Brookesia core and SquareLine demo are reused from
`examples/esp-idf/03_esp-brookesia/components/` through `EXTRA_COMPONENT_DIRS`
in the project `CMakeLists.txt`; they are intentionally not duplicated here.

## Applications

| Directory | Launcher application |
| --- | --- |
| [`brookesia_app_calculator/`](brookesia_app_calculator/) | Calculator |
| [`ButtonTest/`](ButtonTest/) | Direct PWR/EXIO4 and BOOT/GPIO0 level test |
| [`Crosshair/`](Crosshair/) | Circular display and touch alignment target |
| [`draw/`](draw/) | DrawPanel |
| [`Gallery/`](Gallery/) | SD-card JPEG gallery |
| [`Gravitysphere/`](Gravitysphere/) | QMI8658-driven gravity ball |
| [`MusicPlayer/`](MusicPlayer/) | MP3/WAV playback from SD card or SPIFFS |
| [`Recorder/`](Recorder/) | ES7210 stereo WAV recording to SD card |
| [`Settings/`](Settings/) | Wi-Fi, battery, display, audio, storage, and diagnostics |
| [`SpecAnalyzer/`](SpecAnalyzer/) | Live ES7210 microphone spectrum analyzer |
| [`VideoPlayer/`](VideoPlayer/) | MJPEG/PCM AVI playback from SD card |
| [`XiaozhiApp/`](XiaozhiApp/) | AIChats voice and text application |

## Shared product services

| Directory | Responsibility |
| --- | --- |
| [`bsp_extra/`](bsp_extra/) | Board-local ES8311/ES7210 audio integration, PA diagnostics, file playback, and exclusive audio-session ownership |
| [`chat_history/`](chat_history/) | Optional text-only AIChats JSONL history |
| [`storage_service/`](storage_service/) | Shared SD mount leases, card recovery, diagnostics, and safe eject |
| [`system_status/`](system_status/) | Resident AXP2101 battery and native Wi-Fi status used by the status bar and Settings |

These services coordinate hardware or persistent state across applications.
Applications must use their public APIs instead of opening a second codec,
mounting the SD card independently, or maintaining a separate Wi-Fi/battery
state model.

## Local safety overrides

| Directory | Upstream base and local boundary |
| --- | --- |
| [`avi_player_safe/`](avi_player_safe/) | Espressif `avi_player` 2.0.0 with checked file parsing and deterministic stop/deinit cleanup |
| [`esp_audio_player_safe/`](esp_audio_player_safe/) | `chmorgan/esp-audio-player` 1.1.0 with deterministic worker and queued-file cleanup |
| [`esp_xiaozhi_safe/`](esp_xiaozhi_safe/) | Espressif `esp_xiaozhi` 0.1.1 with bounded network and event-queue waits |

Each override preserves the selected upstream component's public version and
API while addressing a firmware lifecycle hazard. Keep the override manifest,
source, wrapper README, and the consuming component's `override_path` in sync.
Do not silently replace an override with a registry download until its local
behavior has been verified upstream or is no longer required.

## Managed BSP and third-party code

`waveshare__esp32_s3_touch_amoled_1_75/` is the resolved Waveshare managed BSP
used by this source snapshot. Its manifest and upstream README belong to the
managed component boundary. Board-specific behavior required only by this
firmware belongs in `bsp_extra/`, or in the shared Waveshare component
repository when it is generally reusable.

Code nested under an upstream component or an explicit `third_party/`
directory retains its upstream license, attribution, README, and naming.
Product documentation should link to that material, not rewrite it as if the
firmware project owned the upstream component. Optional media and prompt assets
must also be reviewed under their own licenses before distribution.

## Validation

After changing an application or shared service, build the complete project and
repeat the relevant target-board sections in
[`../HARDWARE_VALIDATION.md`](../HARDWARE_VALIDATION.md). Changes to audio,
storage, or lifecycle cleanup must also exercise rapid enter/exit and
cross-application switching, because a successful build does not validate
resource ownership on hardware.
