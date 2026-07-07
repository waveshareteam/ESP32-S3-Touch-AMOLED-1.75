#!/usr/bin/env python3
"""Discover first-party examples for GitHub Actions matrices."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_idf_target(project: Path) -> str:
    defaults = project / "sdkconfig.defaults"
    if not defaults.exists():
        return "esp32s3"

    pattern = re.compile(r'^CONFIG_IDF_TARGET="?([^"\n]+)"?')
    for line in defaults.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1)
    return "esp32s3"


def discover_idf_projects() -> list[dict[str, str]]:
    root = REPO_ROOT / "examples" / "esp-idf"
    if not root.exists():
        return []

    projects: list[dict[str, str]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir():
            continue
        if not (child / "CMakeLists.txt").exists():
            continue
        projects.append(
            {
                "name": child.name,
                "path": repo_path(child),
                "target": read_idf_target(child),
            }
        )
    return projects


def discover_arduino_sketches() -> list[dict[str, str]]:
    root = REPO_ROOT / "examples" / "arduino"
    if not root.exists():
        return []

    sketches: list[dict[str, str]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or child.name == "libraries":
            continue
        ino_files = sorted(child.glob("*.ino"))
        if not ino_files:
            continue
        sketches.append(
            {
                "name": child.name,
                "path": repo_path(child),
                "sketch": repo_path(ino_files[0]),
            }
        )
    return sketches


def select_items(items: list[dict[str, str]], selection: str, kind: str) -> list[dict[str, str]]:
    selection = (selection or "all").strip()
    if selection == "all":
        return items

    normalized = selection.replace("\\", "/").strip("/")
    selected = [
        item
        for item in items
        if normalized in {item["name"], item["path"], item["path"].rstrip("/").split("/")[-1]}
    ]
    if selected:
        return selected

    valid = ", ".join(item["name"] for item in items) or "<none>"
    raise SystemExit(f"Unknown {kind} selection '{selection}'. Valid names: {valid}")


def write_github_output(outputs: dict[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        print(json.dumps(outputs, indent=2))
        return

    with Path(output_path).open("a", encoding="utf-8") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--idf-selection", default="all")
    parser.add_argument("--arduino-selection", default="all")
    args = parser.parse_args()

    idf_projects = select_items(discover_idf_projects(), args.idf_selection, "ESP-IDF project")
    arduino_sketches = select_items(
        discover_arduino_sketches(), args.arduino_selection, "Arduino sketch"
    )

    outputs = {
        "idf_projects": json.dumps(idf_projects, separators=(",", ":")),
        "arduino_sketches": json.dumps(arduino_sketches, separators=(",", ":")),
    }
    write_github_output(outputs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
