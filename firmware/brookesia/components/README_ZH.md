# Brookesia 固件组件

[English](README.md)

本目录包含 ESP32-S3-Touch-AMOLED-1.75 固件的产品应用、公共服务、开发板本地
适配，以及经过明确版本固定的安全覆盖层。这里并不是一组可以随意替换的上游库；
以下各类别具有不同的维护边界。

Brookesia 核心与 SquareLine 演示通过工程 `CMakeLists.txt` 中的
`EXTRA_COMPONENT_DIRS`，复用
`examples/esp-idf/03_esp-brookesia/components/` 下的组件，因此不会在此目录中
重复保存。

## 应用

| 目录 | 启动器应用 |
| --- | --- |
| [`brookesia_app_calculator/`](brookesia_app_calculator/) | Calculator（计算器） |
| [`Crosshair/`](Crosshair/) | 圆形显示与触摸对齐靶 |
| [`draw/`](draw/) | DrawPanel（画板） |
| [`Gallery/`](Gallery/) | SD 卡 JPEG 图库 |
| [`Gravitysphere/`](Gravitysphere/) | QMI8658 驱动的重力球 |
| [`MusicPlayer/`](MusicPlayer/) | 从 SD 卡或 SPIFFS 播放 MP3/WAV |
| [`Recorder/`](Recorder/) | 通过 ES7210 将立体声 WAV 录制到 SD 卡 |
| [`Settings/`](Settings/) | Wi-Fi、电池、显示、音频、存储和诊断设置 |
| [`SpecAnalyzer/`](SpecAnalyzer/) | ES7210 麦克风实时频谱分析仪 |
| [`VideoPlayer/`](VideoPlayer/) | 从 SD 卡播放 MJPEG/PCM AVI |
| [`XiaozhiApp/`](XiaozhiApp/) | AIChats 语音与文本应用 |

## 产品公共服务

| 目录 | 职责 |
| --- | --- |
| [`bsp_extra/`](bsp_extra/) | 本板 ES8311/ES7210 音频适配、PA 诊断、文件播放和独占音频会话所有权 |
| [`chat_history/`](chat_history/) | 可选的纯文本 AIChats JSONL 历史记录 |
| [`storage_service/`](storage_service/) | 共享 SD 挂载租约、存储卡恢复、诊断与安全弹出 |
| [`system_status/`](system_status/) | 为状态栏和 Settings 提供常驻 AXP2101 电池状态与原生 Wi-Fi 状态 |

这些服务负责协调多个应用共同使用的硬件或持久状态。应用必须调用其公共接口，
不得自行打开第二套编解码器、独立挂载 SD 卡，或另外维护一套 Wi-Fi/电池状态模型。

## 本地安全覆盖层

| 目录 | 上游基础与本地维护边界 |
| --- | --- |
| [`avi_player_safe/`](avi_player_safe/) | Espressif `avi_player` 2.0.0，加上文件解析检查和确定性的停止/反初始化清理 |
| [`esp_audio_player_safe/`](esp_audio_player_safe/) | `chmorgan/esp-audio-player` 1.1.0，加上确定性的工作任务与队列文件清理 |
| [`esp_xiaozhi_safe/`](esp_xiaozhi_safe/) | Espressif `esp_xiaozhi` 0.1.1，加上有界网络等待与事件队列等待 |

每个覆盖层都保留所选上游版本的公共版本号与 API，同时解决固件生命周期风险。
覆盖层的清单、源码、wrapper README 和使用组件中的 `override_path` 必须保持同步。
在本地行为已经由上游修复或确认不再需要之前，不得悄悄改回组件注册表下载版本。

## 托管 BSP 与第三方代码

`waveshare__esp32_s3_touch_amoled_1_75/` 是当前源码快照解析得到的 Waveshare
托管 BSP。它的组件清单和上游 README 属于托管组件维护边界。本固件专用的开发板
行为应放在 `bsp_extra/` 中；如果某项能力可供多个产品复用，则应在 Waveshare
公共组件仓库中维护。

嵌套在上游组件或明确 `third_party/` 目录中的代码，应保留其上游许可证、署名、
README 和命名。产品文档可以链接这些资料，但不应把它们改写成仿佛由本固件工程
拥有的内容。可选媒体和提示音资源在发布前也必须分别检查其许可证。

## 验证

修改应用或公共服务后，应构建完整工程，并在目标开发板上重新执行
[`../HARDWARE_VALIDATION_ZH.md`](../HARDWARE_VALIDATION_ZH.md) 中相应的验收章节。
涉及音频、存储或生命周期清理的修改还必须覆盖快速进入/退出和跨应用切换；构建
成功本身不能证明硬件上的资源所有权正确。
