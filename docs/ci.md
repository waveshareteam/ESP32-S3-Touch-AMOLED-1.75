# CI

The example workflow discovers build targets dynamically:

- ESP-IDF projects are discovered from `examples/esp-idf/*/CMakeLists.txt`.
- Arduino sketches are discovered from `.ino` files under `examples/arduino/`, excluding `examples/arduino/libraries/**`.

`workflow_dispatch` accepts `all`, an example directory name, or a repo-relative path. This allows maintainers to run the full matrix or a single example.

Current CI matrix pins were resolved from upstream release metadata on 2026-07-07:

- ESP-IDF `v5.5.4` and `v6.0.2`, target `esp32s3`.
- Arduino-ESP32 core `3.3.10`, FQBN `esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB`, using bundled libraries from `examples/arduino/libraries`.

Each successful ESP-IDF and Arduino matrix build uploads a flashable firmware artifact. Download the artifact zip from the workflow run, extract it, then run `flash.sh` or `flash.bat` with the board serial port.

The workflow uploads artifacts from first-party source examples only. Bundled library examples and released factory binaries are intentionally excluded from product CI.

If an example requires hardware, credentials, or an upstream component that is not yet compatible with a selected framework version, document the exclusion here before excluding it from CI.
