# Changelog

[简体中文](CHANGELOG_ZH.md)

All notable repository and firmware changes are documented here.

## [Unreleased]

### Added

- Board-specific CST9217 raw single- and two-point touch diagnostic under
  `examples/arduino/10_Touch_CST9217/`.
- Equivalent English and Simplified Chinese repository guides, board-level hardware references,
  user and maintainer documentation, release notes, and public collaboration guidance.
- An official Waveshare product image with source and checksum provenance for the repository landing pages.

## [1.0.1] - 2026-07-13

### Added

- CI coverage for all first-party examples on ESP-IDF v5.5.4, ESP-IDF v6.0.2, and Arduino-ESP32
  3.3.10.
- Combined firmware images, split and combined flash helpers, package manifests, and release-level
  SHA256 metadata.
- Getting started, example catalog, CI, firmware, release, and troubleshooting documentation.
- GitHub contribution, support, security, issue, and pull request templates.

### Changed

- Normalized first-party examples under `examples/esp-idf/` and `examples/arduino/`.
- Renamed the LC76G Arduino example to `09_LC76G_I2C`.
- Updated ESP-IDF projects for v5.5 and v6 compatibility and current managed components.
- Configured source-built firmware for the board's 16 MB flash layout.

### Fixed

- Reduced per-frame work and bounded display-lock waits in `04_Immersive_block` to prevent watchdog
  resets.
- Corrected `05_Spec_Analyzer` firmware configuration that could advertise a 32 MB image on 16 MB
  hardware.
- Stabilized display locking and runtime behavior across the validated example set.

[Unreleased]: https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/releases/tag/v1.0.1
