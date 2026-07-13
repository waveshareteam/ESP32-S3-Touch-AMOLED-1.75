# Repository Structure

The repository uses stable framework roots so examples, CI, documentation, and releases can be
discovered consistently.

## Canonical Paths

- `examples/esp-idf/`: five first-party ESP-IDF projects.
- `examples/arduino/`: ten first-party Arduino sketches.
- `examples/arduino/libraries/`: bundled dependencies used by those sketches.
- `config/`: shared ESP-IDF compatibility overlays.
- `docs/`: setup, example, CI, component, firmware, and troubleshooting documentation.
- `releases/`: firmware packaging, download, and release staging helpers.
- `firmware/`: factory recovery firmware.
- `Schematic/`: hardware schematic material.
- `.github/`: GitHub Actions and public collaboration templates.

## Naming Convention

First-party examples use a two-digit sequence followed by a descriptive name, such as
`04_Immersive_block` or `09_LC76G_I2C`. New examples should follow the same convention and remain
direct children of the appropriate framework root.

Historical versioned roots such as `examples/ESP-IDF-v5.5/` and
`examples/Arduino-v3.3.5/` must not be restored. Framework versions belong in CI configuration and
release metadata, not directory names.

## CI Discovery Boundary

CI discovers only:

- Direct children of `examples/esp-idf/` containing `CMakeLists.txt`.
- Direct children of `examples/arduino/` containing a top-level `.ino` file.

Examples inside bundled libraries and local components are upstream samples, not product firmware
targets. Factory binaries are released artifacts and are not source build inputs.

## Generated Output Boundary

Build directories, managed components, dependency locks, downloaded artifacts, and release staging
output are ignored. Published example firmware must be built by CI from a tagged commit and validated
before upload.
