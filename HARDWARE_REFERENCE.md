# ESP32-S3-Touch-AMOLED-1.75 Hardware Reference

[简体中文](HARDWARE_REFERENCE_ZH.md)

This reference describes the board-level connections used by this repository. The assignments below were cross-checked against the repository schematic and the maintained ESP-IDF BSP; they are not copied from another product. If a later hardware revision differs, the schematic for that revision is the final authority.

## Board variants

| SKU | Product | Hardware distinction |
| --- | --- | --- |
| 31261 | ESP32-S3-Touch-AMOLED-1.75 | Standard board |
| 31262 | ESP32-S3-Touch-AMOLED-1.75-B | Standard board supplied with a protective case |
| 31264 | ESP32-S3-Touch-AMOLED-1.75-G | GPS version with an onboard LC76G module and a GNSS ceramic antenna |

The base display, touch, power, audio, storage, IMU, RTC, and expansion connections are shared. On the `-G` variant, the LC76G also uses board resources identified below.

## Board overview

| Function | Device or interface | Details |
| --- | --- | --- |
| MCU | ESP32-S3R8 | Dual-core Xtensa LX7 up to 240 MHz, 8 MB PSRAM, external 16 MB flash |
| Wireless | ESP32-S3 radio | 2.4 GHz Wi-Fi 802.11 b/g/n and Bluetooth 5 LE |
| Display | CO5300 AMOLED controller | 1.75-inch, 466 × 466, 16.7 million colors, QSPI |
| Touch | CST9217 | Capacitive touch over the shared I2C bus, with dedicated reset and interrupt lines |
| Power | AXP2101 | Power-path, charging, and battery monitoring for the 3.7 V battery connector |
| Motion | QMI8658 | 6-axis accelerometer and gyroscope |
| RTC | PCF85063 | Real-time clock with backup supply provided by the board power circuit |
| Audio output | ES8311 + NS4150B | I2S DAC/codec, power amplifier control, and MX1.25 2-pin speaker connector |
| Audio input | ES7210 | Four-channel audio ADC connected to two onboard microphones and a playback-reference path |
| I/O expansion | TCA9554 | Provides codec control and interrupt/reset routing for several onboard devices |
| Storage | TF/microSD slot | Native SDMMC wiring; the repository BSP mounts it in 1-bit mode |
| USB | USB Type-C | ESP32-S3 native USB for flashing and serial/JTAG workflows |
| Expansion | 2.54 mm 8-pin header | VBUS, GND, 3V3, UART0, and three GPIOs |
| GNSS (`-G` only) | LC76G | GNSS module, antenna connector/antenna, I2C, optional UART routing, and expander-controlled reset |

## ESP32-S3 GPIO assignment

The table lists every numbered ESP32-S3 GPIO routed to a named board signal or the expansion header in the repository schematic. Pins used internally for flash/PSRAM, pins not routed on the PCB, and power/ground pins are not presented as available GPIOs.

| GPIO | Signal | Board connection | Usage notes |
| ---: | --- | --- | --- |
| 0 | `BOOT` | BOOT push button / download-mode strap | Do not force to an incompatible level during reset. |
| 1 | `SD_CMD` | TF card CMD | Reserved while SDMMC is active. |
| 2 | `SD_CLK` | TF card clock | Reserved while SDMMC is active. |
| 3 | `SD_D0` | TF card D0 | 1-bit SDMMC data line. |
| 4 | `LCD_DATA0` | CO5300 QSPI SIO0 | Display bus. |
| 5 | `LCD_DATA1` | CO5300 QSPI SIO1 | Display bus. |
| 6 | `LCD_DATA2` | CO5300 QSPI SIO2 | Display bus. |
| 7 | `LCD_DATA3` | CO5300 QSPI SIO3 | Display bus. |
| 8 | `I2S_DOUT` | ESP32-S3 to ES8311 DSDIN | Playback data output. |
| 9 | `I2S_BCLK` / `I2S_SCLK` | ES8311 and ES7210 bit clock | Shared audio clock. |
| 10 | `I2S_DIN` / `I2S_ASDOUT` | ES7210 to ESP32-S3 | Microphone/TDM receive data. |
| 11 | `TP_INT` | CST9217 interrupt | Touch controller interrupt. |
| 12 | `LCD_CS` | CO5300 chip select | Display bus. |
| 13 | `LCD_TE` | CO5300 tearing-effect signal | Display synchronization input to the MCU. |
| 14 | `I2C_SCL` | Shared onboard I2C clock | Used by all devices in the I2C table below. |
| 15 | `I2C_SDA` | Shared onboard I2C data | Used by all devices in the I2C table below. |
| 16 | `GPIO16` | Expansion header pin 8 | General 3.3 V GPIO; the maintained BSP does **not** use it as audio MCLK. |
| 17 | `GPIO17` | Expansion header pin 6 | General GPIO on standard/`-B`; may be routed as MCU TX to LC76G RX on `-G`. |
| 18 | `GPIO18` | Expansion header pin 7 | General GPIO on standard/`-B`; may be routed as MCU RX from LC76G TX on `-G`. |
| 19 | `USB_D-` | USB Type-C D- | Reserved when native USB is in use. |
| 20 | `USB_D+` | USB Type-C D+ | Reserved when native USB is in use. |
| 21 | `QMI_INT2` | QMI8658 INT2 | Direct IMU interrupt; INT1 is routed through the TCA9554. |
| 38 | `LCD_PCLK` | CO5300 QSPI clock | Display bus. |
| 39 | `LCD_RST` | CO5300 reset | Display reset; separate from touch reset. |
| 40 | `TP_RST` | CST9217 reset | Touch reset; separate from display reset. |
| 41 | `SD_D3/CS` / `SDCS` | TF card D3/CS | Wired on the PCB; the current BSP 1-bit SDMMC mount does not use this line. |
| 42 | `I2S_MCLK` | ES8311 and ES7210 master clock | Audio master clock used by the maintained BSP. |
| 43 | `U0TXD` | Expansion header pin 5 | UART0 transmit from the ESP32-S3; may also carry console output. |
| 44 | `U0RXD` | Expansion header pin 4 | UART0 receive into the ESP32-S3. |
| 45 | `I2S_LRCK` / `I2S_WS` | ES8311 and ES7210 word-select clock | Shared audio frame clock. |
| 46 | `PA_CTRL` | NS4150B amplifier control circuit | Controlled by the BSP audio path; use the BSP API instead of assuming an electrical active level. |

