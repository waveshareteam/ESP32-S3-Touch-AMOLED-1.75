# 安全 AVI 播放器 2.0.0 覆盖层

[English](README.md)

本组件基于采用 Apache-2.0 许可证的 Espressif `espressif/avi_player` 2.0.0，
对应提交为 `61935c3499f63781d1392c3bfa8be4a46eaf0bd1`。

本地覆盖层保留公开的 2.0.0 API 和 ABI，同时修复文件后端的字节数处理、校验解析
与 seek 边界、使排队的 START 后立即 STOP 具有确定性，并在报告停止/反初始化完成
前关闭当前 `FILE`。`deinit` 会等待工作任务结束，再删除定时器、事件组、任务持有的
状态和缓冲区，因此返回后，调用者可以安全释放存储挂载租约。

仓库根目录的 `LICENSE` 包含 Apache License 2.0。

## 主机回归测试

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\firmware\brookesia\components\avi_player_safe\avi_player\tests\host\run_tests.ps1
```

测试会使用轻量、基于 pthread 的 ESP-IDF stub 编译生产代码 `avi_player.c`，并检查
立即 START/STOP、自然播放结束后反初始化、待处理 STOP 加反初始化、过大或截断的
文件头、模拟媒体读取失败，以及所有受跟踪的 `FILE` 是否均已关闭。
