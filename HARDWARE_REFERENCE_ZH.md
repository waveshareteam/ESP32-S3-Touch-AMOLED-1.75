# ESP32-S3-Touch-AMOLED-1.75 硬件参考

[English](HARDWARE_REFERENCE.md)

本文说明本仓库所使用的板级连接。以下定义已经与仓库内原理图及当前维护的 ESP-IDF BSP 交叉核对，并非从其他产品复制。若后续硬件版本存在差异，应以对应版本的原理图为最终依据。

## 板卡型号

| SKU | 产品 | 硬件区别 |
| --- | --- | --- |
| 31261 | ESP32-S3-Touch-AMOLED-1.75 | 标准版开发板 |
| 31262 | ESP32-S3-Touch-AMOLED-1.75-B | 标准版开发板，配保护外壳 |
| 31264 | ESP32-S3-Touch-AMOLED-1.75-G | GPS 版本，板载 LC76G 模块并配 GNSS 陶瓷天线 |

各版本的显示、触摸、电源、音频、存储、IMU、RTC 和扩展连接基础设计相同；`-G` 版本还会占用下文标注的 LC76G 相关资源。

## 板卡概览

| 功能 | 器件或接口 | 说明 |
| --- | --- | --- |
| MCU | ESP32-S3R8 | 双核 Xtensa LX7，主频最高 240 MHz，8 MB PSRAM，外置 16 MB Flash |
| 无线 | ESP32-S3 无线功能 | 2.4 GHz Wi-Fi 802.11 b/g/n 与 Bluetooth 5 LE |
| 显示 | CO5300 AMOLED 控制器 | 1.75 英寸，466 × 466，1670 万色，QSPI 接口 |
| 触摸 | CST9217 | 电容触摸，共用 I2C 总线，具有独立复位和中断线 |
| 电源 | AXP2101 | 为 3.7 V 电池接口提供电源路径、充电和电池监测功能 |
| 运动传感器 | QMI8658 | 六轴加速度计与陀螺仪 |
| RTC | PCF85063 | 实时时钟，备用电源由板上电源电路提供 |
| 音频输出 | ES8311 + NS4150B | I2S DAC/Codec、功放控制及 MX1.25 2Pin 扬声器接口 |
| 音频输入 | ES7210 | 四通道音频 ADC，连接两个板载麦克风及一路播放参考信号 |
| I/O 扩展 | TCA9554 | 为多个板载器件提供 Codec 控制以及中断/复位转接 |
| 存储 | TF/microSD 卡槽 | 原生 SDMMC 接线；仓库 BSP 以 1-bit 模式挂载 |
| USB | USB Type-C | ESP32-S3 原生 USB，用于烧录及串口/JTAG 工作流 |
| 扩展 | 2.54 mm 8Pin 排针 | VBUS、GND、3V3、UART0 及 3 个 GPIO |
| GNSS（仅 `-G`） | LC76G | GNSS 模块、天线接口/天线、I2C、可选 UART 连接及经扩展器控制的复位 |

## ESP32-S3 GPIO 分配

下表列出仓库原理图中所有连接到具名板级信号或扩展排针的 ESP32-S3 GPIO。Flash/PSRAM 内部使用的引脚、PCB 未引出的引脚以及电源/地引脚均不应视为可用 GPIO，因此不在表内。

