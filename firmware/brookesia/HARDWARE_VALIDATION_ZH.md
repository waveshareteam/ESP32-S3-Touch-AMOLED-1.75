# ESP32-S3-Touch-AMOLED-1.75 硬件验收

[English](HARDWARE_VALIDATION.md)

本检查表用于在目标开发板上验收带 SD 卡素材的 Brookesia 固件。如果故障导致
重启、看门狗、栈溢出、白屏、局部画面损坏、SD 访问租约泄漏或音频所有者冲突，
则不能判定验收通过。

连接硬件前，先在仓库根目录校验发布文件和源码中的测试素材：

```powershell
& .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline
```

## 1. 准备确定性的 SD 卡测试素材

客户 SD 卡素材包为 `firmware/SD-Card-Media-260805.zip`。准备脚本会直接读取该
压缩包，因此仓库中不保留重复解压的素材目录。如需把项目生成的合成测试素材
重新生成到临时工作目录，请使用安装了 Pillow 的 Python 环境：

```powershell
python -m pip install Pillow
$mediaWorkDir = Join-Path $env:TEMP "esp32-s3-touch-amoled-1-75-sd-media"
python firmware\brookesia\tools\generate_sd_test_media.py $mediaWorkDir
```

将 SD 卡插入 Windows 读卡器，然后复制测试素材目录树；脚本不会格式化存储卡，
也不会删除已有文件：

```powershell
$sdDrive = 'X:' # 替换为 SD 卡盘符。
& .\firmware\brookesia\tools\prepare_sd_card.ps1 -Drive $sdDrive
& .\firmware\brookesia\tools\hardware_preflight.ps1 -Offline -SdDrive $sdDrive
```

脚本会拒绝 Windows 系统盘，并且默认拒绝系统未识别为可移动磁盘的驱动器。只有在
人工确认固定类型的驱动器确实是 SD 卡后，才能使用 `-AllowFixedDrive`。除非明确
提供 `-Overwrite`，否则会保留已有文件。固件要求使用 FAT/FAT32 文件系统，未启用
exFAT。复制脚本会拒绝不支持的文件系统，而且绝不会格式化存储卡。

预期的存储卡目录结构：

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

## 2. 烧录完整镜像

合并镜像必须写入 `0x0`，而不是应用程序分区偏移地址。

激活配置好的 ESP-IDF v5.5.4 环境、连接开发板，然后在烧录前运行完整预检：

```powershell
$port = 'COMx' # 替换为开发板串口。
& .\firmware\brookesia\tools\hardware_preflight.ps1 -Port $port
python -m esptool --chip esp32s3 --port $port --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m 0x0 firmware\ESP32-S3-Touch-AMOLED-1.75-FactoryOnly-260805.bin
```

烧录完成后，在配置好的 ESP-IDF v5.5.4 环境中启动串口监视器：

```powershell
$port = 'COMx' # 替换为开发板串口。
$brookesiaBuildDir = Join-Path $env:TEMP "esp32-s3-touch-amoled-1-75-build-v5.5.4"
idf.py -C firmware\brookesia -B $brookesiaBuildDir -p $port monitor
```

首次启动必须正常进入启动器，不得出现 panic、栈溢出、看门狗、白屏或刷新不完整。
确认 P4 风格加载画面逐步完成各初始化阶段、到达 `Ready`，并平滑淡出到完整的
466 x 466 Brookesia 画面。

## 3. Button Test 按键测试

1. 在两个按键都松开的情况下打开 **Button Test**。确认 PWR 显示 `RAW LOW`，
   BOOT 显示 `RAW HIGH`，两张卡片都显示 `RELEASED` 和 `WAITING`。
2. 短按 PWR，不要长按。确认只有 PWR 卡片变为 `RAW HIGH` 和 `PRESSED`；松开后
   恢复为 `RAW LOW` 和 `RELEASED`，同时保留 `PASS LATCHED`。
3. 按下 BOOT。确认只有 BOOT 卡片变为 `RAW LOW` 和 `PRESSED`；松开后恢复为
   `RAW HIGH` 和 `RELEASED`，同时保留 `PASS LATCHED`。
4. 确认底部提示变为 `ALL BUTTONS PASSED`。测试不得读取 AXP2101 按键寄存器；
   PWR 只从 TCA9554 EXIO4 采样，BOOT 只从 GPIO0 采样。
5. 连续退出并重新打开 Button Test 五次。启动器必须始终响应，每次新会话都应清除
   两个锁存结果，且关闭应用后不得有工作任务或 LVGL 定时器继续访问已关闭的页面。

