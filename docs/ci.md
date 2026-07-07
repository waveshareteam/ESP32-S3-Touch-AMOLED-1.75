# CI

GitHub Actions validate this repository through CI. Local compilation is not required to certify repository changes.

## Version Matrix

The current workflow pins were resolved from upstream release metadata on 2026-07-07:

- ESP-IDF `v5.5.4`
- ESP-IDF `v6.0.2`
- Arduino-ESP32 `3.3.10`

Update these pins deliberately after checking upstream release notes and migration guides.

## ESP-IDF

ESP-IDF CI discovers first-party projects under `examples/esp-idf/` and builds each project for `esp32s3` with both selected ESP-IDF versions.

The workflow uses the official ESP-IDF CI action and each example's own project directory. Generated `build/`, `managed_components/`, `dependencies.lock`, and `sdkconfig` files remain ignored.

## Arduino

Arduino CI discovers first-party sketches under `examples/arduino/` and compiles them with Arduino-ESP32 `3.3.10`.

The workflow uses bundled libraries from `examples/arduino/libraries/`. Examples inside bundled libraries are intentionally excluded from product CI.

## Manual Dispatch

Use workflow dispatch inputs to narrow a run:

- `all` builds all discovered examples.
- A directory name builds that one example, such as `02_lvgl_demo_v9`.
- A repo-relative path builds that one example, such as `examples/arduino/01_Hello_world`.

## Firmware Artifacts

The current CI workflow is compile-validation focused. It does not publish source-built firmware archives yet. Add release packaging only after the source examples are green in CI and the repository needs downloadable flashable artifacts.