## Shared I2C bus

The onboard bus uses GPIO14 for SCL and GPIO15 for SDA. Addresses below are 7-bit addresses used by the repository code and schematic configuration.

| Address | Device | Availability and role |
| ---: | --- | --- |
| `0x18` | ES8311 | Playback codec address used by the repository configuration; codec CE is managed through the TCA9554. |
| `0x20` | TCA9554 | Onboard I/O expander with A2:A0 strapped for the `000` address. |
| `0x34` | AXP2101 | Power-management, charging, and battery telemetry. |
| `0x40` | ES7210 | Four-channel microphone/audio ADC. |
| `0x51` | PCF85063 | Real-time clock. |
| `0x5A` | CST9217 | Capacitive touch controller. |
| `0x6B` | QMI8658 | IMU address selected by the board schematic. |
| `0x50` / `0x54` | LC76G (`-G` only) | The repository LC76G I2C example uses `0x50` for commands/writes and `0x54` for reads. |

Some ESP audio-codec headers express the same codec addresses in 8-bit form: `0x30` for ES8311 and
`0x80` for ES7210. Do not pass those 8-bit constants to an API that expects the 7-bit addresses
`0x18` and `0x40`.

Initialize the shared bus once and pass or reuse its handle. The maintained BSP defaults to a 400 kHz I2C clock, while the standalone LC76G Arduino example uses 100 kHz; applications using the `-G` variant should choose a bus speed supported by every active device.

## TCA9554 expander assignment

| Expander pin | Board signal | Direction in normal use | Connected function |
| --- | --- | --- | --- |
| P0 / `EXIO0` | `EXIO0` | Application-defined | No fixed peripheral function shown; available at a test point. |
| P1 / `EXIO1` | `EXIO1` | Application-defined | No fixed peripheral function shown; available at a test point. |
| P2 / `EXIO2` | `EXIO2` | Application-defined | No fixed peripheral function shown; available at a test point. |
| P3 / `EXIO3` | `Codec_CE` | Output | ES8311 codec control/address-enable path. |
| P4 / `EXIO4` | `RTC_INT` | Input | PCF85063 interrupt. |
| P5 / `EXIO5` | `AXP_IRQ` | Input | AXP2101 interrupt. |
| P6 / `EXIO6` | `QMI_INT1` | Input | QMI8658 INT1. |
| P7 / `EXIO7` | `GPS_RST` | Output | LC76G reset on the `-G` variant; optional on other variants. |

## I2S audio interface

| Audio signal | ESP32-S3 GPIO | Direction from MCU | Destination/source |
| --- | ---: | --- | --- |
| MCLK | 42 | Output | Shared by ES8311 and ES7210 |
| BCLK/SCLK | 9 | Output | Shared by ES8311 and ES7210 |
| LRCK/WS | 45 | Output | Shared by ES8311 and ES7210 |
| Playback data | 8 | Output | ES8311 DSDIN |
| Capture data | 10 | Input | ES7210 SDOUT1/TDMOUT |
| PA control | 46 | Control | Board amplifier-control circuit; managed by the BSP |

