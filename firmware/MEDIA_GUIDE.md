# SD-Card Media Production Guide

[简体中文](MEDIA_GUIDE_ZH.md)

Applicable firmware: ESP32-S3-Touch-AMOLED-1.75 Brookesia

Guide date: 2026-08-05

The settings below follow the current firmware's actual parsers, 466 × 466
AMOLED resolution, SD read buffers, and audio path. Renaming a file extension
is not a conversion; the encoded streams inside the file must also match.

## 1. Supported-format summary

| Application | Recommended directory | Actual firmware support | Recommended production settings |
| --- | --- | --- | --- |
| MusicPlayer | `/sdcard/music` | `.mp3` and `.wav`, case-insensitive extensions | WAV: PCM S16LE, 24 kHz, stereo; MP3: 44.1 kHz, stereo, 128 kbit/s |
| Gallery | `/sdcard/photos` | Baseline JPEG, `.jpg` or `.jpeg`; up to 128 indexed files; 4 MiB maximum per file | 466 × 466, `yuvj420p`, white padding, non-progressive JPEG |
| VideoPlayer | `/sdcard/video` | MJPEG AVI; optional 16-bit PCM audio | 320 × 240 or 360 × 360, 10 fps, MJPG, PCM S16LE 24 kHz stereo |
| Recorder | `/sdcard/Waveshare/Recordings` | WAV files created by the device | PCM S16LE, 24 kHz, stereo |

Every video frame must be an independently decodable baseline JPEG. The current
upper-level VideoPlayer has no H.264 decoder, so H.264/H.265 cannot be displayed
even if a lower-level AVI header parser recognizes a related FourCC. AAC, MP3,
ADPCM, and other compressed AVI audio formats are also unsupported.

## 2. Prepare the SD card

1. Format the card as FAT or FAT32 on a computer. The firmware does not support
   exFAT/NTFS and does not automatically format a card after a mount failure.
2. Extract `SD-Card-Media-260805.zip` directly to the card root.
3. Simple ASCII names with `001-`, `002-`, and similar prefixes are
   recommended. Gallery and VideoPlayer sort by filename. MusicPlayer currently
   preserves FAT directory enumeration order, so numeric prefixes do not
   guarantee playback order. UTF-8 long filenames are enabled, but simple
   names are more portable across Windows, FAT32, and command-line tools.
4. Eject the SD card safely through Windows before inserting it into the device.

Recommended layout:

```text
music/                         MP3/WAV input
photos/                        JPG/JPEG input
video/                         AVI input
Waveshare/Recordings/          Recorder output
Waveshare/AIChats/             AIChats text history
Waveshare/Diagnostics/         Diagnostic exports from Settings
```

Compatibility directories include `/Music` and `/Photos`. VideoPlayer
additionally tries `/Video`, `/videos`, `/Videos`, `/avi`, `/AVI`,
`/movies`, `/Movies`, and the card root in that order. Video scanning stops
after the first directory that contains AVI files and is not recursive, so do
not spread one library across several compatibility directories.

Run the FFmpeg commands below from an SD-card root or local staging directory
where these folders already exist. When starting in an empty directory, run:

```powershell
New-Item -ItemType Directory -Force -Path .\photos, .\music, .\video | Out-Null
```

> [!IMPORTANT]
> JSONL history under `Waveshare/AIChats` may contain real conversation text.
> Before sharing, servicing, or redelivering an SD card, disable AIChats history
> and back up or delete those files. Files under `Waveshare/Diagnostics` may
> contain device, reset, storage, battery, and Wi-Fi state and should be
> reviewed before external sharing.

## 3. Install and inspect FFmpeg

Use a recent full build containing both `ffmpeg` and `ffprobe`. Check the
installation first:

```powershell
ffmpeg -version
ffprobe -version
ffmpeg -hide_banner -encoders | findstr /I "mjpeg pcm_s16le libmp3lame"
```

If `libmp3lame` is unavailable, prefer WAV; WAV creation does not require an
MP3 encoder. In the official FFmpeg documentation, `fps` produces a constant
output frame rate, `scale` with `force_original_aspect_ratio=decrease` fits
content inside a bounding box, `pad` centers it on a fixed canvas, and
`ffprobe` reports container and stream properties:

- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html)
- [FFmpeg AVI muxer](https://ffmpeg.org/ffmpeg-formats.html#avi)
- [ffprobe](https://ffmpeg.org/ffprobe.html)

## 4. Create Gallery images

Gallery only scans `.jpg`/`.jpeg` files and requires 8-bit baseline JPEG;
Progressive JPEG is rejected. A file may not exceed 4 MiB, and at most 128
photos are indexed. The decoder can scale some larger images, but pre-converting
to the panel size reduces memory use, opens faster, and lowers SD traffic.

Fit any source image onto a centered 466 × 466 white canvas:

```powershell
ffmpeg -hide_banner -y -i "input.png" -an -map_metadata -1 -vf "scale=466:466:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=466:466:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 -c:v mjpeg -q:v 2 -pix_fmt yuvj420p -update 1 "photos\001-photo.jpg"
```

Notes:

- `force_original_aspect_ratio=decrease` preserves the source aspect ratio.
- `force_divisible_by=2` produces even dimensions for 4:2:0 JPEG.
- `pad=466:466:...:white` centers the whole image without cropping it.
- `-c:v mjpeg -pix_fmt yuvj420p` produces a broadly compatible baseline JPEG.
- `-q:v 2` is a high-quality setting. Larger values generally reduce size and
  detail.

Inspect the output:

```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,pix_fmt -of default=noprint_wrappers=1 "photos\001-photo.jpg"
Get-Item "photos\001-photo.jpg" | Select-Object Name,Length
```

Expect `codec_name=mjpeg`, `width=466`, `height=466`, and
`pix_fmt=yuvj420p`; the file must remain below 4 MiB. Renaming PNG or WebP to
`.jpg` does not convert it.

Batch-convert PNG/JPG/JPEG files:

```powershell
New-Item -ItemType Directory -Force .\sd\photos | Out-Null
Get-ChildItem .\source-photos -File | Where-Object Extension -Match '^\.(png|jpe?g)$' | ForEach-Object {
    $output = Join-Path .\sd\photos ($_.BaseName + '.jpg')
    ffmpeg -hide_banner -y -i $_.FullName -an -map_metadata -1 -vf "scale=466:466:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=466:466:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 -c:v mjpeg -q:v 2 -pix_fmt yuvj420p -update 1 $output
}
```

## 5. Create MusicPlayer audio

WAV is the safest delivery format. Convert to 24 kHz, signed 16-bit
little-endian PCM, stereo:

```powershell
ffmpeg -hide_banner -y -i "input.flac" -map 0:a:0 -vn -map_metadata -1 -c:a pcm_s16le -ar 24000 -ac 2 "music\001-track.wav"
```

To reduce storage use, create MP3 instead:

```powershell
ffmpeg -hide_banner -y -i "input.flac" -map 0:a:0 -vn -map_metadata -1 -c:a libmp3lame -b:a 128k -ar 44100 -ac 2 "music\001-track.mp3"
```

Inspect the output:

```powershell
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_fmt,sample_rate,channels,bits_per_sample,bit_rate -of default=noprint_wrappers=1 "music\001-track.wav"
```

The recommended WAV result is `pcm_s16le`, `s16`, `24000` Hz, and
`2` channels. MusicPlayer detects MP3/WAV from their contents, so changing
only the extension will not work.

The current MusicPlayer UI uses the filename as the title and does not read
embedded artwork, artist, genre, or accurate duration; those fields are part of
the demonstration UI. Its spectrum is precomputed rather than analyzed from
the file and, depending on the preset, ends and advances after approximately
14.8, 26.0, or 34.1 seconds, independently of the real audio EOF. For
predictable customer demonstrations, keep each clip at 10 seconds or less. The
packaged 2–5 second WAV files are intentionally short fixtures for list paging,
previous/next controls, and channel checks.

## 6. Create VideoPlayer AVI files

### Safest 320 × 240 recipe

This one-line command preserves aspect ratio, pads with black, forces 10 fps,
and retains only the first video stream and optional first audio stream:

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -vf "fps=10,scale=320:240:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -c:a pcm_s16le -ar 24000 -ac 2 -shortest -write_channel_mask 0 -f avi "video\001-video.avi"
```

This is the preferred profile:

- AVI container with `MJPG` video FourCC.
- Every frame is a baseline JPEG using `yuvj420p`.
- Constant 320 × 240 at 10 fps, appropriate for the 466 × 466 QSPI display and
  current decode/refresh budget.
- PCM signed 16-bit little-endian audio, 24 kHz, stereo.
- The `?` in `-map "0:a:0?"` allows a silent AVI to be created when the
  source has no audio stream.

### Square content at 360 × 360

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -vf "fps=10,scale=360:360:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=360:360:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -c:a pcm_s16le -ar 24000 -ac 2 -shortest -write_channel_mask 0 -f avi "video\001-square.avi"
```

### Silent video

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map_metadata -1 -vf "fps=10,scale=320:240:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -an -f avi "video\001-silent.avi"
```

### AVI hard limits and tuning

- Every frame must have non-zero width and height, no larger than 466 × 466,
  with a constant resolution throughout the file.
- Display submission is capped at 10 fps. Supplying 20/25/30/60 fps only adds
  parsing and frame-drop load; it does not improve motion.
- PCM audio must be 16-bit with one or two channels, at exactly 8000, 12000,
  16000, 24000, 32000, 44100, or 48000 Hz.
- The AVI header and each individual `movi` chunk must fit below 512 KiB. The
  recommended 320 × 240 and 360 × 360 profiles normally leave ample margin.
- `-q:v 5` balances quality and SD throughput. For stutter or large files,
  try `6` or `7`; for more detail on a stable clip, try `3` or `4`.
  Lower values generally produce higher-quality, larger JPEG frames.
- Do not deliver H.264/H.265/MPEG-4 video, AAC/MP3/ADPCM AVI audio, subtitles,
  cover artwork, or extra data streams.

Inspect both streams:

```powershell
ffprobe -v error -show_entries stream=index,codec_type,codec_name,codec_tag_string,profile,width,height,pix_fmt,r_frame_rate,sample_fmt,sample_rate,channels -of default=noprint_wrappers=1 "video\001-video.avi"
```

Expected key fields resemble:

```text
codec_type=video
codec_name=mjpeg
codec_tag_string=MJPG
width=320
height=240
pix_fmt=yuvj420p
r_frame_rate=10/1
codec_type=audio
codec_name=pcm_s16le
sample_fmt=s16
sample_rate=24000
channels=2
```

Check that the largest media packet remains below 512 KiB:

```powershell
$sizes = ffprobe -v error -show_packets -show_entries packet=size -of csv=p=0 "video\001-video.avi" | ForEach-Object { [int64]$_ }
$sizes | Measure-Object -Maximum
```

`Maximum` must be less than `524288`. Final acceptance should still test
sound, picture, previous/next, pause/resume, and exit on the actual device.

## 7. Recorder output

Recorder captures the two front ES7210 microphones as 24 kHz, 16-bit, stereo
PCM WAV under `/sdcard/Waveshare/Recordings`. While recording, it uses a
temporary `.wav.partial` file and checkpoints the WAV header every five
seconds. The final `.wav` appears only after a synchronized stop.

Do not remove the card during recording. When the card is still installed in
the device, stop and leave Recorder, choose
`Settings > Storage > Safe eject`, wait for unmount confirmation, and only
then remove it physically. When the card is in a PC reader, use Windows Eject
after copying. A completed recording can be copied into `/sdcard/music` for
MusicPlayer playback.

If an unexpected power loss leaves only a `.wav.partial` file, first back it
up, then recover the raw PCM after its 44-byte WAV header into a new file:

```powershell
ffmpeg -hide_banner -y -skip_initial_bytes 44 -f s16le -ar 24000 -ac 2 -i "REC-xxx.wav.partial" -c:a pcm_s16le "REC-recovered.wav"
```

Recording consumes about 96,000 bytes/s, or approximately 5.49 MiB/min. Leave
sufficient FAT32 free space for long recordings.

## 8. Troubleshooting

| Symptom | First checks |
| --- | --- |
| Gallery reports no photos | Confirm `photos`, real baseline JPEG, no file above 4 MiB, and no more than 128 indexed files |
| A photo is skipped or fails to open | Progressive/damaged JPEG, excessive dimensions, or memory pressure; reconvert with the command above |
| VideoPlayer shows controls but no picture | The AVI is not MJPEG/MJPG, its frames are not baseline JPEG, or a frame dimension exceeds 466 |
| Video has no sound | Audio is not `pcm_s16le`, not 16-bit, has an unsupported rate/channel count, or another application owns audio |
| Video stutters | Use 320 × 240 at 10 fps, raise `-q:v` to 6–7, and avoid fine noise, very fast motion, and oversized frames |
| MusicPlayer finds no tracks | Use `music` and genuine MP3/WAV content; do not merely rename an extension |
| SD card will not mount | Use FAT/FAT32, not exFAT/NTFS; reinsert it and choose Rescan card in Settings |

Only distribute media for which you have the necessary rights. The synthetic
fixtures in the supplied package contain no third-party music or film content.