| GPIO | 信号 | 板级连接 | 使用说明 |
| ---: | --- | --- | --- |
| 0 | `BOOT` | BOOT 按键/下载模式启动配置脚 | 复位期间不要由外部电路强制为不兼容电平。 |
| 1 | `SD_CMD` | TF 卡 CMD | SDMMC 工作时应保留。 |
| 2 | `SD_CLK` | TF 卡时钟 | SDMMC 工作时应保留。 |
| 3 | `SD_D0` | TF 卡 D0 | 1-bit SDMMC 数据线。 |
| 4 | `LCD_DATA0` | CO5300 QSPI SIO0 | 显示总线。 |
| 5 | `LCD_DATA1` | CO5300 QSPI SIO1 | 显示总线。 |
| 6 | `LCD_DATA2` | CO5300 QSPI SIO2 | 显示总线。 |
| 7 | `LCD_DATA3` | CO5300 QSPI SIO3 | 显示总线。 |
| 8 | `I2S_DOUT` | ESP32-S3 至 ES8311 DSDIN | 播放数据输出。 |
| 9 | `I2S_BCLK` / `I2S_SCLK` | ES8311 与 ES7210 位时钟 | 共用音频时钟。 |
| 10 | `I2S_DIN` / `I2S_ASDOUT` | ES7210 至 ESP32-S3 | 麦克风/TDM 接收数据。 |
| 11 | `TP_INT` | CST9217 中断 | 触摸控制器中断。 |
| 12 | `LCD_CS` | CO5300 片选 | 显示总线。 |
| 13 | `LCD_TE` | CO5300 撕裂效应信号 | 输入 MCU 的显示同步信号。 |
| 14 | `I2C_SCL` | 板载共用 I2C 时钟 | 由下方 I2C 表中的所有器件共用。 |
| 15 | `I2C_SDA` | 板载共用 I2C 数据 | 由下方 I2C 表中的所有器件共用。 |
| 16 | `GPIO16` | 扩展排针 Pin 8 | 通用 3.3 V GPIO；当前维护的 BSP **未**将其用作音频 MCLK。 |
| 17 | `GPIO17` | 扩展排针 Pin 6 | 标准版/`-B` 可作通用 GPIO；`-G` 版可能作为 MCU TX 连接 LC76G RX。 |
| 18 | `GPIO18` | 扩展排针 Pin 7 | 标准版/`-B` 可作通用 GPIO；`-G` 版可能作为 MCU RX 连接 LC76G TX。 |
| 19 | `USB_D-` | USB Type-C D- | 使用原生 USB 时应保留。 |
| 20 | `USB_D+` | USB Type-C D+ | 使用原生 USB 时应保留。 |
| 21 | `QMI_INT2` | QMI8658 INT2 | IMU 直接中断；INT1 经 TCA9554 转接。 |
| 38 | `LCD_PCLK` | CO5300 QSPI 时钟 | 显示总线。 |
| 39 | `LCD_RST` | CO5300 复位 | 显示复位，与触摸复位相互独立。 |
| 40 | `TP_RST` | CST9217 复位 | 触摸复位，与显示复位相互独立。 |
| 41 | `SD_D3/CS` / `SDCS` | TF 卡 D3/CS | PCB 已连接；当前 BSP 的 1-bit SDMMC 挂载未使用此线。 |
| 42 | `I2S_MCLK` | ES8311 与 ES7210 主时钟 | 当前维护 BSP 使用的音频主时钟。 |
| 43 | `U0TXD` | 扩展排针 Pin 5 | ESP32-S3 的 UART0 发送；也可能承载控制台输出。 |
| 44 | `U0RXD` | 扩展排针 Pin 4 | ESP32-S3 的 UART0 接收。 |
| 45 | `I2S_LRCK` / `I2S_WS` | ES8311 与 ES7210 字选择时钟 | 共用音频帧时钟。 |
| 46 | `PA_CTRL` | NS4150B 功放控制电路 | 由 BSP 音频路径控制；请使用 BSP API，不要自行假定电气有效电平。 |

## 共用 I2C 总线

板载总线使用 GPIO14 作为 SCL、GPIO15 作为 SDA。下表均为仓库代码及原理图配置所使用的 7-bit 地址。

| 地址 | 器件 | 适用范围及作用 |
| ---: | --- | --- |
| `0x18` | ES8311 | 仓库配置使用的播放 Codec 地址；Codec CE 由 TCA9554 管理。 |
| `0x20` | TCA9554 | 板载 I/O 扩展器，A2:A0 配置为 `000` 地址。 |
| `0x34` | AXP2101 | 电源管理、充电及电池遥测。 |
| `0x40` | ES7210 | 四通道麦克风/音频 ADC。 |
| `0x51` | PCF85063 | 实时时钟。 |
| `0x5A` | CST9217 | 电容触摸控制器。 |
| `0x6B` | QMI8658 | 由板卡原理图选择的 IMU 地址。 |
| `0x50` / `0x54` | LC76G（仅 `-G`） | 仓库 LC76G I2C 示例使用 `0x50` 发送命令/写入，使用 `0x54` 读取。 |

