# 持续集成

[English](ci.md)

`Build Examples` 工作流会先运行始终可见的质量与路由门禁，然后发现、构建并打包由完整改动文件分类
选中的第一方示例。GitHub Release 中的示例固件来自该工作流，不通过手工方式编译后发布。

## 质量与路由门禁

每个 Pull Request 都会运行仓库本地单元测试、严格的完整 Markdown 审计和支持重命名的改动文件分类器。
检出包含完整历史，因此当差异为空或不可用时分类器会失败关闭。根目录、示例、草图和捆绑库的 Markdown
不会选择示例构建；直接示例源码只选择对应工程或草图；共享输入和真实全局构建输入会选择适用的完整
surface。`firmware/**` 会按文件类型报告，但默认不进入示例矩阵。

工作流使用以 Pull Request 或分支为范围的并发组，并取消过时的 PR 或分支运行。标签运行会保留，以覆盖发布。

## 发现边界

- ESP-IDF 工程是 `examples/esp-idf/` 下包含 `CMakeLists.txt` 的直接子目录。
- Arduino 示例是 `examples/arduino/` 下包含顶层 `.ino` 文件的直接子目录。
- `examples/arduino/libraries/**`、本地组件示例与 `firmware/**` 均被排除。独立工程
  `firmware/brookesia/` 使用 ESP-IDF 5.5 手动构建。

手动运行工作流时，选择器支持 `all`、示例目录名或仓库相对路径。

## 已验证矩阵

以下版本已于 2026-08-10 依据上游发布重新核验：

| 框架 | 版本 | 示例数 | 固件产物数 |
| --- | --- | ---: | ---: |
| ESP-IDF | `v5.5.4` | 5 | 5 |
| ESP-IDF | `v6.0.2` | 5 | 5 |
| Arduino-ESP32 | `3.3.10` | 10 | 10 |

ESP-IDF 目标为 `esp32s3`。Arduino 使用
`esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB` 与仓库捆绑库。

完整发布运行包含 1 个质量/路由任务、2 个发现任务和 20 个构建/打包任务（5 个 ESP-IDF 工程 × 2 个
ESP-IDF 版本，另加 10 个 Arduino 草图）。矩阵任务不启用 fail-fast，因此单个失败不会隐藏其他示例的结果。
v1.0.1 标签早于 `10_Touch_CST9217`，当时生成 19 个固件包。

## 产物约定

每个成功构建会上传一个 `*-combined.zip`，其中包含：

- `bin/` 下按偏移地址组织的原始二进制文件。
- 从 `0x0` 烧录的单个 `bin/<artifact-name>-combined.bin`。
- 记录框架、版本、工程、目标、Git SHA、文件大小和 SHA-256 的 `manifest.json`。
- `flash_combined.sh`、`flash_combined.bat` 与 `flash_combined_args.txt`。
- 用于分区镜像烧录的 `flash.sh`、`flash.bat` 与 `flash_args.txt`。
- 软件包 README。

打包器会拒绝二进制区域重叠。合并镜像以 `0xFF` 填充未使用地址间隙，并按 ESP-IDF 或
Arduino 提供的偏移地址保留每个二进制文件。

## 版本策略

CI 跟踪 ESP-IDF v5.5 分支的最新稳定补丁、最新稳定 ESP-IDF v6，以及本仓库支持的最新稳定
Arduino-ESP32。更新版本时应同时完成：

1. 上游 Release 与迁移指南审查。
2. 完整矩阵 CI。
3. 受影响示例的实机验证。
4. 文档与发布说明更新。

## 发布门禁

只有满足以下条件才可发布：

1. Pull Request 的 20 个构建/打包任务全部成功。
2. 完成实机验证。
3. Pull Request 已合并，Release 标签指向合并后的提交。
4. 标签触发的 CI 成功。
5. 标签工作流中的全部压缩包通过 `prepare_release_assets.py` 校验。
6. GitHub Release 包含 20 个 combined ZIP 与 `manifest-combined-assets.json`。

维护命令见[发布脚本](../releases/README_ZH.md)。
