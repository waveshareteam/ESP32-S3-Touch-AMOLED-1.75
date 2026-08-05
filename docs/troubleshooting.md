# Troubleshooting

[简体中文](troubleshooting_ZH.md) | **English**

Start with the exact board model, firmware filename or source revision, framework version, and the
first operation that fails. Change one variable at a time. Use firmware, partitions, and settings for
ESP32-S3-Touch-AMOLED-1.75; similarly named boards are not binary compatible.

## Board Does Not Enter Download Mode

- Confirm that the USB cable carries data and that the USB power source is stable.
- Close other serial monitors or applications that own the selected port.
- Confirm the port disappears and returns when the board is disconnected and reconnected.
- If automatic reset fails, hold BOOT, tap RESET, start the flash command, and release BOOT when
  writing begins.
- Reduce the flashing baud rate if writes fail at changing offsets or with packet/time-out errors.

Do not diagnose a port problem by repeatedly erasing flash; download mode is available independently
of the application stored in flash.

## Flash Layout, 16 MB Header, and Complete Images

An error similar to the following means the detected flash size and image header do not agree:

```text
Detected size(16384k) smaller than the size in the binary image header(32768k)
```

Use a package for this board's 16 MB flash layout. Do not combine a bootloader, partition table,
application, ESP-SR model, or filesystem from different artifacts. Prefer the packaged
`*-combined.bin` at `0x0`; the factory image is a complete 16 MiB image and must also be written at
`0x0`.

Erasing the entire flash is not a routine first step. Consider it only when a known incompatible old
partition table or 32 MB image remains after the correct complete image has been selected. The
following operation deletes all flash-resident settings and content, so back up anything required and
confirm the target port before running it:

```bash
python -m esptool --chip esp32s3 --port PORT erase_flash
```

After an exceptional full erase, immediately flash one complete, matching combined image. Do not boot
with only an application binary present.

## Boot Loops, Watchdogs, or Stack Overflows

1. Confirm the board is powered from a stable source and disconnect optional expansion hardware.
2. Reflash the matching complete image at `0x0`.
3. Capture the boot banner and the first panic, watchdog message, or backtrace. Later repetitions of
   the same reset usually add no new information.
4. For source builds, confirm the documented ESP-IDF version, the project's `sdkconfig.defaults`, and
   its partition table. Keep `sdkconfig.defaults.v6` enabled for the ESP-Brookesia example on ESP-IDF
   v6.

Do not replace individual Brookesia, LVGL, BSP, or audio components with copies from another board.
Display locks, task stacks, audio ownership, and memory configuration are board/project-specific.

## Blank, White, Partially Updated, or Corrupted Display

- Confirm the firmware targets the 466 × 466 CO5300 QSPI AMOLED on this exact board.
- Reset once after flashing and use a stable USB power source.
- Flash the entire combined image instead of only the application binary.
- Do not mix display initialization, LVGL configuration, cache/flush callbacks, or BSP files from a
  different display or framework build.
- Compare with `02_lvgl_demo_v9`. If that example is correct but Brookesia is not, record which boot
  stage or application first introduces stale/blank regions.
- If only touched regions update or old pixels remain, capture one photo of the whole circular panel
  and the first related display/LVGL error. Repeated taps can hide the original refresh boundary.

This AMOLED has no conventional GPIO-controlled LCD backlight. A completely white or blank image is
therefore not normally corrected by toggling a backlight pin; check panel initialization, the complete
image, power stability, and the display flush path instead.

## Touch Is Missing, Offset, or Intermittent

- Run `10_Touch_CST9217` and confirm that touch interrupts produce raw coordinates. This diagnostic
  intentionally does not initialize the display or LVGL.
- Remove water, protective-film bubbles, or conductive objects from the panel and test one finger,
  then two fingers.
- If the raw diagnostic works but an LVGL application does not, keep the shipped rotation and touch
  transform together; do not change only one axis, swap, or mirror setting.