## 4. 存储与 Settings

1. 打开 **Settings > Storage**。
2. 确认已显示存储卡名称、容量、可用空间、1 位 SDMMC 总线和时钟信息。
3. 运行 4 MiB 基准测试。只有读写都完成，并且预期 CRC32 与实际 CRC32 一致时，
   测试才算通过。
4. 导出诊断信息，确认 `/Waveshare/Diagnostics` 下出现新的文本文件。
5. 启用 AI 聊天历史记录，关闭 Settings 后重新打开，确认设置已持久化保存。

## 5. MusicPlayer 与共享音频所有权

1. 打开 **MusicPlayer**，确认六个立体声 WAV 测试曲目全部被索引。
2. 确认上一首、播放/暂停和下一首按钮在 466 x 466 圆屏布局中清晰可见且响应正常。
3. 从第 5 首切换到第 6 首，再切换回来，以覆盖第二个列表页面。
4. 播放第 1 首曲目，确认左声道可听到 440 Hz，右声道可听到 880 Hz。
5. 暂停播放，退出应用，再次打开，并重复快速进入/退出五次。
6. 依次在 MusicPlayer、SpecAnalyzer、Recorder、VideoPlayer 和 AIChats 之间切换。
   每个应用必须成功取得音频资源，或明确报告资源忙；任何应用都不得重启，也不得
   从其他所有者手中抢占 ES8311/ES7210 会话。

## 6. Gallery

1. 打开 **Gallery**，确认两个基线编码 JPEG 测试图片均被索引。
2. 测试上一张、下一张和幻灯片控制。
3. 确认宽图和方图均居中显示，没有残留像素或局部刷新区域。
4. 在图片加载过程中关闭 Gallery，然后重新打开，重复五次。
5. 临时重命名 `/photos`，重新打开 Gallery，并确认错误页面不会持续占用 SD 访问
   租约；此时 Settings 中的安全弹出仍必须能够成功执行。

## 7. Recorder

1. 开始录音，并依次靠近两个麦克风说话，录制至少十秒。
2. 正常停止录音，确认 `/Waveshare/Recordings` 下出现 WAV 文件。
3. 在电脑上播放该文件，确认格式为 24 kHz、16 位、立体声，并且 ES7210 的两个
   麦克风通道都包含音频。
4. 重复开始/停止五次，并在正在录音时关闭应用。输出必须仍是可读取的 WAV 文件，
   而不是长度为零的文件。

## 8. VideoPlayer

1. 播放 `01-mjpeg-320x240-10fps-pcm24k.avi`。
2. 确认移动白色方块按照有意设置的 10 fps 上限平滑前进，并且可以听到 PCM 音频。
3. 测试暂停、上一段、下一段、自然播放结束、立即返回和重新打开。
4. 连续十次快速进入并立即返回。任何 AVI 回调都不得访问已经释放的画布、帧缓冲、
   文件、编解码器或 SD 访问租约。

## 9. 安全弹出、重新插入和历史记录

1. MusicPlayer 或 VideoPlayer 持有已打开文件时，**Safe eject** 必须报告资源忙，
   并保持存储卡挂载。
2. 关闭媒体应用后重试。安全弹出必须成功卸载存储卡。
3. 拔出并重新插入存储卡，选择重新扫描，确认所有测试素材重新出现。
4. 使用 AIChats 完成一次文本交互，关闭应用；启用历史记录时，确认
   `/Waveshare/AIChats` 下出现 JSONL 记录。关闭历史记录后，确认后续交互不再
   追加到文件中。
5. 停止所有写入任务后，不执行安全弹出就拔出存储卡，再重新插入，然后直接打开
   Gallery，不要先进入 Settings。新的第一次存储访问租约必须检测到失效挂载并
   自动恢复。

如果 Recorder 在采集到音频后报告保存失败，请在电脑上检查对应的
`.wav.partial` 文件。其文件头每五秒执行一次检查点更新，因此中断的录音不会被
发布成成功完成的 `.wav` 文件。

## 10. 最终耐久验收

在监视串口输出的同时，至少循环进入全部启动器应用二十次。只有在整个过程中没有
panic、看门狗、栈溢出、堆断言、无效状态循环、应用关闭后仍占用 SD 访问租约，
以及跨所有者释放音频资源错误时，发布版本才能通过验收。记录最终固件 SHA256、
SD 卡标识、基准测试结果、电池读数、Wi-Fi RSSI 和串口日志，并与测试结果一同保存。