部分 ESP 音频 Codec 头文件会以 8-bit 形式表示同一地址：ES8311 为 `0x30`，ES7210 为
`0x80`。对于要求 7-bit 地址的 API，不要传入这些 8-bit 常量，应分别使用 `0x18` 与 `0x40`。

共用总线只应初始化一次，并传递或复用其句柄。当前维护的 BSP 默认使用 400 kHz I2C 时钟，而独立的 LC76G Arduino 示例使用 100 kHz；`-G` 版本应用应选择所有已启用器件均支持的总线速率。

## TCA9554 扩展器分配

| 扩展器引脚 | 板级信号 | 正常使用方向 | 连接功能 |
| --- | --- | --- | --- |
| P0 / `EXIO0` | `EXIO0` | 由应用定义 | 原理图未指定固定外设功能，可在测试点访问。 |
| P1 / `EXIO1` | `EXIO1` | 由应用定义 | 原理图未指定固定外设功能，可在测试点访问。 |
| P2 / `EXIO2` | `EXIO2` | 由应用定义 | 原理图未指定固定外设功能，可在测试点访问。 |
| P3 / `EXIO3` | `Codec_CE` | 输出 | ES8311 Codec 控制/地址使能路径。 |
| P4 / `EXIO4` | `RTC_INT` | 输入 | PCF85063 中断。 |
| P5 / `EXIO5` | `AXP_IRQ` | 输入 | AXP2101 中断。 |
| P6 / `EXIO6` | `QMI_INT1` | 输入 | QMI8658 INT1。 |
| P7 / `EXIO7` | `GPS_RST` | 输出 | `-G` 版本 LC76G 复位；其他版本为可选功能。 |

## I2S 音频接口

| 音频信号 | ESP32-S3 GPIO | 相对 MCU 的方向 | 目标/来源 |
| --- | ---: | --- | --- |
| MCLK | 42 | 输出 | ES8311 与 ES7210 共用 |
| BCLK/SCLK | 9 | 输出 | ES8311 与 ES7210 共用 |
| LRCK/WS | 45 | 输出 | ES8311 与 ES7210 共用 |
| 播放数据 | 8 | 输出 | ES8311 DSDIN |
| 采集数据 | 10 | 输入 | ES7210 SDOUT1/TDMOUT |
| PA 控制 | 46 | 控制 | 板上功放控制电路，由 BSP 管理 |

当前维护的 BSP 支持在同一组物理时钟上，以标准 I2S 驱动 ES8311 播放，并以四时隙 TDM 从 ES7210 采集。其语音配置为 24 kHz、16-bit、标准 I2S 双声道 TX，加四时隙 TDM RX，MCLK 倍频为 ×256。ES7210 物理输入连接如下：

- MIC1 与 MIC2：两个板载前置麦克风。
- MIC3：来自 ES8311 的模拟播放参考信号，供软件进行回声处理。
- MIC4：未连接。

BSP 的四个接收时隙顺序为 MIC1、MIC3（参考）、MIC2、MIC4。请使用 BSP 定义的通道掩码，不要假定物理麦克风编号与串行时隙编号相同。

## TF 卡 / SDMMC

| SD 信号 | GPIO | 当前 BSP 用法 |
| --- | ---: | --- |
| CMD | 1 | 1-bit SDMMC 命令 |
| CLK | 2 | 1-bit SDMMC 时钟 |
| D0 | 3 | 1-bit SDMMC 数据 |
| D3/CS（`SDCS`） | 41 | PCB 已连接，但当前 1-bit SDMMC 挂载未选用 |

