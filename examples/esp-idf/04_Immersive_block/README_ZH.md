# 沉浸式方块

> [English](README.md)

此 ESP-IDF 示例在 ESP32-S3-Touch-AMOLED-1.75 上渲染由运动控制的下落方块场景。

## 硬件

- ESP32-S3-Touch-AMOLED-1.75
- QSPI AMOLED 显示屏
- 电容触摸
- QMI8658 IMU

倾斜开发板即可控制场景。示例会初始化开发板显示和 I2C 总线、读取 QMI8658，并从独立应用任务更新 LVGL 界面。

## 支持版本

- ESP-IDF `v5.5.5`
- ESP-IDF `v6.0.2`
- 目标 `esp32s3`

## 构建与烧录

在仓库根目录且已激活 ESP-IDF 的环境中运行：

```bash
idf.py -C examples/esp-idf/04_Immersive_block \
  -B build/04_Immersive_block \
  set-target esp32s3 build

idf.py -C examples/esp-idf/04_Immersive_block \
  -B build/04_Immersive_block \
  -p PORT flash monitor
```

## 运行说明

显示更新使用有界锁等待和固定帧延迟。长时间渲染操作会让出系统任务，且每帧执行的工作量受限。更改动画密度或增加效果时应保留这些调度保护；无界渲染可能触发任务看门狗。

如需预编译镜像，请使用 GitHub Release 中匹配的 `04_Immersive_block` 软件包，并从 `0x0` 烧录其合并二进制文件。
