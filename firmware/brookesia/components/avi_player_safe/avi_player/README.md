# Safe AVI player 2.0.0 override

This component is derived from Espressif's Apache-2.0 licensed
`espressif/avi_player` 2.0.0 at commit
`61935c3499f63781d1392c3bfa8be4a46eaf0bd1`.

The local override keeps the public 2.0.0 API and ABI while fixing the file
backend's byte-count handling, validating parser and seek boundaries, making
queued START followed immediately by STOP deterministic, and closing the
active `FILE` before stop/deinit completion is reported. `deinit` waits for the
worker to finish before deleting the timer, event group, task-owned state, and
buffers, so callers can safely release their storage mount lease after it
returns.

The repository root `LICENSE` contains the Apache License 2.0.

## Host regression test

Run `tests/host/run_tests.ps1` from the repository root. The test compiles the
production `avi_player.c` against lightweight pthread-backed ESP-IDF stubs and
checks immediate START/STOP, natural end followed by deinit, pending STOP plus
deinit, oversized/truncated headers, simulated media-read failure, and that
every tracked `FILE` is closed.