BSP 将 D1 至 D7 配置为未连接，也未声明卡检测或写保护 GPIO。TF 卡挂载期间不要复用 GPIO1、GPIO2 或 GPIO3。GPIO41 是卡的 D3/CS 信号，并非机械卡检测输入。

## 8Pin 扩展排针

引脚编号与原理图中的 `H2` 排针一致。

| 排针 Pin | 信号 | 说明 |
| ---: | --- | --- |
| 1 | VBUS | USB 电源轨；需注意电源共享与倒灌要求。 |
| 2 | GND | 地。 |
| 3 | 3V3 | 板上 3.3 V 电源轨；使用前确认电流及外部供电要求。 |
| 4 | GPIO44 / U0RXD | ESP32-S3 的 UART0 接收。 |
| 5 | GPIO43 / U0TXD | ESP32-S3 的 UART0 发送。 |
| 6 | GPIO17 | 通用 GPIO；`-G` 版本可能与 LC76G RX 共用。 |
| 7 | GPIO18 | 通用 GPIO；`-G` 版本可能与 LC76G TX 共用。 |
| 8 | GPIO16 | 通用 GPIO。 |

所有 GPIO 均为 3.3 V 逻辑，不耐受 5 V。VBUS 是电源轨，不能作为逻辑电平参考。

## 电源、USB、显示与按键

- 电池接口用于单节 3.7 V 锂电池。充电及遥测应使用 AXP2101 驱动并遵循板上电源设计。
- PWR 按键属于 AXP2101 电源控制路径，并非空闲的 ESP32-S3 GPIO；BOOT 按键连接 GPIO0。
- GPIO19/GPIO20 是原生 USB D-/D+。复用它们可能导致 USB 烧录、USB Serial/JTAG 或应用 USB 功能失效。
- AMOLED 没有独立的 GPIO LED 背光。亮度由 CO5300 面板命令控制，通用 LCD 背光 PWM 示例不适用。
- 显示复位为 GPIO39，触摸复位为 GPIO40，不应把两者当成同一条复位线。

## 集成注意事项

1. 添加外部外设前，应先保留所有板载功能已占用的 GPIO。扩展排针上的引脚仍可能与控制台或 GNSS 功能共用。
2. 在 `-G` 版本上复用 GPIO17/GPIO18 前，应确认实际装配的 UART 连接，并通过 TCA9554 P7 协调 LC76G 复位。
3. 应复用现有 I2C 控制器，而不是在 GPIO14/GPIO15 上安装多个独立驱动；新增器件还需检查地址冲突。
4. 音频 MCLK 使用 GPIO42。GPIO16 在当前维护 BSP 与板卡原理图中是扩展 GPIO。
5. ES8311、ES7210、功放控制路径及共用时钟应交由 BSP 管理。直接切换 GPIO46 或 TCA9554 P3 可能与 Codec 生命周期管理冲突。
6. GPIO0 是启动配置脚，GPIO43/GPIO44 可能用于 UART0；外部电路不能妨碍启动或固件恢复。
7. 从外部电源驱动 VBUS 或 3V3 前，必须评估倒灌、稳压以及 AXP2101 电源路径。

## 参考资料

- [仓库原理图](Schematic/ESP32-S3-Touch-AMOLED-1.75-schematic.pdf)
- [当前维护的 ESP-IDF BSP 引脚定义](firmware/brookesia/components/waveshare__esp32_s3_touch_amoled_1_75/include/bsp/esp32_s3_touch_amoled_1_75.h)
- [当前维护的 ESP-IDF BSP 实现](firmware/brookesia/components/waveshare__esp32_s3_touch_amoled_1_75/esp32_s3_touch_amoled_1_75.c)
- [AXP2101 ESP-IDF 示例](examples/esp-idf/01_AXP2101)
- [LC76G I2C Arduino 示例](examples/arduino/09_LC76G_I2C/09_LC76G_I2C.ino)
- [Waveshare 官方文档](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75)
- [Waveshare 官方产品页](https://www.waveshare.com/product/esp32-s3-touch-amoled-1.75.htm)
