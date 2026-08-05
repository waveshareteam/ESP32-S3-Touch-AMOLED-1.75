# ESP32-S3-Touch-AMOLED-1.75 hardware validation

[简体中文](HARDWARE_VALIDATION_ZH.md)

This checklist validates the Brookesia SD-media build on the target board. A
failure is not accepted if it causes a reboot, watchdog, stack overflow, white
screen, partial-screen corruption, leaked SD lease, or audio-owner conflict.

From the repository root, verify the release files and source fixtures before
connecting hardware:

```powershell
& .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline
```

## 1. Prepare deterministic SD media

The customer SD package is `firmware/SD-Card-Media-260805.zip`. The preparation
script reads that archive directly, so a duplicate extracted media directory is
not kept in the repository. To regenerate the project-generated synthetic fixtures into a
temporary working directory, use a Python environment with Pillow:

```powershell
python -m pip install Pillow
$mediaWorkDir = Join-Path $env:TEMP "esp32-s3-touch-amoled-1-75-sd-media"
python firmware\brookesia\tools\generate_sd_test_media.py $mediaWorkDir
```

Insert the SD card into a Windows reader and copy the fixture tree without
formatting or deleting existing files:

```powershell
$sdDrive = 'X:' # Replace with the SD-card drive.
& .\firmware\brookesia\tools\prepare_sd_card.ps1 -Drive $sdDrive
& .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline -SdDrive $sdDrive
```

The script refuses the Windows system drive and, by default, any drive not
reported as removable. Use `-AllowFixedDrive` only after manually confirming
that a fixed-type drive is the SD card. Existing files are retained unless
`-Overwrite` is explicitly supplied. The firmware requires a FAT/FAT32 card;
exFAT is not enabled. The copy script rejects unsupported filesystems and never
formats the card.

Expected card layout:

```text
/music/01-left-440Hz-right-880Hz.wav
/music/02-left-330Hz-right-660Hz.wav
/music/03-left-392Hz-right-784Hz.wav
/music/04-left-523Hz-right-1046Hz.wav
/music/05-left-262Hz-right-524Hz.wav
/music/06-left-659Hz-right-988Hz.wav
/photos/01-wide-color-bars.jpg
/photos/02-square-navigation.jpg
/video/01-mjpeg-320x240-10fps-pcm24k.avi
/Waveshare/Recordings/
/Waveshare/AIChats/
/Waveshare/Diagnostics/
```

## 2. Flash the complete image

The combined image is written at offset `0x0`, not the application offset:

Activate the configured ESP-IDF v5.5.4 environment, connect the board, and run
the full preflight before flashing:

