# Brookesia 固件

[English](README.md)

面向客户的交付说明，以及烧录、SD 卡和 FFmpeg 素材制作说明见
[`../README_ZH.md`](../README_ZH.md) 和
[`../MEDIA_GUIDE_ZH.md`](../MEDIA_GUIDE_ZH.md)。本地应用、公共服务与安全覆盖层
的维护边界见[组件说明](components/README_ZH.md)。

本项目将 ESP32-P4-WIFI6-Touch-LCD-4B Brookesia 固件中可复用的应用层
移植到 ESP32-S3-Touch-AMOLED-1.75。

本固件专门使用目标板原生 BSP，以驱动 466 x 466 CO5300 QSPI AMOLED、
CST9217 触摸控制器、ES8311/ES7210 音频器件以及 ESP32-S3 原生 Wi-Fi。
项目不包含仅适用于 P4 的 MIPI DSI、PPA、ESP-Hosted/C6、摄像头、以太网、
继电器和 RS485 代码。

包含以下应用：

- SquareLine 演示
- Calculator（计算器）
- DrawPanel（画板）
- SpecAnalyzer（频谱分析仪），通过 ES7210 获取实时双麦克风 FFT 数据
- MusicPlayer（音乐播放器），播放 `/sdcard/music` 中的 MP3/WAV 文件，
  并以 `/spiffs/music` 作为后备目录
- Gallery（图库），浏览 `/sdcard/photos` 中的基线编码 JPG/JPEG 图片，
  支持异步解码、上一张/下一张控制和幻灯片模式
- VideoPlayer（视频播放器），播放 `/sdcard/video` 中特意采用低帧率的
  MJPEG/PCM AVI 文件
- Recorder（录音机），将两个前置 ES7210 麦克风采集的 24 kHz、16 位立体声
  WAV 录音保存到 `/sdcard/Waveshare/Recordings`；每五秒对临时
  `.wav.partial` 文件执行一次检查点写入，并且仅在同步关闭文件后发布最终
  `.wav` 文件
- Settings（设置），提供原生 Wi-Fi、AMOLED 亮度、音量、AXP2101 电池遥测、
  充电状态、Wi-Fi RSSI、SD 卡信息、CRC 基准测试、诊断信息导出和安全弹出功能
- AIChats，支持 WakeNet、VAD、Opus 音频、激活流程和小智传输通道
- Gravitysphere（重力球），由 QMI8658 加速度计实时数据驱动，并将球体及其光晕
  限制在面板真实的圆形边界内
- Crosshair（十字准星），提供带同心圆、方位刻度和中心轴的全屏圆形校准靶，
  并支持通过触摸选择对比配色方案

## SD 卡目录结构

存储卡通过开发板的 1 位 SDMMC 连接按需挂载为 FAT/FAT32 文件系统，
挂载点为 `/sdcard`。固件已启用长 UTF-8 文件名。请使用以下目录：

| 目录 | 用途和格式 |
| --- | --- |
| `/sdcard/music` | MP3 和 WAV 曲目；为兼容旧目录，也接受 `/sdcard/Music` |
| `/sdcard/photos` | 基线编码 JPG/JPEG；单个文件最大 4 MiB，最多索引 128 张图片 |
| `/sdcard/video` | MJPEG AVI；可选音频必须为 16 位 PCM 单声道或立体声 |
| `/sdcard/Waveshare/Recordings` | Recorder 创建的立体声 WAV 文件 |
| `/sdcard/Waveshare/AIChats` | 可选的纯文本 JSONL 聊天记录 |
| `/sdcard/Waveshare/Diagnostics` | 设备、SD 卡、电池和 Wi-Fi 诊断快照 |

视频播放有意限制为最高每秒显示 10 帧。对于这块 466 x 466 QSPI 面板，
建议将 MJPEG 编码为约 320 x 240 或 360 x 360、10 fps，并确保每帧尺寸不超过
466 x 466。PCM 音频可使用 8、12、16、24、32、44.1 或 48 kHz 采样率。
不支持 H.264 和使用压缩音频的 AVI 文件。

设备在空闲一段时间后首次取得存储访问权时，会探测已挂载的存储卡。如果存储卡
被意外拔出后重新插入，存储服务会先丢弃失效的挂载并重新挂载，再将文件系统交给
应用。安全弹出状态会保持锁定，直至用户明确选择 **Rescan card（重新扫描存储卡）**。