- If no raw events appear, check the CST9217 reset/interrupt path and shared I2C bus before changing UI
  code.

When reporting an offset, identify the touched landmark and the reported point; a general statement
such as “touch is wrong” is not sufficient to distinguish rotation, scaling, and missed interrupts.

## Brookesia Loading or Launcher Startup

The factory firmware displays a staged loading screen while the board, storage, audio, status
services, and applications initialize. It should reach `Ready` and transition to the complete
466 × 466 launcher without a panic, white screen, or partially refreshed frame.

If it stops at a stage, record that stage and the immediately related serial output. On a first
AIChats installation, ensure the partition table, application, `srmodels.bin`, and `storage.bin` all
come from the same build; the supplied factory image already combines them. For source builds, keep
the synchronized local Brookesia snapshot and dependency configuration instead of updating one
component in isolation.

## Battery, Charging, Status Bar, or Wi-Fi State

The battery icon and percentage are driven by the AXP2101 fuel gauge and charging state. The Wi-Fi
icon represents the actual station connection and RSSI, not merely whether the Wi-Fi switch is on.

- With no battery connected, do not expect a normal battery percentage. Connect the intended battery
  and allow the gauge to settle after boot.
- If battery, VBUS, temperature, or charging fields remain unavailable, compare with
  `01_AXP2101` or `05_LVGL_AXP2101_ADC_Data` before changing Settings.
- If Wi-Fi is enabled but the icon remains disconnected, verify a reachable 2.4 GHz access point,
  reconnect from Settings, and wait for association and IP acquisition.
- If Settings closes but Wi-Fi should remain enabled, reboot once and check that the persisted switch
  and saved network reconnect. The resident Wi-Fi service is designed to operate outside the
  Settings page.
- For an incorrect icon, compare the Settings detail (charging state or RSSI) with the status bar at
  the same time. Report both observations rather than a screenshot of only one widget.

Do not publish Wi-Fi credentials or an unredacted scan list when asking for help.

## AIChats Shows “Service unavailable”

“Service unavailable” can originate from network reachability, activation/account state, or the
remote Xiaozhi service; it does not by itself prove an ES8311/ES7210 hardware fault.

1. Confirm the status bar and Settings show an actual Wi-Fi connection, not only an enabled switch.
2. Confirm the device completed the required activation flow and that the configured remote service
   is currently available.
3. Close MusicPlayer, VideoPlayer, SpecAnalyzer, and Recorder before testing voice input/output so
   AIChats can acquire the shared audio service.
4. If WakeNet/model initialization fails, install the complete matching factory image; do not flash
   only the application when `srmodels.bin` or storage content may be missing.
5. Separate transport failures from audio failures: a remote-service response with no sound points to
   playback/volume; no connection attempt points to Wi-Fi or activation; no microphone activity points
   to audio ownership or capture initialization.

Redact activation codes, tokens, account identifiers, conversation text, and voice recordings from
all reports.

## MusicPlayer, ES8311, Speaker, or PA Has No Sound

- Put genuine MP3/WAV files under `/sdcard/music` (or `/sdcard/Music` for compatibility); changing a
  filename extension does not convert its contents.
- Confirm the player lists the file, the play/pause state changes, volume is above zero, and an
  external speaker is connected correctly.
- Close VideoPlayer and AIChats before retesting. Only one application may own the shared speaker
  path at a time.
- The board playback path uses ES8311 and the PA-enable signal on GPIO46. The BSP audio service should
  configure both; do not permanently force the PA on or bypass its ownership/lifecycle handling.
- Compare with Arduino `08_ES8311`. If that example works, preserve its board-specific I2S/codec path
  when diagnosing the factory application.
- If opening the app causes a reset, collect the first panic/backtrace and the log lines immediately
  before it. Do not treat silence, an audio-busy message, and a reboot as the same failure.