```powershell
$port = 'COMx' # Replace with the board's serial port.
& .\firmware\brookesia\tools\hardware_preflight.ps1 -Port $port
python -m esptool --chip esp32s3 --port $port --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 firmware\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

After flashing, start an ESP-IDF monitor from the configured v5.5.4
environment:

```powershell
$port = 'COMx' # Replace with the board's serial port.
$brookesiaBuildDir = Join-Path $env:TEMP "esp32-s3-touch-amoled-1-75-build-v5.5.4"
idf.py -C firmware\brookesia -B $brookesiaBuildDir -p $port monitor
```

The first boot must reach the launcher without a panic, stack overflow,
watchdog, white screen, or incomplete refresh. Confirm the P4-style loading
screen advances through its initialization stages, reaches `Ready`, and fades
cleanly to the full 466 x 466 Brookesia screen.

## 3. Button Test

1. Open **Button Test** with both keys released. Confirm PWR reports `RAW LOW`
   and BOOT reports `RAW HIGH`; both cards must show `RELEASED` and `WAITING`.
2. Briefly tap PWR without holding it. Confirm only the PWR card changes to
   `RAW HIGH` and `PRESSED`, then returns to `RAW LOW` and `RELEASED` after the
   key is released. `PASS LATCHED` must remain visible.
3. Press BOOT. Confirm only the BOOT card changes to `RAW LOW` and `PRESSED`,
   then returns to `RAW HIGH` and `RELEASED` after release. Its `PASS LATCHED`
   result must remain visible.
4. Confirm the footer changes to `ALL BUTTONS PASSED`. The test must not read an
   AXP2101 button register; PWR is sampled from TCA9554 EXIO4 and BOOT directly
   from GPIO0.
5. Leave and reopen Button Test five times. The launcher must remain responsive,
   each new session must clear both latched results, and no worker task or LVGL
   timer may access a closed application screen.

## 4. Storage and Settings

1. Open **Settings > Storage**.
2. Confirm card name, capacity, free space, 1-bit SDMMC bus, and clock are
   populated.
3. Run the 4 MiB benchmark. It passes only when write/read complete and the
   expected and actual CRC32 match.
4. Export diagnostics and confirm a new text file appears under
   `/Waveshare/Diagnostics`.
5. Enable AI chat history, close Settings, reopen it, and confirm the setting
   persisted.

## 5. Music and shared audio ownership

1. Open **MusicPlayer** and confirm all six stereo WAV tracks are indexed.
2. Confirm previous, play/pause, and next buttons are visible and responsive on
   the round 466 x 466 layout.
3. Navigate from track 5 to track 6 and back to exercise the second list page.
4. Play track 1 and listen for 440 Hz on the left channel and 880 Hz on the
   right channel.
5. Pause, leave the app, reopen it, and repeat rapid enter/exit five times.
6. Switch in sequence between MusicPlayer, SpecAnalyzer, Recorder, VideoPlayer,
   and AIChats. Each app must either acquire audio or report it busy; none may
   reboot or steal the ES8311/ES7210 session from another owner.

## 6. Gallery

1. Open **Gallery** and confirm both baseline JPEG fixtures are indexed.
2. Exercise previous, next, and slideshow controls.
3. Confirm wide and square photos are centered without stale pixels or partial
   refresh regions.
4. Close Gallery while a photo is loading, then reopen it five times.
5. Temporarily rename `/photos`, reopen Gallery, and confirm the error page does
   not keep the SD lease busy; Settings safe eject must still succeed.

## 7. Recorder

1. Record at least ten seconds while speaking near each microphone in turn.
2. Stop normally and confirm a WAV file appears under
   `/Waveshare/Recordings`.
3. Play the file on a PC and confirm it is 24 kHz, 16-bit, stereo and that both
   ES7210 microphone channels contain audio.
4. Repeat start/stop five times and close the app during an active recording.
   The output must remain a readable WAV rather than a zero-length file.

## 8. VideoPlayer

1. Play `01-mjpeg-320x240-10fps-pcm24k.avi`.
2. Confirm the moving white square advances smoothly at the intentional 10 fps
   cap and PCM audio is audible.
3. Exercise pause, previous, next, natural end, immediate back, and reopen.
4. Repeat immediate enter/back ten times. No AVI callback may touch a released
   canvas, frame buffer, file, codec, or SD lease.

## 9. Safe eject, reinsertion, and history

1. While MusicPlayer or VideoPlayer owns an open file, **Safe eject** must
   report busy and leave the card mounted.
2. Close the media app and retry. Safe eject must unmount successfully.
3. Remove and reinsert the card, choose rescan, and confirm all fixtures return.
4. Use AIChats for one text exchange, close the app, and confirm a JSONL record
   under `/Waveshare/AIChats` when history is enabled. Disable history and
   confirm later exchanges are not appended.
5. With every writer stopped, remove the card without Safe eject, reinsert it,
   and open Gallery directly without visiting Settings. The first new storage
   lease must detect the stale mount and recover automatically.

If Recorder ever reports a save failure after capturing audio, inspect the
corresponding `.wav.partial` file on a PC. Its header is checkpointed every five
seconds so an interrupted recording is not published as a successful `.wav`.

## 10. Final soak gate

Cycle through all launcher applications at least twenty times while monitoring
serial output. The release passes only with no panic, watchdog, stack overflow,
heap assertion, invalid state loop, SD lease left busy after app close, or
cross-owner audio release error. Record the final firmware SHA256, SD card
identity, benchmark result, battery reading, Wi-Fi RSSI, and serial log with the
test result.
