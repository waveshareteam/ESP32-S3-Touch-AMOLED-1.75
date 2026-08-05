# SD 卡素材制作指南 / SD-Card Media Production Guide

适用固件 / Firmware: ESP32-S3-Touch-AMOLED-1.75 Brookesia

版本日期 / Guide date: 2026-08-05

本文中的参数是按照当前固件的实际解析器、466 × 466 AMOLED 分辨率、SD 读取缓冲和音频链路整理的。不要只修改文件扩展名；容器内部的编码格式也必须匹配。

The settings below follow the current firmware's actual parsers, 466 × 466 AMOLED resolution, SD read buffers, and audio path. Renaming a file extension is not a conversion; the encoded streams inside the file must also match.

---

## 中文说明

### 1. 支持格式速查

| 应用 | 推荐目录 | 固件实际支持 | 推荐制作参数 |
| --- | --- | --- | --- |
| MusicPlayer | `/sdcard/music` | `.mp3`、`.wav`，扩展名大小写不敏感 | WAV：PCM S16LE、24 kHz、双声道；MP3：44.1 kHz、双声道、128 kbit/s |
| Gallery | `/sdcard/photos` | 基线 JPEG，`.jpg` 或 `.jpeg`；最多索引 128 张；单文件最大 4 MiB | 466 × 466、`yuvj420p`、白色留边、非渐进式 JPEG |
| VideoPlayer | `/sdcard/video` | MJPEG AVI；可选 16-bit PCM 音频 | 320 × 240 或 360 × 360、10 fps、MJPG、PCM S16LE 24 kHz 双声道 |
| Recorder | `/sdcard/Waveshare/Recordings` | 由设备自动创建 WAV | PCM S16LE、24 kHz、双声道 |

视频每一帧都必须是可独立解码的基线 JPEG。当前上层 VideoPlayer 没有 H.264 解码器，因此即使某些 AVI 头可以被底层解析，也不能播放 H.264/H.265 视频。AVI 中的 AAC、MP3、ADPCM 等压缩音频也不支持。

### 2. 准备 SD 卡

1. 在电脑上把卡格式化为 FAT 或 FAT32。当前固件不支持 exFAT/NTFS，并且挂载失败时不会自动格式化卡。
2. 将 `SD-Card-Media-260805.zip` 的内容直接解压到卡根目录。
3. 建议使用简单的 ASCII 文件名，并用 `001-`、`002-` 等前缀辅助命名管理。Gallery 和 VideoPlayer 按文件名排序；MusicPlayer 当前按 FAT 目录枚举顺序显示，因此数字前缀不能保证播放顺序。固件已启用 UTF-8 长文件名，但简单命名在 Windows、FAT32 和命令行之间更稳妥。
4. 通过 Windows 安全弹出 SD 卡后，再插入设备。

推荐目录结构：

```text
music/                         MP3/WAV 输入
photos/                        JPG/JPEG 输入
video/                         AVI 输入
Waveshare/Recordings/          Recorder 输出
Waveshare/AIChats/             AIChats 文本历史
Waveshare/Diagnostics/         Settings 导出的诊断文件
```

兼容目录包括 `/Music`、`/Photos`，VideoPlayer 还会依次尝试 `/Video`、`/videos`、`/Videos`、`/avi`、`/AVI`、`/movies`、`/Movies` 和卡根目录。视频扫描在找到第一个含 AVI 的目录后停止，而且不递归子目录，因此不要把同一批 AVI 分散到多个兼容目录。

本文后续 FFmpeg 命令应在已建立这些目录的 SD 卡根目录或本地素材暂存目录中运行。在空目录中开始时，先执行：

```powershell
New-Item -ItemType Directory -Force -Path .\photos, .\music, .\video | Out-Null
```

隐私提示：`Waveshare/AIChats` 下的 JSONL 历史可能包含真实对话文本。共享、返修或重新交付 SD 卡前，请关闭 AIChats 历史记录，并备份或删除这些文件。`Waveshare/Diagnostics` 文件可能包含设备、复位、存储、电池和 Wi-Fi 状态，应审核后再对外分享。

### 3. 安装并检查 FFmpeg

使用包含 `ffmpeg` 和 `ffprobe` 的近期完整构建。安装后先检查：

