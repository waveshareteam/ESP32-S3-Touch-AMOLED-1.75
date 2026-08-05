Waveshare ESP32-S3-Touch-AMOLED-1.75 SD card package
Waveshare ESP32-S3-Touch-AMOLED-1.75 SD 卡素材包

中文
====

1. 本卡必须使用 FAT 或 FAT32；不要使用 exFAT/NTFS。
2. 将本 ZIP 的“内容”复制到 SD 卡根目录，不要再套一层目录。
3. 推荐目录和格式：
   music       MP3 或 PCM WAV；最稳妥为 24 kHz、16-bit、双声道 WAV
   photos      基线 JPG/JPEG；最多 128 张、单文件不超过 4 MiB
   video       MJPEG AVI；推荐 320x240 或 360x360、10 fps、PCM S16LE 24 kHz 双声道
   Waveshare/Recordings   Recorder 自动保存的 24 kHz、16-bit、双声道 WAV
   Waveshare/AIChats      可选的纯文本聊天历史
   Waveshare/Diagnostics  Settings 导出的诊断文件
4. media_manifest.json 记录 9 个测试素材的大小和 SHA-256。
5. 完整的 FFmpeg 制作、ffprobe 校验、Recorder partial 恢复和故障排查命令见 MEDIA_GUIDE.md。
6. 卡在电脑读卡器中时，复制完成后请通过 Windows 安全弹出。卡仍插在设备中时，拔卡前必须先退出媒体应用，并在 Settings > Storage > Safe eject 中卸载。
7. AIChats 历史可能包含真实对话文本。共享、返修或重新交付 SD 卡前，请关闭历史记录，并备份或删除 Waveshare/AIChats 下的 JSONL 文件；Diagnostics 文件也应审核后再分享。

包内素材说明：music 中有 6 个双声道音调 WAV，用于列表翻页、上一首/下一首和左右声道测试；photos 中有宽屏和方形基线 JPEG；video 中有 320x240、10 fps、MJPEG + 24 kHz PCM 的 AVI。

English / 英文
--------------

1. The card must use FAT or FAT32; do not use exFAT or NTFS.
2. Copy the contents of this ZIP directly to the SD-card root. Do not add another package directory.
3. Recommended directories and formats:
   music       MP3 or PCM WAV; 24 kHz, 16-bit, stereo WAV is the safest profile
   photos      Baseline JPG/JPEG; at most 128 indexed files and 4 MiB per file
   video       MJPEG AVI; 320x240 or 360x360 at 10 fps with PCM S16LE 24 kHz stereo is recommended
   Waveshare/Recordings   24 kHz, 16-bit, stereo WAV created by Recorder
   Waveshare/AIChats      Optional text-only chat history
   Waveshare/Diagnostics  Diagnostic files exported from Settings
4. media_manifest.json records the size and SHA-256 of all nine validation fixtures.
5. See MEDIA_GUIDE.md for complete FFmpeg creation, ffprobe validation, Recorder partial recovery, and troubleshooting commands.
6. When the card is in a PC reader, eject it through Windows after copying. When it is still in the device, leave all media applications and choose Settings > Storage > Safe eject before physical removal.
7. AIChats history may contain real conversation text. Before sharing, servicing, or redelivering the SD card, disable history and back up or delete JSONL files under Waveshare/AIChats; review Diagnostics files before sharing them as well.

Package contents: music contains six stereo tone WAV files for list paging, previous/next, and channel tests; photos contains wide and square baseline JPEG fixtures; video contains a 320x240, 10 fps MJPEG + 24 kHz PCM AVI fixture.
