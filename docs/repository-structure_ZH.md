# 仓库结构

[English](repository-structure.md)

本仓库使用稳定的框架根目录，便于一致地发现示例、CI、文档与发布产物。

## 标准路径

- `README.md` 与 `README_ZH.md`：内容等价的英文和简体中文仓库说明。
- `HARDWARE_REFERENCE.md` 与 `HARDWARE_REFERENCE_ZH.md`：中英双语板级硬件参考。
- `assets/`：文档使用的官方产品图片。
- `examples/esp-idf/`：5 个第一方 ESP-IDF 工程。
- `examples/arduino/`：10 个第一方 Arduino 示例。
- `examples/arduino/libraries/`：Arduino 示例使用的捆绑依赖。
- `config/`：共用 ESP-IDF 兼容配置。
- `docs/`：配置、示例、CI、组件、固件与故障排查文档。
- `releases/`：固件打包、下载和 Release 暂存工具。
- `firmware/`：通过源码维护的 Brookesia 固件与工厂恢复镜像。
- `Schematic/`：硬件原理图资料。
- `.github/`：GitHub Actions 与公开协作模板。

## 命名约定

第一方示例使用两位数字序号加描述性名称，例如 `04_Immersive_block` 或
`09_LC76G_I2C`。新示例应遵循同一约定，并保持为对应框架根目录的直接子目录。

不得恢复 `examples/ESP-IDF-v5.5/`、`examples/Arduino-v3.3.5/` 等历史版本目录。框架版本
应记录在 CI 配置与 Release 元数据中，而不应写入目录名称。

## CI 发现边界

CI 只发现：

- `examples/esp-idf/` 下包含 `CMakeLists.txt` 的直接子目录。
- `examples/arduino/` 下包含顶层 `.ino` 文件的直接子目录。

捆绑库与本地组件中的示例属于上游样例，不是产品固件目标。`firmware/brookesia/` 是发现边界外
的独立源码工程；工厂二进制属于发布产物，不是源码构建输入。

## 生成文件边界

构建目录、managed components、依赖锁、下载产物和 Release 暂存输出均被忽略。公开示例固件
必须由 CI 从带标签的提交构建，并在上传前完成校验。
