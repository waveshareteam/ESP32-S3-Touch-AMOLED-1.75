# 发布脚本

[English](README.md)

本目录中的脚本用于打包 CI 构建输出、下载工作流产物、验证合并固件，并暂存 GitHub Release
待发布文件。

正式发布的固件必须来自成功的标签工作流。以下命令可用于开发和验证脚本，但本地固件构建
不能直接作为 Release 输入。

## 软件包内容

`package_firmware.py` 读取框架构建输出，并生成 `<artifact-name>-combined.zip`，其中包含：

- `bin/` 下按原始偏移地址烧录的二进制文件。
- 从 `0x0` 烧录的 `bin/<artifact-name>-combined.bin`。
- 适用于 Shell 和 Windows 的分区镜像与合并镜像烧录脚本。
- 分区镜像与合并镜像的命令文本文件。
- 包含源码、版本、偏移地址、文件大小和 SHA256 校验值的 `manifest.json`。
- 软件包 README。

对于 ESP-IDF，偏移地址和 esptool 参数来自 `flasher_args.json`。对于 Arduino，优先使用导出的
`.merged.bin`；若不存在，则按标准 ESP32-S3 二进制布局推导。

## 打包 ESP-IDF 构建

```bash
python3 releases/package_firmware.py \
  --framework esp-idf \
  --project examples/esp-idf/02_lvgl_demo_v9 \
  --build-dir build/02_lvgl_demo_v9-v6.0.2 \
  --name ESP32-S3-Touch-AMOLED-1.75-02_lvgl_demo_v9-v6.0.2 \
  --framework-version v6.0.2 \
  --target esp32s3 \
  --git-sha <git-sha> \
  --output-dir release-artifacts
```

## 打包 Arduino 构建

```bash
python3 releases/package_firmware.py \
  --framework arduino \
  --project examples/arduino/01_HelloWorld \
  --build-dir build/01_HelloWorld-3.3.10 \
  --name ESP32-S3-Touch-AMOLED-1.75-01_HelloWorld-arduino-3.3.10 \
  --framework-version 3.3.10 \
  --target esp32s3 \
  --git-sha <git-sha> \
  --output-dir release-artifacts
```

## 下载 CI 产物

下载已完成工作流运行中的全部固件，并保留内部的合并 ZIP 文件：

```bash
python3 releases/download_artifacts.py \
  --run-id <run-id> \
  --keep-archives \
  --clean
```

省略 `--run-id` 时，下载器会选择当前分支最近一次成功的 `examples.yml` 运行。使用
`--artifact <name>` 可下载单个产物，使用 `--pattern "firmware-esp-idf-*"` 可下载指定子集。

产物会解压到 `releases/downloads/run-<run-id>/`。身份验证使用环境变量 `GH_TOKEN`、
`GITHUB_TOKEN`，或当前已登录的 GitHub CLI。不要把 Token 写入命令、文档或仓库文件。

## 暂存 Release

标签工作流成功后，验证并暂存全部 20 个固件压缩包：

```bash
python3 releases/prepare_release_assets.py \
  --input-dir releases/downloads/run-<run-id> \
  --output-dir releases/dist/vX.Y.Z \
  --version vX.Y.Z \
  --git-sha <tag-commit-sha> \
  --expected-count 20 \
  --clean
```

脚本会拒绝缺少合并镜像、偏移地址错误、校验值不匹配、产物名称重复、Git SHA 混用或压缩包
数量异常的输入。验证通过后，脚本会复制 ZIP 文件并生成
`manifest-combined-assets.json`。

将 20 个 ZIP 文件、合并产物清单和对应的发布说明上传到 GitHub Release。历史 v1.0.1 标签
早于 `10_Touch_CST9217`，因此只包含 19 个固件 ZIP 文件。
