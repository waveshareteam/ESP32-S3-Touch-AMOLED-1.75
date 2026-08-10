# CST9217 触摸诊断

> [English](README.md)

此 Arduino 示例通过串口监视器报告原始 CST9217 触摸坐标，不会启动 AMOLED 显示或 LVGL。它将触摸控制器、I2C 总线、复位引脚和中断线与图形栈的其他部分隔离开来。

## 硬件

- ESP32-S3-Touch-AMOLED-1.75
- 板载 CST9217 触摸控制器
- 115200 波特率的 USB 串口连接

此开发板使用的 CST9217 驱动支持最多两个同时触摸点。

## 构建

使用 Arduino-ESP32 `3.3.10`、16 MB Flash、`app3M_fat9M_16MB` 分区方案和捆绑库：

```bash
arduino-cli compile \
  --fqbn "esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB" \
  --libraries examples/arduino/libraries \
  examples/arduino/10_Touch_CST9217
```

## 预期输出

初始化后，触摸面板会打印活动触点数量和原始坐标：

```text
Touch controller: CST9217
Supported touch points: 2
Reporting raw controller coordinates.
Touch points: 2
  Point 1: raw_x=120 raw_y=210
  Point 2: raw_x=338 raw_y=275
```

这些是控制器的原始坐标。LVGL 示例在使用触摸输入前会应用开发板的 `466 x 466` 边界和 XY 镜像，因此显示的坐标可能不同。

## 硬件验证

发布前请验证：

- 面板所有边缘的重复单指点击。
- 双指检测和坐标稳定性。
- 长按和快速连续触摸。
- 长时间运行中稳定的中断处理。