The maintained BSP supports ES8311 playback over standard I2S and ES7210 capture over four-slot TDM on the same physical clocks. Its voice profile is 24 kHz, 16-bit, stereo standard-I2S TX plus four-slot TDM RX with MCLK ×256. The ES7210 physical inputs are wired as follows:

- MIC1 and MIC2: the two onboard front microphones.
- MIC3: the ES8311 analog playback reference used by echo-processing software.
- MIC4: not connected.

The BSP serializes the four receive slots in the order MIC1, MIC3 (reference), MIC2, MIC4. Use the BSP channel masks rather than assuming that physical microphone numbering equals serialized slot numbering.

## TF card / SDMMC

| SD signal | GPIO | Current BSP use |
| --- | ---: | --- |
| CMD | 1 | 1-bit SDMMC command |
| CLK | 2 | 1-bit SDMMC clock |
| D0 | 3 | 1-bit SDMMC data |
| D3/CS (`SDCS`) | 41 | Wired, but not selected by the current 1-bit SDMMC mount |

The BSP configures D1 through D7 as not connected and does not declare a card-detect or write-protect GPIO. Do not repurpose GPIO1, GPIO2, or GPIO3 while the card is mounted. GPIO41 is the card's D3/CS signal, not a mechanical card-detect input.

## 8-pin expansion header

Pin numbering follows the schematic header `H2`.

| Header pin | Signal | Notes |
| ---: | --- | --- |
| 1 | VBUS | USB supply rail; observe power-sharing and backfeed requirements. |
| 2 | GND | Ground. |
| 3 | 3V3 | Board 3.3 V rail; verify current and external-supply requirements before use. |
| 4 | GPIO44 / U0RXD | UART0 receive into the ESP32-S3. |
| 5 | GPIO43 / U0TXD | UART0 transmit from the ESP32-S3. |
| 6 | GPIO17 | General GPIO; may be shared with LC76G RX on `-G`. |
| 7 | GPIO18 | General GPIO; may be shared with LC76G TX on `-G`. |
| 8 | GPIO16 | General GPIO. |

All GPIO signals use 3.3 V logic and are not 5 V tolerant. VBUS is a power rail, not a logic-level reference.

## Power, USB, display, and buttons

- The battery connector is intended for a single-cell 3.7 V lithium battery. Use the AXP2101 driver and the board power design for charging and telemetry.
- The PWR button is part of the AXP2101 power-control path; it is not listed as a free ESP32-S3 GPIO. The BOOT button is connected to GPIO0.
- GPIO19/GPIO20 are the native USB D-/D+ pair. Reusing them can disable USB flashing, USB Serial/JTAG, or application USB functions.
- The AMOLED has no separate GPIO-driven LED backlight. Brightness is controlled through CO5300 panel commands, so generic LCD backlight PWM examples do not apply.
- Display reset is GPIO39 and touch reset is GPIO40. They must not be treated as a shared reset line.

## Integration notes

1. Reserve every onboard-assigned GPIO before adding external peripherals. Pins shown on the expansion header may still be shared with console or GNSS functions.
2. On the `-G` version, confirm the fitted UART routing before using GPIO17/GPIO18 for another purpose, and coordinate LC76G reset through TCA9554 P7.
3. Share the existing I2C controller instead of installing multiple independent drivers on GPIO14/GPIO15. Check new peripherals for address conflicts.
4. Use GPIO42 for audio MCLK. GPIO16 is an expansion GPIO in the maintained BSP and board schematic.
5. Let the BSP manage ES8311, ES7210, the amplifier-control path, and their shared clocks. Directly toggling GPIO46 or TCA9554 P3 can conflict with codec lifecycle handling.
6. GPIO0 is a boot strap, and GPIO43/GPIO44 may be used for UART0. External circuits must not prevent boot or firmware recovery.
7. Do not drive VBUS or 3V3 from an external supply without accounting for backfeeding, regulation, and the AXP2101 power path.

## References

- [Repository schematic](Schematic/ESP32-S3-Touch-AMOLED-1.75-schematic.pdf)
- [Maintained ESP-IDF BSP pin definitions](firmware/brookesia/components/waveshare__esp32_s3_touch_amoled_1_75/include/bsp/esp32_s3_touch_amoled_1_75.h)
- [Maintained ESP-IDF BSP implementation](firmware/brookesia/components/waveshare__esp32_s3_touch_amoled_1_75/esp32_s3_touch_amoled_1_75.c)
- [AXP2101 ESP-IDF example](examples/esp-idf/01_AXP2101)
- [LC76G I2C Arduino example](examples/arduino/09_LC76G_I2C/09_LC76G_I2C.ino)
- [Official Waveshare documentation](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75)
- [Official Waveshare product page](https://www.waveshare.com/product/esp32-s3-touch-amoled-1.75.htm)