```powershell
ffmpeg -version
ffprobe -version
ffmpeg -hide_banner -encoders | findstr /I "mjpeg pcm_s16le libmp3lame"
```

如果没有 `libmp3lame`，仍可优先制作 WAV；WAV 不依赖 MP3 编码器。FFmpeg 官方文档中，`fps` 用于输出固定帧率，`scale` 的 `force_original_aspect_ratio=decrease` 用于在目标框内保持比例，`pad` 用于居中补边，`ffprobe` 用于检查容器和流信息：

- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html)
- [FFmpeg AVI muxer](https://ffmpeg.org/ffmpeg-formats.html#avi)
- [ffprobe](https://ffmpeg.org/ffprobe.html)

### 4. 制作 Gallery 图片

Gallery 只扫描 `.jpg`/`.jpeg`，要求 8-bit 基线 JPEG，不接受 Progressive JPEG。单文件不能超过 4 MiB，最多索引 128 张。固件可以把较大图片缩小后解码，但预先转换到屏幕尺寸更省内存、打开更快，也能减少 SD 卡读取时间。

推荐把任何图片等比例缩放并居中到 466 × 466 白底画布：

```powershell
ffmpeg -hide_banner -y -i "input.png" -an -map_metadata -1 -vf "scale=466:466:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=466:466:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 -c:v mjpeg -q:v 2 -pix_fmt yuvj420p -update 1 "photos\001-photo.jpg"
```

说明：

- `force_original_aspect_ratio=decrease` 保持原始宽高比。
- `force_divisible_by=2` 保证 4:2:0 JPEG 的宽高为偶数。
- `pad=466:466:...:white` 把图片居中放到白底方形画布，不裁掉内容。
- `-c:v mjpeg -pix_fmt yuvj420p` 生成兼容性好的基线 JPEG。
- `-q:v 2` 是高质量设置。数值调大，文件通常更小但细节更少。

检查输出：

```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,pix_fmt -of default=noprint_wrappers=1 "photos\001-photo.jpg"
Get-Item "photos\001-photo.jpg" | Select-Object Name,Length
```

预期应看到 `codec_name=mjpeg`、`width=466`、`height=466` 和 `pix_fmt=yuvj420p`，文件应小于 4 MiB。不要通过把 PNG/WebP 改名为 `.jpg` 的方式制作素材。

批量转换当前目录下的 PNG/JPG/JPEG：

```powershell
New-Item -ItemType Directory -Force .\sd\photos | Out-Null
Get-ChildItem .\source-photos -File | Where-Object Extension -Match '^\.(png|jpe?g)$' | ForEach-Object {
    $output = Join-Path .\sd\photos ($_.BaseName + '.jpg')
    ffmpeg -hide_banner -y -i $_.FullName -an -map_metadata -1 -vf "scale=466:466:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=466:466:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 -c:v mjpeg -q:v 2 -pix_fmt yuvj420p -update 1 $output
}
```

### 5. 制作 MusicPlayer 音乐

WAV 是最稳妥的交付格式。推荐转换为 24 kHz、16-bit little-endian PCM、双声道：

```powershell
ffmpeg -hide_banner -y -i "input.flac" -map 0:a:0 -vn -map_metadata -1 -c:a pcm_s16le -ar 24000 -ac 2 "music\001-track.wav"
```

如需减小容量，可制作 MP3：

```powershell
ffmpeg -hide_banner -y -i "input.flac" -map 0:a:0 -vn -map_metadata -1 -c:a libmp3lame -b:a 128k -ar 44100 -ac 2 "music\001-track.mp3"
```

检查输出：

```powershell
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_fmt,sample_rate,channels,bits_per_sample,bit_rate -of default=noprint_wrappers=1 "music\001-track.wav"
```

推荐 WAV 的结果为 `pcm_s16le`、`s16`、`24000` Hz、`2` channels。MusicPlayer 按文件内容识别 MP3/WAV，所以仅修改后缀不能工作。

当前 MusicPlayer UI 使用文件名作为标题，不读取内嵌封面、artist、genre 或准确时长；界面上的这些字段属于演示 UI。现版频谱动画也不是从音频实时分析得到，而会根据所用预置频谱在约 14.8、26.0 或 34.1 秒结束并触发下一首，与真实音频 EOF 无关。为了得到可预测的客户演示效果，建议每段素材不超过 10 秒；本包中的 2–5 秒 WAV 就是用于翻页、上一首/下一首和声道检查的短测试素材。

### 6. 制作 VideoPlayer AVI

#### 最稳妥的 320 × 240 命令

下面的单行命令保留原视频比例、补黑边、固定 10 fps，并只保留第一路视频和可选的第一路音频：

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -vf "fps=10,scale=320:240:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -c:a pcm_s16le -ar 24000 -ac 2 -shortest -write_channel_mask 0 -f avi "video\001-video.avi"
```

这组参数是首选：

- AVI 容器；视频 FourCC 为 `MJPG`。
- 每一帧都是基线 JPEG，像素格式为 `yuvj420p`。
- 320 × 240、恒定 10 fps，适合 466 × 466 QSPI 屏幕和当前解码/刷新预算。
- 音频为 PCM signed 16-bit little-endian、24 kHz、双声道。
- `-map "0:a:0?"` 中的 `?` 表示源文件没有音轨时仍可生成无声 AVI。

#### 方形内容：360 × 360

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -vf "fps=10,scale=360:360:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=360:360:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -c:a pcm_s16le -ar 24000 -ac 2 -shortest -write_channel_mask 0 -f avi "video\001-square.avi"
```

#### 不需要声音

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map_metadata -1 -vf "fps=10,scale=320:240:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -an -f avi "video\001-silent.avi"
```

#### AVI 硬限制和调优

- 每帧宽、高都必须大于 0 且不超过 466；同一文件中不要改变分辨率。
- 屏幕提交硬限制为最高 10 fps。输入 20/25/30/60 fps 只会增加解析和丢帧负担，不会更流畅。
- PCM 音频必须是 16-bit、1 或 2 声道，采样率只能为 8000、12000、16000、24000、32000、44100 或 48000 Hz。
- AVI 头和单个 `movi` 数据块都必须小于 512 KiB。推荐命令在 320 × 240 或 360 × 360 下通常有很大余量。
- `-q:v 5` 是质量与 SD 吞吐的平衡点。如果画面卡顿或文件过大，可改为 `6` 或 `7`；如果细节不足且播放稳定，可改为 `3` 或 `4`。数值越小，通常质量越高、JPEG 帧越大。
- 不要交付 H.264/H.265/MPEG-4 视频，也不要在 AVI 中使用 AAC、MP3、ADPCM 音频、字幕、封面或额外数据流。

检查视频和音频流：

```powershell
ffprobe -v error -show_entries stream=index,codec_type,codec_name,codec_tag_string,profile,width,height,pix_fmt,r_frame_rate,sample_fmt,sample_rate,channels -of default=noprint_wrappers=1 "video\001-video.avi"
```

关键结果应类似：

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

检查最大音视频数据包是否低于 512 KiB：

```powershell
$sizes = ffprobe -v error -show_packets -show_entries packet=size -of csv=p=0 "video\001-video.avi" | ForEach-Object { [int64]$_ }
$sizes | Measure-Object -Maximum
```

`Maximum` 必须小于 `524288`。实际播放仍应在设备上确认声音、画面、上一段/下一段、暂停/继续和退出行为。

### 7. Recorder 输出

Recorder 使用 ES7210 的两路前置麦克风生成 24 kHz、16-bit、双声道 PCM WAV，并保存到 `/sdcard/Waveshare/Recordings`。录音过程中使用临时 `.wav.partial` 文件，每 5 秒更新一次 WAV 头；正常停止后才发布最终 `.wav` 文件。

录音时不要拔卡。卡仍插在设备中时，应先结束录音并退出 Recorder，再在 `Settings > Storage > Safe eject` 中卸载，确认完成后才能物理拔卡。卡在电脑读卡器中时，则在复制完成后使用 Windows 的“弹出”功能。最终 WAV 可以复制到 `/sdcard/music` 交给 MusicPlayer 播放。

如果异常断电后只留下 `.wav.partial`，先备份原文件，再把 44-byte WAV 头之后的原始 PCM 恢复成新文件：

```powershell
ffmpeg -hide_banner -y -skip_initial_bytes 44 -f s16le -ar 24000 -ac 2 -i "REC-xxx.wav.partial" -c:a pcm_s16le "REC-recovered.wav"
```

录音数据率约为 96,000 bytes/s，即约 5.49 MiB/min；请为长时间录音预留足够的 FAT32 空间。

### 8. 常见问题

| 现象 | 优先检查 |
| --- | --- |
| Gallery 显示没有照片 | 目录是否为 `photos`；是否为真正的基线 JPEG；是否超过 4 MiB 或 128 张 |
| 图片被跳过或打开失败 | Progressive JPEG、损坏的 JPEG、尺寸过大或内存不足；用本文命令重新转换 |
| VideoPlayer 只有界面没有画面 | AVI 内不是 MJPEG/MJPG，JPEG 帧不是基线格式，或帧宽高超过 466 |
| 视频无声 | 音轨不是 `pcm_s16le`，不是 16-bit，声道数/采样率不在允许范围，或音频设备正在被其他应用占用 |
| 视频卡顿 | 降到 320 × 240、10 fps，把 `-q:v` 提高到 6–7，并避免细碎噪声、高速运动和超大单帧 |
| MusicPlayer 找不到文件 | 放入 `music`，使用真正的 MP3/WAV；不要只改文件扩展名 |
| SD 卡无法挂载 | 使用 FAT/FAT32，不要使用 exFAT/NTFS；重新插卡后在 Settings 中 Rescan card |

请只使用您有权分发的图片、音乐和视频素材。测试包内的合成素材不包含第三方音乐或影视内容。

---

## English

### 1. Supported-format summary

| Application | Recommended directory | Actual firmware support | Recommended production settings |
| --- | --- | --- | --- |
| MusicPlayer | `/sdcard/music` | `.mp3` and `.wav`, case-insensitive extensions | WAV: PCM S16LE, 24 kHz, stereo; MP3: 44.1 kHz, stereo, 128 kbit/s |
| Gallery | `/sdcard/photos` | Baseline JPEG, `.jpg` or `.jpeg`; up to 128 indexed files; 4 MiB maximum per file | 466 × 466, `yuvj420p`, white padding, non-progressive JPEG |
| VideoPlayer | `/sdcard/video` | MJPEG AVI; optional 16-bit PCM audio | 320 × 240 or 360 × 360, 10 fps, MJPG, PCM S16LE 24 kHz stereo |
| Recorder | `/sdcard/Waveshare/Recordings` | WAV files created by the device | PCM S16LE, 24 kHz, stereo |

Every video frame must be an independently decodable baseline JPEG. The current upper-level VideoPlayer has no H.264 decoder, so H.264/H.265 cannot be displayed even if a lower-level AVI header parser recognizes a related FourCC. AAC, MP3, ADPCM, and other compressed AVI audio formats are also unsupported.

### 2. Prepare the SD card

1. Format the card as FAT or FAT32 on a computer. The firmware does not support exFAT/NTFS and does not automatically format a card after a mount failure.
2. Extract the contents of `SD-Card-Media-260805.zip` directly to the card root.
3. Simple ASCII names with `001-`, `002-`, and similar prefixes are recommended for easier file management. Gallery and VideoPlayer sort by filename. MusicPlayer currently preserves FAT directory enumeration order, so numeric prefixes do not guarantee playback order. UTF-8 long filenames are enabled, but simple names are more portable across Windows, FAT32, and command-line tools.
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

Compatibility directories include `/Music` and `/Photos`. VideoPlayer additionally tries `/Video`, `/videos`, `/Videos`, `/avi`, `/AVI`, `/movies`, `/Movies`, and the card root in that order. Video scanning stops after the first directory that contains AVI files and is not recursive, so do not spread one library across several compatibility directories.

Run the FFmpeg commands below from an SD-card root or local staging directory in which these folders already exist. When starting in an empty directory, run:

```powershell
New-Item -ItemType Directory -Force -Path .\photos, .\music, .\video | Out-Null
```

Privacy notice: JSONL history under `Waveshare/AIChats` may contain real conversation text. Before sharing, servicing, or redelivering an SD card, disable AIChats history and back up or delete those files. Files under `Waveshare/Diagnostics` may contain device, reset, storage, battery, and Wi-Fi state and should be reviewed before external sharing.

### 3. Install and inspect FFmpeg

Use a recent full build containing both `ffmpeg` and `ffprobe`. Check the installation first:

```powershell
ffmpeg -version
ffprobe -version
ffmpeg -hide_banner -encoders | findstr /I "mjpeg pcm_s16le libmp3lame"
```

If `libmp3lame` is unavailable, prefer WAV; WAV creation does not require an MP3 encoder. In the official FFmpeg documentation, `fps` produces a constant output frame rate, `scale` with `force_original_aspect_ratio=decrease` fits content inside a bounding box, `pad` centers it on a fixed canvas, and `ffprobe` reports container and stream properties:

- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html)
- [FFmpeg AVI muxer](https://ffmpeg.org/ffmpeg-formats.html#avi)
- [ffprobe](https://ffmpeg.org/ffprobe.html)

### 4. Create Gallery images

Gallery only scans `.jpg`/`.jpeg` files and requires 8-bit baseline JPEG; Progressive JPEG is rejected. A file may not exceed 4 MiB, and at most 128 photos are indexed. The decoder can scale some larger images, but pre-converting to the panel size reduces memory use, opens faster, and lowers SD traffic.

Fit any source image onto a centered 466 × 466 white canvas:

```powershell
ffmpeg -hide_banner -y -i "input.png" -an -map_metadata -1 -vf "scale=466:466:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=466:466:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 -c:v mjpeg -q:v 2 -pix_fmt yuvj420p -update 1 "photos\001-photo.jpg"
```

Notes:

- `force_original_aspect_ratio=decrease` preserves the source aspect ratio.
- `force_divisible_by=2` produces even dimensions for 4:2:0 JPEG.
- `pad=466:466:...:white` centers the whole image without cropping it.
- `-c:v mjpeg -pix_fmt yuvj420p` produces a broadly compatible baseline JPEG.
- `-q:v 2` is a high-quality setting. Larger values generally reduce size and detail.

Inspect the output:

```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,pix_fmt -of default=noprint_wrappers=1 "photos\001-photo.jpg"
Get-Item "photos\001-photo.jpg" | Select-Object Name,Length
```

Expect `codec_name=mjpeg`, `width=466`, `height=466`, and `pix_fmt=yuvj420p`; the file must remain below 4 MiB. Renaming PNG or WebP to `.jpg` does not convert it.

Batch-convert PNG/JPG/JPEG files:

```powershell
New-Item -ItemType Directory -Force .\sd\photos | Out-Null
Get-ChildItem .\source-photos -File | Where-Object Extension -Match '^\.(png|jpe?g)$' | ForEach-Object {
    $output = Join-Path .\sd\photos ($_.BaseName + '.jpg')
    ffmpeg -hide_banner -y -i $_.FullName -an -map_metadata -1 -vf "scale=466:466:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=466:466:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1" -frames:v 1 -c:v mjpeg -q:v 2 -pix_fmt yuvj420p -update 1 $output
}
```

### 5. Create MusicPlayer audio

WAV is the safest delivery format. Convert to 24 kHz, signed 16-bit little-endian PCM, stereo:

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

The recommended WAV result is `pcm_s16le`, `s16`, `24000` Hz, and `2` channels. MusicPlayer detects MP3/WAV from their contents, so changing only the extension will not work.

The current MusicPlayer UI uses the filename as the title and does not read embedded artwork, artist, genre, or accurate duration; those fields are part of the demonstration UI. Its spectrum is precomputed rather than analyzed from the file and, depending on the preset, ends and advances to the next track after approximately 14.8, 26.0, or 34.1 seconds, independently of the real audio EOF. For predictable customer demonstrations, keep each clip at 10 seconds or less. The packaged 2–5 second WAV files are intentionally short fixtures for list paging, previous/next controls, and channel checks.

### 6. Create VideoPlayer AVI files

#### Safest 320 × 240 recipe

This one-line command preserves aspect ratio, pads with black, forces 10 fps, and retains only the first video stream and optional first audio stream:

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -vf "fps=10,scale=320:240:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -c:a pcm_s16le -ar 24000 -ac 2 -shortest -write_channel_mask 0 -f avi "video\001-video.avi"
```

This is the preferred profile:

- AVI container with `MJPG` video FourCC.
- Every frame is a baseline JPEG using `yuvj420p`.
- Constant 320 × 240 at 10 fps, appropriate for the 466 × 466 QSPI display and current decode/refresh budget.
- PCM signed 16-bit little-endian audio, 24 kHz, stereo.
- The `?` in `-map "0:a:0?"` allows a silent AVI to be created when the source has no audio stream.

#### Square content at 360 × 360

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map "0:a:0?" -map_metadata -1 -vf "fps=10,scale=360:360:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=360:360:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -c:a pcm_s16le -ar 24000 -ac 2 -shortest -write_channel_mask 0 -f avi "video\001-square.avi"
```

#### Silent video

```powershell
ffmpeg -hide_banner -y -i "input.mp4" -map 0:v:0 -map_metadata -1 -vf "fps=10,scale=320:240:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -tag:v MJPG -an -f avi "video\001-silent.avi"
```

#### AVI hard limits and tuning

- Every frame must have non-zero width and height, no larger than 466 × 466, with a constant resolution throughout the file.
- Display submission is capped at 10 fps. Supplying 20/25/30/60 fps only adds parsing and frame-drop load; it does not improve motion.
- PCM audio must be 16-bit with one or two channels, at exactly 8000, 12000, 16000, 24000, 32000, 44100, or 48000 Hz.
- The AVI header and each individual `movi` chunk must fit below 512 KiB. The recommended 320 × 240 and 360 × 360 profiles normally leave ample margin.
- `-q:v 5` balances quality and SD throughput. For stutter or large files, try `6` or `7`; for more detail on a stable clip, try `3` or `4`. Lower values generally produce higher-quality, larger JPEG frames.
- Do not deliver H.264/H.265/MPEG-4 video, AAC/MP3/ADPCM AVI audio, subtitles, cover artwork, or extra data streams.

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

`Maximum` must be less than `524288`. Final acceptance should still test sound, picture, previous/next, pause/resume, and exit on the actual device.

### 7. Recorder output

Recorder captures the two front ES7210 microphones as 24 kHz, 16-bit, stereo PCM WAV under `/sdcard/Waveshare/Recordings`. While recording, it uses a temporary `.wav.partial` file and checkpoints the WAV header every five seconds. The final `.wav` appears only after a synchronized stop.

Do not remove the card during recording. When the card is still installed in the device, stop and leave Recorder, choose `Settings > Storage > Safe eject`, wait for unmount confirmation, and only then remove it physically. When the card is in a PC reader, use Windows Eject after copying. A completed recording can be copied into `/sdcard/music` for MusicPlayer playback.

If an unexpected power loss leaves only a `.wav.partial` file, first back it up, then recover the raw PCM after its 44-byte WAV header into a new file:

```powershell
ffmpeg -hide_banner -y -skip_initial_bytes 44 -f s16le -ar 24000 -ac 2 -i "REC-xxx.wav.partial" -c:a pcm_s16le "REC-recovered.wav"
```

Recording consumes about 96,000 bytes/s, or approximately 5.49 MiB/min. Leave sufficient FAT32 free space for long recordings.

### 8. Troubleshooting

| Symptom | First checks |
| --- | --- |
| Gallery reports no photos | Confirm `photos`, real baseline JPEG, no file above 4 MiB, and no more than 128 indexed files |
| A photo is skipped or fails to open | Progressive/damaged JPEG, excessive dimensions, or memory pressure; reconvert with the command above |
| VideoPlayer shows controls but no picture | The AVI is not MJPEG/MJPG, its frames are not baseline JPEG, or a frame dimension exceeds 466 |
| Video has no sound | Audio is not `pcm_s16le`, not 16-bit, has an unsupported rate/channel count, or another application owns audio |
| Video stutters | Use 320 × 240 at 10 fps, raise `-q:v` to 6–7, and avoid fine noise, very fast motion, and oversized frames |
| MusicPlayer finds no tracks | Use `music` and genuine MP3/WAV content; do not merely rename an extension |
| SD card will not mount | Use FAT/FAT32, not exFAT/NTFS; reinsert it and choose Rescan card in Settings |

Only distribute media for which you have the necessary rights. The synthetic fixtures in the supplied package contain no third-party music or film content.