For predictable validation, use the WAV profile and test fixtures documented in the
[SD-card Media Guide](../firmware/MEDIA_GUIDE.md).

## SpecAnalyzer, Recorder, ES7210, or Microphones Fail

- Close MusicPlayer, VideoPlayer, and AIChats so the capture path is not owned by another app.
- SpecAnalyzer and Recorder use the two onboard microphones through ES7210. Speak near each
  microphone in turn to distinguish a channel issue from an overall capture failure.
- Recorder output should be 24 kHz, 16-bit stereo WAV under
  `/sdcard/Waveshare/Recordings`. Stop recording normally and wait for the synchronized close before
  removing the card.
- A `.wav.partial` file can remain after interrupted power or removal. Back it up and follow the
  recovery command in the media guide; do not rename it directly to `.wav` and assume the header is
  final.
- If the spectrum remains flat and recordings contain silence, inspect ES7210 initialization and
  audio-owner messages before changing FFT or UI code.
- If an app reports audio busy, close the current owner. It should not steal or release another
  application's audio session.

## microSD, Gallery, VideoPlayer, or AVI Problems

- Use FAT or FAT32. The current firmware does not support exFAT or NTFS and does not auto-format a
  card after mount failure.
- Open **Settings > Storage** to check capacity/free space, run the CRC benchmark, rescan after
  reinsertion, and use **Safe eject** before physical removal.
- Gallery scans baseline `.jpg`/`.jpeg` under `/sdcard/photos`, indexes at most 128 files, and rejects
  files larger than 4 MiB. Progressive JPEG is not supported.
- VideoPlayer expects MJPEG (`MJPG`) AVI under `/sdcard/video`. Use 320 × 240 or 360 × 360 at 10 fps;
  optional audio must be 16-bit PCM with a supported rate and one or two channels. H.264/H.265 video
  and AAC/MP3/ADPCM AVI audio are not supported.
- If video controls appear without a picture, inspect the streams with `ffprobe`; renaming an MP4 to
  `.avi` is not a conversion.
- If playback stutters, use 320 × 240 at 10 fps, reduce per-frame JPEG size, and test with the supplied
  synthetic AVI before blaming the card or display.

See the [SD-card Media Guide](../firmware/MEDIA_GUIDE.md) for exact directories, FFmpeg recipes,
`ffprobe` checks, safe-eject behavior, and Recorder recovery.

## Arduino Core, Board, or Library Conflicts

- Use Arduino-ESP32 `3.3.10`, ESP32-S3, 16 MB flash, and the
  `app3M_fat9M_16MB` partition scheme.
- Use the bundled libraries under `examples/arduino/libraries`. Remove duplicate global copies or
  ensure the bundled path takes precedence.
- Read the compiler's “Multiple libraries were found” output and confirm the selected path before
  changing source code.
- Do not combine pin definitions or display/audio libraries from a similarly named Waveshare board.
- Build one unchanged repository example first. If it succeeds, reintroduce local changes in small
  groups.

## Request Support with Minimal, Redacted Evidence

Follow [SUPPORT.md](../SUPPORT.md) and include only the evidence needed to reproduce the first
failure:

- Exact board variant and any connected expansion hardware.
- Firmware filename or commit revision, framework/tool version, and flash method.
- Short reproduction steps, expected behavior, and actual behavior.
- The boot banner plus the smallest log excerpt from the last normal stage through the first error or
  backtrace.
- One cropped photo when a display or connection-state mismatch cannot be described clearly.

Before sharing, redact SSIDs, passwords, IP and MAC addresses, device IDs, UUIDs, activation codes,
tokens, account identifiers, conversation text, recording contents/filenames, customer data, and local
usernames or filesystem paths. Do not upload a complete serial log, Wi-Fi scan, diagnostics export,
SD-card image, or screenshot when a smaller sanitized excerpt demonstrates the problem.
