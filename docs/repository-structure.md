# Repository Structure

The repository uses a stable product layout so examples, CI, and documentation can be discovered consistently.

## Canonical Paths

- `examples/esp-idf/` contains first-party ESP-IDF projects.
- `examples/arduino/` contains first-party Arduino sketches.
- `examples/arduino/libraries/` contains bundled Arduino libraries used by those sketches.
- `config/` is reserved for shared ESP-IDF overlays.
- `docs/` contains maintainer and user-facing notes.
- `.github/` contains CI and collaboration templates.
- `Firmware/` contains released factory flashing and recovery binaries.
- `Schematic/` contains hardware schematic material.

## Compatibility Paths

The old versioned example roots are retained with README notes only:

- `examples/ESP-IDF-v5.5/`
- `examples/Arduino-v3.3.5/`

Do not add new source projects under those compatibility paths. New examples should use `examples/esp-idf/` or `examples/arduino/`.

## CI Discovery Boundary

CI discovers only first-party examples:

- Direct child directories of `examples/esp-idf/` that contain `CMakeLists.txt`.
- Direct child directories of `examples/arduino/` that contain a top-level `.ino` file.

Examples inside bundled libraries are excluded from product CI unless the repository intentionally adds a separate library CI workflow.
