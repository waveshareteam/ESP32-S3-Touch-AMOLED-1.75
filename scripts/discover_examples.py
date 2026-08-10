#!/usr/bin/env python3
"""Discover first-party examples for GitHub Actions matrices."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = "esp32s3"


def repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_idf_target(project: Path) -> str:
    defaults = project / "sdkconfig.defaults"
    if not defaults.exists():
        return DEFAULT_TARGET

    pattern = re.compile(r'^CONFIG_IDF_TARGET="?([^"\n]+)"?')
    for line in defaults.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1)
    return DEFAULT_TARGET


def discover_idf_projects() -> list[dict[str, str]]:
    root = REPO_ROOT / "examples" / "esp-idf"
    if not root.exists():
        return []

    projects: list[dict[str, str]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or not (child / "CMakeLists.txt").exists():
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


def select_items(
    items: list[dict[str, str]], selector: str, kind: str, allow_empty: bool = False
) -> list[dict[str, str]]:
    selector = (selector or "all").strip()
    if selector == "all":
        return items

    normalized = selector.replace("\\", "/").strip("/")
    selected = [
        item
        for item in items
        if normalized in {
            item["name"],
            item["path"],
            item["path"].rstrip("/").split("/")[-1],
            item.get("sketch", ""),
        }
    ]
    if selected:
        return selected
    if allow_empty:
        return []

    valid = ", ".join(item["name"] for item in items) or "<none>"
    raise SystemExit(f"Unknown {kind} selector '{selector}'. Valid names: {valid}")


def selectors_from_json(value: str | None, kind: str) -> list[str] | None:
    if value is None:
        return None
    try:
        selectors = json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {kind} selectors JSON: {exc.msg}") from exc
    if not isinstance(selectors, list) or not all(isinstance(item, str) for item in selectors):
        raise SystemExit(f"{kind} selectors JSON must be an array of strings")
    return selectors


def select_routed_items(
    items: list[dict[str, str]], selectors: list[str] | None, kind: str, allow_empty: bool
) -> list[dict[str, str]]:
    if selectors is None:
        return items
    known = {item["path"] for item in items}
    unknown = sorted(set(selectors) - known)
    if unknown:
        raise SystemExit(f"Unknown routed {kind} path(s): {', '.join(unknown)}")
    selected = [item for item in items if item["path"] in selectors]
    if not selected and not allow_empty:
        raise SystemExit(f"Routed {kind} selection is empty; pass --allow-empty only for a verified no-build route")
    return selected


def expand_idf_matrix(items: list[dict[str, str]], idf_versions: str) -> list[dict[str, str]]:
    versions = [item.strip() for item in idf_versions.split(",") if item.strip()]
    return [{**project, "idf": version} for project in items for version in versions]


def expand_arduino_matrix(
    items: list[dict[str, str]], arduino_core: str, fqbn: str
) -> list[dict[str, str]]:
    return [{**sketch, "core": arduino_core, "fqbn": fqbn} for sketch in items]


def write_outputs(matrix: list[dict[str, str]], github_output: str | None) -> None:
    payload = {
        "matrix": json.dumps({"include": matrix}, separators=(",", ":")),
        "count": str(len(matrix)),
    }
    if not github_output:
        print(json.dumps(payload, indent=2))
        return

    with Path(github_output).open("a", encoding="utf-8") as handle:
        for key, value in payload.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", choices=("esp-idf", "arduino"), required=True)
    parser.add_argument("--selector", default="all")
    parser.add_argument("--selectors-json", help="compact JSON array of routed repository-relative paths")
    parser.add_argument("--allow-empty", action="store_true", help="permit a verified no-build routed selection")
    parser.add_argument("--idf-versions", default="v5.5.4,v6.0.2")
    parser.add_argument("--arduino-core", default="3.3.10")
    parser.add_argument(
        "--fqbn",
        default="esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB",
    )
    parser.add_argument("--github-output")
    args = parser.parse_args()

    if args.surface == "esp-idf":
        items = select_routed_items(
            discover_idf_projects(), selectors_from_json(args.selectors_json, "ESP-IDF project"),
            "ESP-IDF project", args.allow_empty,
        )
        items = select_items(items, args.selector, "ESP-IDF project", args.allow_empty)
        matrix = expand_idf_matrix(items, args.idf_versions)
    else:
        items = select_routed_items(
            discover_arduino_sketches(), selectors_from_json(args.selectors_json, "Arduino sketch"),
            "Arduino sketch", args.allow_empty,
        )
        items = select_items(items, args.selector, "Arduino sketch", args.allow_empty)
        matrix = expand_arduino_matrix(items, args.arduino_core, args.fqbn)

    write_outputs(matrix, args.github_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