`firmware/SD-Card-Media-260805.zip` 中提供了不受版权限制的 WAV、基线编码
JPEG 和 MJPEG/PCM AVI 测试素材。其中六首 WAV 曲目还覆盖 MusicPlayer 的第二个
列表页面。`tools/prepare_sd_card.ps1` 会直接读取该 ZIP，并在不格式化存储卡、
不替换现有文件的前提下，将测试素材复制到 FAT/FAT32 可移动存储卡。
ZIP 中还包含中英双语 `README.txt` 和完整的双语 `MEDIA_GUIDE.md`，后者提供了
适用于本固件的 FFmpeg 和 ffprobe 命令。
完整的串口、UI、存储、音频资源所有权、安全弹出和耐久性测试流程见
[`HARDWARE_VALIDATION_ZH.md`](HARDWARE_VALIDATION_ZH.md)。
现在可运行 `tools/hardware_preflight.ps1 -Offline` 验证发布文件哈希和测试素材
清单；激活 ESP-IDF 并连接目标开发板后，再去掉 `-Offline` 重新运行。

Phone 状态栏也由真实硬件状态驱动：电池图标和百分比跟随 AXP2101 电量计及充电
状态，Wi-Fi 图标则跟随 Station 连接状态和实际 RSSI 等级。常驻状态服务采用
官方开发板示例中的安全充电配置（关闭 TS 测量、50 mA 预充电、400 mA 恒流充电、
25 mA 终止电流和 4.2 V 目标电压），在启动时恢复持久化保存的 Wi-Fi 开关状态，
并且即使 Settings 已关闭，也会继续执行重新连接。开发板专用的圆屏样式表会将这些
部件移入屏幕顶部的可见弦形区域，而不是放在并不存在的矩形屏幕角落。启动器每页
使用居中的 2 x 2 安全网格，并保留每个图标的 112 x 112 尺寸，而不会按照通用矩形
手机布局将其缩小。

Crosshair 启动器图标保留为 112 x 112 圆角 PNG，并使用托管 `lvgl` 组件中官方
LVGL v9 的 `scripts/LVGLImage.py` 工具转换为 `ARGB8888` C 数据。依赖解析完成后，
可使用以下命令重新生成：

```text
python managed_components/lvgl__lvgl/scripts/LVGLImage.py --ofmt C --cf ARGB8888 --name img_app_crosshair --output components/Crosshair/assets components/Crosshair/assets/img_app_crosshair.png
```

## 构建

使用 ESP-IDF 5.5，并以 `esp32s3` 为目标进行构建：

```text
idf.py -C firmware/brookesia set-target esp32s3 build
```

本项目复用 `examples/esp-idf/03_esp-brookesia/components/` 中已经维护的
Brookesia 核心和 SquareLine 组件，不会重复存放这些大型源码树。

16 MB 分区表为应用程序预留 8 MB，为 `storage` SPIFFS 分区预留 6 MB，并为
ESP-SR 模型分区预留 960 KB。构建过程会生成并烧录选定的 WakeNet 模型，同时从
托管 `xiaozhi-fonts` 组件中暂存 AIChats 字体。生成的 SPIFFS 镜像不包含任何
第三方音乐或提示音频。

使用 `idf.py -C firmware/brookesia flash monitor` 执行完整烧录。首次安装 AIChats
时必须执行完整烧录，因为分区表、`srmodels.bin`、应用程序和 `storage.bin` 必须
相互匹配。

## 硬件验证

ESP-IDF v5.5.4 构建成功可验证全部十二个应用、存储镜像和 ESP-SR 模型镜像能够
一同完成编译与打包。当前带日期的出厂固件及其交付检查记录见
[`../README_ZH.md`](../README_ZH.md)。任何源码变更后，重新生成的出厂固件候选版本
必须再次完成 [`HARDWARE_VALIDATION_ZH.md`](HARDWARE_VALIDATION_ZH.md) 中针对目标
开发板的检查，包括显示、触摸、AXP2101 电量计行为、QMI8658 方向、Wi-Fi、
麦克风/扬声器音频、存储以及长时间应用切换；通过这些检查后，才可替换已发布的
出厂固件。
