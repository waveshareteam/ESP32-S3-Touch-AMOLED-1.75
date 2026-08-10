#!/usr/bin/env python3
"""Audit example-CI routing for a Waveshare ESP32-family repository.

The script is a deterministic routing oracle for repository maintenance and a
candidate implementation for repository-local change classification.  It reads
a complete changed-file scope, discovers first-party examples through
``inventory_repo.py``, and reports which ESP-IDF projects or Arduino sketches
need the expensive build matrix.  It never builds projects or edits the target
repository.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

from audit_markdown import (
    AuditError,
    Change,
    changes_from_base,
    changes_from_file,
    changes_from_worktree,
    load_config as load_ownership_config,
    posix_path,
    require_clean_base_checkout,
)
from inventory_repo import make_inventory


DEFAULT_CONFIG = {
    # Narrow exceptions evaluated before documentation rules.  Use only when a
    # Markdown-looking or documentation-asset path is a real build input.
    "build_override_patterns": [],
    # Markdown is documentation regardless of where it is nested.  This order
    # prevents an example/library README from selecting a build target merely
    # because its parent directory contains source.
    "documentation_patterns": ["*.md", "**/*.md"],
    "documentation_asset_patterns": [
        "docs/*.gif", "docs/**/*.gif",
        "docs/*.jpeg", "docs/**/*.jpeg",
        "docs/*.jpg", "docs/**/*.jpg",
        "docs/*.pdf", "docs/**/*.pdf",
        "docs/*.png", "docs/**/*.png",
        "docs/*.svg", "docs/**/*.svg",
        "docs/*.webp", "docs/**/*.webp",
    ],
    # These files are not documentation-only, but they should not start product
    # example builds unless a repository adds a narrower positive rule.
    "ignore_build_patterns": [
        ".github/ISSUE_TEMPLATE/**",
        ".github/PULL_REQUEST_TEMPLATE/**",
        "CODE_OF_CONDUCT*",
        "CONTRIBUTING*",
        "LICENSE*",
        "SECURITY*",
        "SUPPORT*",
    ],
    # Firmware is an explicitly separate maintenance surface.  Source changes
    # here are reported, never silently fed into the default examples matrix.
    "firmware_patterns": ["firmware/**"],
    # Conventional shared roots.  Repositories can extend these with an optional
    # JSON config; no current product or example name is encoded here.
    "esp_idf_shared_patterns": [
        "examples/esp-idf/common/**",
        "examples/esp-idf/components/**",
    ],
    "arduino_shared_patterns": [
        "examples/arduino/common/**",
        "examples/arduino/libraries/**",
    ],
    "esp_idf_global_patterns": [
        "CMakeLists.txt",
        "idf_component.yml",
        "sdkconfig*",
        "partitions*.csv",
        "config/*.cmake", "config/**/*.cmake",
        "config/*.defaults", "config/**/*.defaults",
        "config/*.h", "config/**/*.h",
    ],
    "arduino_global_patterns": ["platformio.ini"],
    # Workflow changes can alter the toolchain, matrix, or build command.  A
    # repository may put a known docs-only workflow in ignore_build_patterns.
    "global_build_patterns": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
}

CONFIG_KEYS = set(DEFAULT_CONFIG)
BINARY_SUFFIXES = {".bin"}
ARCHIVE_SUFFIXES = {".zip", ".7z", ".tar", ".tgz", ".gz", ".xz", ".bz2"}


class RoutingError(RuntimeError):
    """Operational or configuration error (exit code 2)."""


@dataclass(frozen=True)
class PathRoute:
    path: str
    status: str
    kind: str
    reason: str


def matches(path: str, patterns: Iterable[str]) -> bool:
    normalized = posix_path(path).strip("/")
    return any(
        fnmatch.fnmatchcase(normalized, posix_path(pattern).strip("/"))
        for pattern in patterns
    )


def validate_pattern(pattern: str, label: str) -> str:
    normalized = posix_path(pattern.strip())
    if not normalized or re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("/"):
        raise RoutingError(f"{label} entries must be repository-relative patterns: {pattern!r}")
    if ".." in PurePosixPath(normalized.replace("*", "placeholder")).parts:
        raise RoutingError(f"{label} entries must not escape the repository: {pattern!r}")
    return normalized


def load_routing_config(path: Path | None) -> dict[str, list[str]]:
    config = copy.deepcopy(DEFAULT_CONFIG)
    if path is None:
        return config
    try:
        user = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingError(f"cannot read JSON routing config {path}: {exc}") from exc
    if not isinstance(user, dict):
        raise RoutingError("routing config root must be a JSON object")
    unknown = sorted(set(user) - CONFIG_KEYS)
    if unknown:
        raise RoutingError("unknown routing config keys: " + ", ".join(unknown))
    for key, value in user.items():
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise RoutingError(f"routing config key {key!r} must contain strings")
        config[key].extend(validate_pattern(item, key) for item in value)
    return config


def validate_changes(changes: Sequence[Change]) -> None:
    if not changes:
        raise RoutingError(
            "changed-file scope is empty; obtain a complete base/head diff instead of "
            "treating missing change data as all examples or as a pass"
        )
    for change in changes:
        for raw in (change.path, change.old_path):
            if raw is None:
                continue
            normalized = posix_path(raw)
            pure = PurePosixPath(normalized)
            if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", normalized):
                raise RoutingError(f"changed path must be repository-relative: {raw!r}")


def impact_paths(change: Change) -> list[str]:
    paths = [posix_path(change.path)]
    if change.status == "R" and change.old_path:
        paths.append(posix_path(change.old_path))
    return paths


def path_is_within(path: str, root: str) -> bool:
    normalized = posix_path(path).strip("/")
    normalized_root = posix_path(root).strip("/")
    if normalized_root in {"", "."}:
        return True
    return normalized == normalized_root or normalized.startswith(normalized_root + "/")


def route_changes(
    root: Path,
    changes: Sequence[Change],
    routing_config: dict[str, list[str]],
    ownership_config: dict,
    *,
    max_files: int,
    max_text_files: int,
) -> dict:
    root = root.resolve()
    validate_changes(changes)
    inventory = make_inventory(
        root,
        max_files=max_files,
        max_text_files=max_text_files,
        policy_config=ownership_config,
    )
    if inventory["scan_truncated"]:
        raise RoutingError(
            "repository inventory was truncated; raise --max-files before trusting CI routing"
        )

    idf_projects = sorted(inventory["example_ci_idf_projects"])
    arduino_sketches = sorted(inventory["arduino_sketches"])
    arduino_roots = {
        sketch: posix_path(PurePosixPath(sketch).parent)
        for sketch in arduino_sketches
    }

    selected_idf: set[str] = set()
    selected_arduino: set[str] = set()
    all_idf = False
    all_arduino = False
    docs_only = True
    firmware_touched = False
    release_review_required = False
    unknown_paths: set[str] = set()
    routes: list[PathRoute] = []

    def add_route(path: str, status: str, kind: str, reason: str) -> None:
        routes.append(PathRoute(path=path, status=status, kind=kind, reason=reason))

    for change in changes:
        for path in impact_paths(change):
            suffix = PurePosixPath(path).suffix.lower()
            in_firmware = matches(path, routing_config["firmware_patterns"])
            build_override = matches(path, routing_config["build_override_patterns"])
            if in_firmware:
                firmware_touched = True

            if not build_override and matches(path, routing_config["documentation_patterns"]):
                add_route(path, change.status, "documentation", "documentation pattern")
                continue
            if not build_override and matches(path, routing_config["documentation_asset_patterns"]):
                add_route(path, change.status, "documentation_asset", "documentation asset pattern")
                continue

            docs_only = False
            if in_firmware:
                if suffix in BINARY_SUFFIXES | ARCHIVE_SUFFIXES:
                    release_review_required = True
                    kind = "firmware_delivery_artifact"
                    reason = "firmware delivery surface is outside default example CI"
                else:
                    kind = "firmware_source_or_config"
                    reason = "firmware maintenance is outside default example CI"
                add_route(path, change.status, kind, reason)
                continue
            if matches(path, routing_config["ignore_build_patterns"]):
                add_route(path, change.status, "non_build", "configured non-build pattern")
                continue

            direct_idf = [project for project in idf_projects if path_is_within(path, project)]
            if direct_idf:
                selected_idf.update(direct_idf)
                add_route(path, change.status, "esp_idf_project", "changed first-party ESP-IDF project")
                continue

            direct_arduino = [
                sketch for sketch, sketch_root in arduino_roots.items()
                if path_is_within(path, sketch_root)
            ]
            if direct_arduino:
                selected_arduino.update(direct_arduino)
                add_route(path, change.status, "arduino_sketch", "changed first-party Arduino sketch")
                continue

            if matches(path, routing_config["esp_idf_shared_patterns"]):
                all_idf = bool(idf_projects)
                add_route(path, change.status, "esp_idf_shared", "shared ESP-IDF input")
                continue
            if matches(path, routing_config["arduino_shared_patterns"]):
                all_arduino = bool(arduino_sketches)
                add_route(path, change.status, "arduino_shared", "shared Arduino input")
                continue
            if matches(path, routing_config["global_build_patterns"]):
                all_idf = bool(idf_projects)
                all_arduino = bool(arduino_sketches)
                add_route(path, change.status, "global_build", "global workflow or build input")
                continue
            if matches(path, routing_config["esp_idf_global_patterns"]):
                all_idf = bool(idf_projects)
                add_route(path, change.status, "esp_idf_global", "global ESP-IDF build input")
                continue
            if matches(path, routing_config["arduino_global_patterns"]):
                all_arduino = bool(arduino_sketches)
                add_route(path, change.status, "arduino_global", "global Arduino build input")
                continue

            if suffix in BINARY_SUFFIXES | ARCHIVE_SUFFIXES:
                release_review_required = True
                add_route(
                    path,
                    change.status,
                    "release_artifact",
                    "binary/archive change requires release review, not default example CI",
                )
                continue

            # A complete but unfamiliar non-document path is conservatively
            # build-impacting.  This is distinct from an incomplete diff, which
            # is an operational error and never becomes a silent fallback-all.
            unknown_paths.add(path)
            all_idf = bool(idf_projects)
            all_arduino = bool(arduino_sketches)
            add_route(path, change.status, "unknown_build_impact", "unclassified non-document path")

    if all_idf:
        selected_idf = set(idf_projects)
    if all_arduino:
        selected_arduino = set(arduino_sketches)

    def framework_report(all_selected: bool, selected: set[str], available: list[str]) -> dict:
        if all_selected:
            mode = "all"
        elif selected:
            mode = "selected"
        else:
            mode = "none"
        return {
            "mode": mode,
            "selected": sorted(selected),
            "available": available,
        }

    return {
        "schema_version": 1,
        "repository": root.name,
        "scope": {
            "changed_files": len(changes),
            "impact_paths": len(routes),
            "docs_only": docs_only,
            "example_build_required": bool(selected_idf or selected_arduino),
            "firmware_touched": firmware_touched,
            "release_review_required": release_review_required,
        },
        "esp_idf": framework_report(all_idf, selected_idf, idf_projects),
        "arduino": framework_report(all_arduino, selected_arduino, arduino_sketches),
        "unknown_paths": sorted(unknown_paths),
        "routes": [asdict(item) for item in routes],
    }


def print_text(report: dict) -> None:
    scope = report["scope"]
    print(f"CI routing audit: {report['repository']}")
    print(
        "Scope: "
        f"changed_files={scope['changed_files']} docs_only={scope['docs_only']} "
        f"build_required={scope['example_build_required']} "
        f"firmware_touched={scope['firmware_touched']} "
        f"release_review={scope['release_review_required']}"
    )
    for framework in ("esp_idf", "arduino"):
        data = report[framework]
        print(
            f"{framework}: mode={data['mode']} "
            f"selected={len(data['selected'])} available={len(data['available'])}"
        )
        for item in data["selected"]:
            print(f"  - {item}")
    for item in report["routes"]:
        print(f"[{item['kind']}] {item['status']} {item['path']}: {item['reason']}")
    if report["unknown_paths"]:
        print("Unknown non-document paths (conservatively routed to all available examples):")
        for path in report["unknown_paths"]:
            print(f"  - {path}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit docs-only and example-build routing from a complete changed-file scope."
    )
    parser.add_argument("repo", type=Path, help="repository checkout to inspect")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--base", help="route files changed from merge-base(BASE, HEAD)")
    source.add_argument("--working-tree", action="store_true", help="route staged, unstaged, and untracked files")
    source.add_argument("--changed-files-from", type=Path, help="read paths or git name-status lines from a UTF-8 file")
    parser.add_argument("--routing-config", type=Path, help="optional JSON routing-pattern extension")
    parser.add_argument("--ownership-config", type=Path, help="optional Markdown/inventory ownership policy")
    parser.add_argument("--strict-unknown", action="store_true", help="fail when a non-document path needs conservative all-example routing")
    parser.add_argument("--expect-docs-only", action="store_true", help="fail unless every impact path is documentation/documentation assets")
    parser.add_argument("--expect-no-example-builds", action="store_true", help="fail if any ESP-IDF or Arduino example is selected")
    parser.add_argument("--max-files", type=int, default=50_000)
    parser.add_argument("--max-text-files", type=int, default=2_000)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    if not args.repo.is_dir():
        print(f"error: repository path does not exist or is not a directory: {args.repo}", file=sys.stderr)
        return 2
    try:
        root = args.repo.resolve()
        routing_config = load_routing_config(args.routing_config)
        ownership_config = load_ownership_config(args.ownership_config)
        if args.base:
            require_clean_base_checkout(root)
            changes = changes_from_base(root, args.base)
        elif args.working_tree:
            changes = changes_from_worktree(root)
        else:
            changes = changes_from_file(args.changed_files_from)
        report = route_changes(
            root,
            changes,
            routing_config,
            ownership_config,
            max_files=args.max_files,
            max_text_files=args.max_text_files,
        )
    except (RoutingError, AuditError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)

    policy_failures = []
    if args.strict_unknown and report["unknown_paths"]:
        policy_failures.append("unknown non-document paths")
    if args.expect_docs_only and not report["scope"]["docs_only"]:
        policy_failures.append("scope is not documentation-only")
    if args.expect_no_example_builds and report["scope"]["example_build_required"]:
        policy_failures.append("one or more example builds were selected")
    if policy_failures:
        print("routing policy failed: " + "; ".join(policy_failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
