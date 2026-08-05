# 变更记录

[English](CHANGELOG.md)

本文件记录仓库与固件的主要变更。

## [未发布]

### 新增

- 新增 Brookesia Button Test 出厂测试应用：从 TCA9554 EXIO4 读取整形后的 PWR
  状态、从 GPIO0 读取 BOOT 状态，显示实时电平并锁存通过结果，不依赖 AXP2101
  按键寄存器。
- 在 `examples/arduino/10_Touch_CST9217/` 新增本板专用的 CST9217 原始单点、双点触摸诊断示例。
- 增加内容等价的中英文仓库说明、板级硬件参考、用户与维护者文档、发布说明和公开协作指南。
- 在 `firmware/` 下增加独立配对的中英文固件交付、素材制作、硬件验收与本地组件说明。
- 增加用于仓库首页的 Waveshare 官方产品图，并记录素材来源与校验值。

### 修复

- 恢复首页快捷入口的语义图标，以及全部主要章节的 emoji 前缀，使其与既有 Waveshare
  仓库风格一致。

## [1.0.1] - 2026-07-13

### 新增

- 对全部第一方示例提供 ESP-IDF v5.5.4、ESP-IDF v6.0.2 和 Arduino-ESP32 3.3.10 的 CI 覆盖。
- 增加合并固件、分区与合并烧录脚本、软件包 manifest 和 Release 级 SHA-256 元数据。
- 增加快速开始、示例目录、CI、固件、发布与故障排查文档。
- 增加 GitHub 贡献、支持、安全、Issue 与 Pull Request 模板。

### 变更

- 将第一方示例统一整理到 `examples/esp-idf/` 和 `examples/arduino/`。
- 将 LC76G Arduino 示例重命名为 `09_LC76G_I2C`。
- 更新 ESP-IDF 工程，使其兼容 v5.5、v6 与当前 managed components。
- 将源码构建固件配置为本板的 16 MB Flash 布局。

### 修复

- 降低 `04_Immersive_block` 单帧工作量并限制显示锁等待，避免看门狗复位。
- 修正 `05_Spec_Analyzer` 固件配置，避免在 16 MB 硬件上声明 32 MB 镜像。
- 稳定已验证示例集的显示锁与运行行为。

[未发布]: https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/tag/v1.0.1
