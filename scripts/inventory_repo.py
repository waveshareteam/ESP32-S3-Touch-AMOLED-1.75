#!/usr/bin/env python3
"""Inventory a Waveshare ESP32-family repository for modernization work.

The script is read-only. It prints repo-relative findings that help an agent plan
layout normalization, managed component migration, CI coverage, release artifacts,
documentation ownership, and public collaboration templates.  Its optional JSON
policy is shared with audit_markdown.py so upstream trees do not pollute product
target, feature, hardware-reference, component, or first-party Arduino results.
Keyword matches are discovery hints; only first-party active target configuration,
CMake build/dependency declarations, or component-manifest dependencies can confirm
a capability or drive a repository-shape classification.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import shlex
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from audit_markdown import (
    AUDITED_OWNERSHIP,
    AuditError,
    UPSTREAM_OWNERSHIP,
    classify,
    discover_dynamic_upstream_roots,
    load_config,
    matches,
)

SKIP_DIR_NAMES = {
    ".git", ".pytest_cache", ".venv", "build", "dist", "managed_components",
    "node_modules", "__pycache__",
}

TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".h", ".hpp", ".ino", ".cmake", ".txt",
    ".md", ".yml", ".yaml", ".json", ".conf", ".defaults", ".csv",
}

TEXT_NAMES = {"CMakeLists.txt", "Kconfig", "sdkconfig", "sdkconfig.defaults", "sdkconfig.ci", "README.md"}
FEATURE_PATTERNS = {
    "p4_c6_hosted_wifi": re.compile(r"(?<![A-Za-z0-9])(?:esp_wifi_remote|esp_hosted|remote_wifi|sdio_slave)(?![A-Za-z0-9])", re.I),
    "brookesia": re.compile(r"(?<![A-Za-z0-9])(?:esp[_-]?brookesia|brookesia)(?![A-Za-z0-9])", re.I),
    "lvgl_display_touch": re.compile(r"(?<![A-Za-z0-9])(?:lvgl|esp_lcd|lcd|display|touch|gt911|ft5x06)(?![A-Za-z0-9])", re.I),
    "audio_i2s_codec": re.compile(r"(?<![A-Za-z0-9])(?:i2s|audio|codec|es8311|es7210)(?![A-Za-z0-9])", re.I),
    "camera_video": re.compile(r"(?<![A-Za-z0-9])(?:camera|video|esp_video|mipi|dsi)(?![A-Za-z0-9])", re.I),
    "storage_sd_usb": re.compile(r"(?<![A-Za-z0-9])(?:sdmmc|sdcard|fatfs|usb|tinyusb)(?![A-Za-z0-9])", re.I),
    "sensors": re.compile(r"(?<![A-Za-z0-9])(?:imu|sensor|qmi\d+|bmi\d+|icm\d+|ltr\d+|sht\d+|bmp\d+)(?![A-Za-z0-9])", re.I),
}
TARGET_PATTERNS = {
    target: re.compile(rf"(?<![A-Za-z0-9]){target}(?![A-Za-z0-9])", re.I)
    for target in ("esp32p4", "esp32s3", "esp32c6", "esp32s2", "esp32c3", "esp32")
}
INACTIVE_DIR_NAMES = {"archive", "archived", "backup", "backups", "deprecated", "legacy", "obsolete", "old"}
# Waveshare checked-in firmware delivery images are inventoried as .bin only.
# Other executable/image suffixes may exist in a repository, but this inventory
# must not label .hex, .uf2, or .elf files as Waveshare firmware binaries.
BINARY_SUFFIXES = {".bin"}
DELIVERY_ARCHIVE_SUFFIXES = {".zip", ".7z", ".tar", ".tgz", ".gz"}
PACKAGING_SCRIPT_SUFFIXES = {".py", ".ps1", ".sh", ".bat", ".cmd"}
PACKAGING_NAME_RE = re.compile(
    r"(?:pack(?:age|aging)?|release|artifact|bundle|archive|flash|prepare|image|merge|download)",
    re.I,
)
FIRMWARE_RESOURCE_SUFFIXES = {
    ".bmp", ".gif", ".jpeg", ".jpg", ".json", ".mp3", ".png", ".svg", ".wav", ".webp",
}
BUILD_CONFIG_NAMES = {
    "CMakeLists.txt", "Kconfig", "Kconfig.projbuild", "idf_component.yml",
    "dependencies.lock", "sdkconfig", "sdkconfig.defaults", "sdkconfig.ci",
}
LICENSE_NAME_RE = re.compile(
    r"^(?:licen[cs]e|copying)(?:[._-][A-Za-z0-9]+)*$",
    re.I,
)
IDF_PROJECT_ROLES = (
    "first_party_example",
    "maintained_firmware",
    "root_application",
    "test_app",
    "embedded_upstream",
)
TEST_APP_DIR_NAMES = {"test", "tests", "test_app", "test_apps", "test-app", "test-apps"}
HARDWARE_REF_SUFFIXES = {".pdf", ".sch", ".kicad_sch", ".brd", ".kicad_pcb", ".pcb", ".dsn"}
HARDWARE_REF_DIR_NAMES = {"hardware", "schematic", "schematics", "dimensions", "mechanical", "pcb"}
HARDWARE_REF_NAME_PATTERNS = ["schematic", "sch", "hardware", "pinout", "dimension", "mechanical", "datasheet"]


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def has_part(path: Path, root: Path, names: set[str]) -> bool:
    try:
        return bool({part.lower() for part in path.relative_to(root).parts} & names)
    except ValueError:
        return False


def should_skip_dir(path: Path) -> bool:
    name = path.name.lower()
    if name in SKIP_DIR_NAMES:
        return True
    if name.startswith("build") and (path / "CMakeCache.txt").exists():
        return True
    return False


def is_policy_excluded(path: Path, root: Path, policy_config: dict, *, is_dir: bool = False) -> bool:
    """Return whether the shared Markdown-audit policy excludes this repo path."""
    relative = rel(path, root)
    if relative in {"", "."}:
        return False
    candidates = [relative]
    if is_dir:
        candidates.append(relative.rstrip("/") + "/")
    return any(matches(candidate, policy_config["exclude_patterns"]) for candidate in candidates)


def scan_tree(
    root: Path,
    max_files: int,
    policy_config: dict,
) -> tuple[list[Path], list[Path], bool]:
    dirs: list[Path] = []
    files: list[Path] = []
    truncated = False
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        kept_dirs = []
        for dirname in dirnames:
            child = current_path / dirname
            if not should_skip_dir(child) and not is_policy_excluded(
                child, root, policy_config, is_dir=True
            ):
                dirs.append(child)
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in filenames:
            file_path = current_path / filename
            if is_policy_excluded(file_path, root, policy_config):
                continue
            files.append(file_path)
            if len(files) >= max_files:
                truncated = True
                dirnames[:] = []
                break
        if truncated:
            break
    return dirs, files, truncated


def safe_read(path: Path, limit: int = 200_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def build_indexes(root: Path, dirs: list[Path], files: list[Path]) -> tuple[dict[Path, set[str]], set[Path]]:
    files_by_dir: dict[Path, set[str]] = defaultdict(set)
    dir_set = set(dirs)
    dir_set.add(root)
    for path in files:
        files_by_dir[path.parent].add(path.name)
    return files_by_dir, dir_set


def collect_top_level(root: Path, policy_config: dict) -> list[str]:
    names = []
    try:
        for child in root.iterdir():
            if child.name == ".git" or is_policy_excluded(
                child, root, policy_config, is_dir=child.is_dir()
            ):
                continue
            names.append(child.name + ("/" if child.is_dir() else ""))
    except OSError:
        pass
    return sorted(names, key=str.lower)


def classify_idf_project_role(root: Path, project_dir: Path, policy_config: dict) -> str:
    relative = rel(project_dir, root)
    ownership = classify(rel(project_dir / "CMakeLists.txt", root), policy_config)
    parts = [part.lower() for part in project_dir.relative_to(root).parts]
    if ownership in UPSTREAM_OWNERSHIP:
        return "embedded_upstream"
    if set(parts) & TEST_APP_DIR_NAMES:
        return "test_app"
    if project_dir == root:
        return "root_application"
    if parts and parts[0] == "firmware":
        return "maintained_firmware"
    if "examples" in parts or "example" in parts:
        return "first_party_example"
    if parts and re.search(r"(?i)^esp[-_ ]?idf(?:[-_ ].*)?$", parts[0]):
        return "first_party_example"
    return "root_application"


def collect_idf_projects_by_role(
    root: Path,
    dirs: list[Path],
    files_by_dir: dict[Path, set[str]],
    dir_set: set[Path],
    policy_config: dict,
) -> dict[str, list[str]]:
    projects: dict[str, list[str]] = {role: [] for role in IDF_PROJECT_ROLES}
    excluded = {"managed_components", ".git", "build", "node_modules"}
    for project_dir in sorted(set([root] + dirs)):
        if (
            project_dir.name.lower() == "main"
            or has_part(project_dir, root, excluded)
            or is_policy_excluded(project_dir, root, policy_config, is_dir=True)
        ):
            continue
        names = files_by_dir.get(project_dir, set())
        if "CMakeLists.txt" not in names:
            continue
        has_main = (project_dir / "main") in dir_set
        cmake_text = safe_read(project_dir / "CMakeLists.txt", limit=40_000).lower()
        if has_main or re.search(r"\bproject\s*\(", cmake_text):
            role = classify_idf_project_role(root, project_dir, policy_config)
            projects[role].append(rel(project_dir, root))
    return {role: sorted(set(projects[role])) for role in IDF_PROJECT_ROLES}


def flatten_idf_projects(projects_by_role: dict[str, list[str]]) -> list[str]:
    return sorted({path for paths in projects_by_role.values() for path in paths})


def collect_arduino_sketches(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    excluded = {".git", "build", "managed_components", "node_modules", "libraries"}
    sketches = [
        rel(path, root)
        for path in files
        if path.suffix.lower() == ".ino"
        and not has_part(path, root, excluded)
        and not is_policy_excluded(path, root, policy_config)
        and classify(rel(path, root), policy_config) in AUDITED_OWNERSHIP
    ]
    return sorted(set(sketches))


def collect_upstream_arduino_sketches(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    excluded = {".git", "build", "managed_components", "node_modules"}
    sketches = [
        rel(path, root) for path in files
        if path.suffix.lower() == ".ino"
        and not has_part(path, root, excluded)
        and not is_policy_excluded(path, root, policy_config)
        and (
            has_part(path, root, {"libraries"})
            or classify(rel(path, root), policy_config) in UPSTREAM_OWNERSHIP
        )
    ]
    return sorted(set(sketches))


def collect_component_candidates(
    root: Path,
    dirs: list[Path],
    files_by_dir: dict[Path, set[str]],
    policy_config: dict,
) -> tuple[list[str], list[str]]:
    local_candidates: list[str] = []
    upstream_components: list[str] = []
    excluded = {".git", "build", "managed_components", "node_modules"}
    dir_set = set(dirs)
    for comp_root in dirs:
        root_name = comp_root.name.lower()
        if (
            root_name not in {"components", "bsp"}
            or has_part(comp_root, root, excluded)
            or is_policy_excluded(comp_root, root, policy_config, is_dir=True)
        ):
            continue
        for child in dir_set:
            if child.parent != comp_root or not child.is_dir():
                continue
            names = files_by_dir.get(child, set())
            if not names:
                continue
            relative = rel(child, root)
            if is_policy_excluded(child, root, policy_config, is_dir=True):
                continue
            ownership = classify(rel(child / "README.md", root), policy_config)
            if ownership in UPSTREAM_OWNERSHIP:
                upstream_components.append(relative)
            else:
                local_candidates.append(relative)
    return sorted(set(local_candidates)), sorted(set(upstream_components))


def collect_manifests(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    excluded = {".git", "build", "node_modules"}
    return sorted({
        rel(path, root)
        for path in files
        if path.name == "idf_component.yml"
        and not has_part(path, root, excluded)
        and not is_policy_excluded(path, root, policy_config)
        and classify(rel(path, root), policy_config) not in UPSTREAM_OWNERSHIP
    })


def collect_ci_files(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    result = []
    for path in files:
        if is_policy_excluded(path, root, policy_config):
            continue
        if classify(rel(path, root), policy_config) not in AUDITED_OWNERSHIP:
            continue
        relative = rel(path, root).lower()
        parts = relative.split("/")
        name = path.name.lower()
        if relative.startswith(".github/workflows/") and path.suffix.lower() in {".yml", ".yaml"}:
            result.append(rel(path, root))
        elif "ci" in parts or re.match(r"^ci([._-]|$)", name):
            result.append(rel(path, root))
    return sorted(set(result))


def collect_release_packaging_evidence(
    root: Path,
    files: list[Path],
    policy_config: dict,
) -> list[str]:
    """Collect positive packaging evidence; documentation alone is not evidence."""
    result: list[str] = []
    for path in files:
        if is_policy_excluded(path, root, policy_config):
            continue
        relative = rel(path, root)
        if classify(relative, policy_config) not in AUDITED_OWNERSHIP:
            continue
        lower = relative.lower()
        suffix = path.suffix.lower()
        if suffix in DELIVERY_ARCHIVE_SUFFIXES:
            if classify_delivery_archive(relative) in {"delivery", "sd_resource"}:
                result.append(relative)
        elif suffix in PACKAGING_SCRIPT_SUFFIXES and PACKAGING_NAME_RE.search(relative):
            result.append(relative)
        elif (
            lower.startswith(".github/workflows/")
            and suffix in {".yml", ".yaml"}
            and re.search(
                r"(?i)(?:upload-artifact|package[_ -]?firmware|release[_ -]?artifact|archive|\.zip\b)",
                safe_read(path, limit=120_000),
            )
        ):
            result.append(relative)
    return sorted(set(result))


def collect_github_templates(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    result = []
    for path in files:
        if is_policy_excluded(path, root, policy_config):
            continue
        relative = rel(path, root)
        if classify(relative, policy_config) not in AUDITED_OWNERSHIP:
            continue
        lower = relative.lower()
        if lower.startswith(".github/issue_template/") or lower == ".github/pull_request_template.md":
            result.append(relative)
    return sorted(set(result))



def collect_hardware_reference_files(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    excluded = {".git", "build", "managed_components", "node_modules"}
    refs: list[str] = []
    for path in files:
        if has_part(path, root, excluded) or is_policy_excluded(path, root, policy_config):
            continue
        relative = rel(path, root)
        if classify(relative, policy_config) in UPSTREAM_OWNERSHIP:
            continue
        parts = {part.lower() for part in Path(relative).parts}
        name = path.name.lower()
        suffix = path.suffix.lower()
        in_hardware_dir = bool(parts & HARDWARE_REF_DIR_NAMES)
        named_like_hardware = any(pattern in name for pattern in HARDWARE_REF_NAME_PATTERNS)
        is_hardware_file = suffix in HARDWARE_REF_SUFFIXES and (in_hardware_dir or named_like_hardware)
        is_hardware_note = is_text_candidate(path) and (in_hardware_dir or named_like_hardware)
        if is_hardware_file or is_hardware_note:
            refs.append(relative)
    return sorted(set(refs))[:80]


def hardware_reference_group(relative: str) -> str:
    parts = list(Path(relative).parts)
    lower = [part.lower() for part in parts]
    for collection in ("boards", "board", "products", "product", "targets"):
        if collection in lower:
            index = lower.index(collection)
            if index + 1 < len(parts) - 1:
                return "/".join(parts[:index + 2])
    for index, part in enumerate(lower[:-1]):
        if part not in HARDWARE_REF_DIR_NAMES:
            continue
        if index > 0:
            return "/".join(parts[:index])
        if len(parts) > 2 and lower[1] not in HARDWARE_REF_DIR_NAMES:
            return "/".join(parts[:2])
        return "repository"
    parent = Path(relative).parent.as_posix()
    return "repository" if parent in {"", "."} else parent


def group_hardware_references(references: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for relative in references:
        grouped[hardware_reference_group(relative)].append(relative)
    return {group: sorted(set(paths)) for group, paths in sorted(grouped.items())}


def collect_binary_files(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    excluded = {".git", "build", "managed_components", "node_modules"}
    binaries = [
        rel(path, root)
        for path in files
        if path.suffix.lower() in BINARY_SUFFIXES
        and not has_part(path, root, excluded)
        and not is_policy_excluded(path, root, policy_config)
        and classify(rel(path, root), policy_config) in AUDITED_OWNERSHIP
    ]
    return sorted(set(binaries))[:60]


def collect_license_files(root: Path, files: list[Path], policy_config: dict) -> list[str]:
    licenses = []
    for path in files:
        if path.parent != root or is_policy_excluded(path, root, policy_config):
            continue
        if LICENSE_NAME_RE.match(path.name):
            licenses.append(rel(path, root))
    return sorted(set(licenses), key=str.lower)


def firmware_group_for(relative: str, *, project: bool = False) -> str | None:
    parts = Path(relative).parts
    if not parts or parts[0].lower() != "firmware":
        return None
    if project and len(parts) >= 2:
        return "/".join(parts[:2])
    if len(parts) >= 3:
        return "/".join(parts[:2])
    return "firmware"


def classify_delivery_archive(relative: str) -> str:
    """Classify an archive from path/name evidence without assuming it is firmware."""
    lower = relative.lower()
    evidence = lower
    parts = Path(lower).parts
    if parts and parts[0] == "firmware":
        evidence = "/".join(parts[1:])
    tokens = set(filter(None, re.split(r"[^a-z0-9]+", evidence)))
    if "sd" in tokens and tokens & {"asset", "assets", "card", "media", "resource", "resources"}:
        return "sd_resource"
    if tokens & {"fixture", "fixtures", "sample", "samples", "test", "tests"}:
        return "test_resource"
    if (
        lower.startswith("releases/")
        or tokens & {"delivery", "factory", "firmware", "flash", "image", "ota", "release"}
    ):
        return "delivery"
    return "unknown"


def is_build_config(path: Path) -> bool:
    name = path.name
    lower = name.lower()
    return (
        name in BUILD_CONFIG_NAMES
        or lower.startswith("sdkconfig")
        or lower.startswith("partition") and path.suffix.lower() == ".csv"
        or path.suffix.lower() in {".cmake", ".defaults", ".projbuild"}
    )


def collect_firmware_inventory(
    root: Path,
    files: list[Path],
    projects_by_role: dict[str, list[str]],
    policy_config: dict,
) -> tuple[dict[str, dict[str, list]], list[dict[str, str]]]:
    groups: dict[str, dict[str, list]] = {}

    def group_data(name: str) -> dict[str, list]:
        return groups.setdefault(name, {
            "first_party_markdown": [],
            "source_projects": [],
            "build_config": [],
            "binaries": [],
            "archives": [],
            "resources": [],
            "packaging_scripts": [],
        })

    for project in projects_by_role.get("maintained_firmware", []):
        group = firmware_group_for(project, project=True)
        if group is not None:
            group_data(group)["source_projects"].append(project)

    immutable: list[dict[str, str]] = []
    for path in files:
        if is_policy_excluded(path, root, policy_config):
            continue
        relative = rel(path, root)
        group = firmware_group_for(relative)
        if group is None:
            continue
        data = group_data(group)
        ownership = classify(relative, policy_config)
        upstream = ownership in UPSTREAM_OWNERSHIP
        suffix = path.suffix.lower()
        if suffix == ".md" and ownership in AUDITED_OWNERSHIP:
            data["first_party_markdown"].append(relative)
        if not upstream and is_build_config(path):
            data["build_config"].append(relative)
        if not upstream and suffix == ".bin":
            data["binaries"].append(relative)
            immutable.append({"path": relative, "kind": "firmware_binary"})
        elif not upstream and suffix in DELIVERY_ARCHIVE_SUFFIXES:
            archive_kind = classify_delivery_archive(relative)
            data["archives"].append({"path": relative, "kind": archive_kind})
            if archive_kind in {"delivery", "sd_resource"}:
                immutable.append({"path": relative, "kind": f"archive:{archive_kind}"})
        if not upstream and (
            suffix in FIRMWARE_RESOURCE_SUFFIXES
            or {part.lower() for part in Path(relative).parts} & {"assets", "media", "resources", "spiffs", "littlefs"}
        ):
            data["resources"].append(relative)
        if (
            not upstream
            and suffix in PACKAGING_SCRIPT_SUFFIXES
            and PACKAGING_NAME_RE.search(relative)
        ):
            data["packaging_scripts"].append(relative)

    for data in groups.values():
        for key in (
            "first_party_markdown", "source_projects", "build_config", "binaries",
            "resources", "packaging_scripts",
        ):
            data[key] = sorted(set(data[key]))
        data["archives"] = sorted(data["archives"], key=lambda item: item["path"])
    immutable = sorted(immutable, key=lambda item: item["path"])
    return {name: groups[name] for name in sorted(groups)}, immutable


def is_text_candidate(path: Path) -> bool:
    return path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES


def strip_source_comments(text: str) -> str:
    text = re.sub(r"(?ms)^\s*#if\s+0\b.*?^\s*#endif\b", " ", text)
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        quote = ""
        escaped = False
        index = 0
        while index < len(line):
            char = line[index]
            if escaped:
                escaped = False
            elif char == "\\" and quote:
                escaped = True
            elif quote:
                if char == quote:
                    quote = ""
            elif char in {'"', "'"}:
                quote = char
            elif (
                char == "/"
                and index + 1 < len(line)
                and line[index + 1] == "/"
                and not (index > 0 and line[index - 1] == ":")
            ):
                line = line[:index]
                break
            index += 1
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"(?m)^\s*#\s*CONFIG_[A-Za-z0-9_]+\s+is\s+not\s+set\s*$", " ", text)
    return re.sub(
        r"(?m)^\s*#(?!\s*(?:include|if|ifdef|ifndef|elif|define)\b).*$",
        " ",
        text,
    )


def iter_cmake_calls(text: str) -> Iterable[tuple[str, str]]:
    """Yield common CMake calls with balanced, possibly multiline arguments."""
    cleaned = strip_source_comments(text)
    start_re = re.compile(
        r"(?i)\b(idf_component_register|project|target_link_libraries|add_subdirectory|set|fetchcontent_declare|externalproject_add)\s*\("
    )
    position = 0
    while True:
        match = start_re.search(cleaned, position)
        if match is None:
            return
        depth = 1
        index = match.end()
        quote = ""
        escaped = False
        while index < len(cleaned) and depth:
            char = cleaned[index]
            if escaped:
                escaped = False
            elif char == "\\" and quote:
                escaped = True
            elif quote:
                if char == quote:
                    quote = ""
            elif char in {'"', "'"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth:
            return
        yield match.group(1).lower(), cleaned[match.end():index - 1]
        position = index


def cmake_tokens(arguments: str) -> list[str]:
    lexer = shlex.shlex(arguments.replace(";", " "), posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return arguments.replace(";", " ").split()


def extract_cmake_dependency_terms(text: str) -> set[str]:
    terms: set[str] = set()
    register_keywords = {
        "SRCS", "SRC_DIRS", "EXCLUDE_SRCS", "INCLUDE_DIRS", "PRIV_INCLUDE_DIRS",
        "REQUIRES", "PRIV_REQUIRES", "LDFRAGMENTS", "EMBED_FILES",
        "EMBED_TXTFILES", "KCONFIG", "KCONFIG_PROJBUILD", "WHOLE_ARCHIVE",
    }
    for call, arguments in iter_cmake_calls(text):
        tokens = cmake_tokens(arguments)
        if not tokens:
            continue
        if call == "idf_component_register":
            collecting = False
            for token in tokens:
                upper = token.upper()
                if upper in {"REQUIRES", "PRIV_REQUIRES"}:
                    collecting = True
                    continue
                if upper in register_keywords:
                    collecting = False
                    continue
                if collecting:
                    terms.add(token)
        elif call == "target_link_libraries":
            terms.update(
                token for token in tokens[1:]
                if token.upper() not in {"PUBLIC", "PRIVATE", "INTERFACE"}
            )
        elif call == "add_subdirectory":
            terms.add(tokens[0])
        elif call == "project":
            # An active project identity is implementation evidence, but only the
            # project name is considered; DESCRIPTION/HOMEPAGE prose is ignored.
            terms.add(tokens[0])
        elif call == "set" and tokens[0].upper() in {
            "EXTRA_COMPONENT_DIRS", "COMPONENTS", "IDF_COMPONENT_MANAGER"
        }:
            terms.update(tokens[1:])
    return {term.strip('"\'') for term in terms if term.strip('"\'')}


def strip_yaml_comment(line: str) -> str:
    quote = ""
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
        elif char == "\\" and quote:
            escaped = True
        elif quote:
            if char == quote:
                quote = ""
        elif char in {'"', "'"}:
            quote = char
        elif char == "#":
            return line[:index]
    return line


def yaml_key_value(line: str) -> tuple[str, str] | None:
    match = re.match(r"\s*[\"']?([^:\"']+?)[\"']?\s*:\s*(.*?)\s*$", line)
    if match is None:
        return None
    return match.group(1).strip(), match.group(2).strip().strip('"\'')


def parse_manifest_dependencies(text: str) -> dict[str, dict[str, str]]:
    """Parse the common idf_component.yml dependency mapping conservatively."""
    lines = [strip_yaml_comment(line).rstrip() for line in text.splitlines()]
    dependencies: dict[str, dict[str, str]] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        match = re.match(r"^(\s*)dependencies\s*:\s*(.*?)\s*$", line, re.I)
        if match is None:
            index += 1
            continue
        base_indent = len(match.group(1).expandtabs(2))
        inline = match.group(2).strip()
        if inline.startswith("{") and inline.endswith("}"):
            for entry in inline[1:-1].split(","):
                parsed = yaml_key_value(entry)
                if parsed is not None:
                    name, value = parsed
                    dependencies[name] = {"value": value}
        index += 1
        dependency_indent: int | None = None
        current: str | None = None
        while index < len(lines):
            nested = lines[index]
            if not nested.strip():
                index += 1
                continue
            indent = len(nested) - len(nested.lstrip(" \t"))
            if indent <= base_indent:
                break
            parsed = yaml_key_value(nested)
            if parsed is None:
                index += 1
                continue
            key, value = parsed
            if dependency_indent is None:
                dependency_indent = indent
            if indent == dependency_indent:
                current = key
                dependencies.setdefault(current, {})["value"] = value
            elif current is not None and indent > dependency_indent:
                dependencies[current][key.lower()] = value
            index += 1
    return dependencies


def manifest_dependency_names(text: str) -> set[str]:
    disabled = {"0", "false", "n", "no", "none", "null", "off", "disabled"}
    return {
        name
        for name, metadata in parse_manifest_dependencies(text).items()
        if metadata.get("value", "").lower() not in disabled
    }


GITHUB_REPOSITORY_RE = re.compile(
    r"(?i)(?:https?://github\.com/|ssh://(?:[^/@]+@)?github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
)


def github_repositories(text: str) -> list[str]:
    repositories = []
    for match in GITHUB_REPOSITORY_RE.finditer(text):
        repository = match.group(1).removesuffix(".git").rstrip("/.,);]}")
        if repository.count("/") == 1:
            repositories.append(repository)
    return sorted(set(repositories), key=str.lower)


def sanitize_repository_location(value: str) -> str:
    value = value.strip().strip('"\'')
    github = github_repositories(value)
    if github:
        return "https://github.com/" + github[0]
    if re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith(("/", "\\\\")):
        return "[local repository path omitted]"
    scp = re.match(r"^(?:[^@/:]+@)?([^:]+):(.+)$", value)
    if scp and "://" not in value:
        return f"ssh://{scp.group(1)}/{scp.group(2).removesuffix('.git')}"
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if not parsed.scheme or not parsed.hostname:
        return value
    host = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        # A malformed port must not make inventory fail or force us to return
        # the original URL, which may contain credentials.
        port = None
    if port:
        host += f":{port}"
    return urlunsplit((parsed.scheme, host, parsed.path.removesuffix(".git"), "", ""))


def resolve_git_dir(root: Path) -> Path | None:
    dotgit = root / ".git"
    if dotgit.is_dir():
        return dotgit
    if dotgit.is_file():
        match = re.match(r"(?i)\s*gitdir:\s*(.+?)\s*$", safe_read(dotgit, limit=4_000))
        if match:
            candidate = Path(match.group(1))
            return candidate if candidate.is_absolute() else (root / candidate).resolve()
    return None


def collect_git_remotes(root: Path) -> list[dict[str, str]]:
    git_dir = resolve_git_dir(root)
    if git_dir is None or not (git_dir / "config").is_file():
        return []
    parser = configparser.RawConfigParser()
    try:
        parser.read(git_dir / "config", encoding="utf-8")
    except (configparser.Error, OSError):
        return []
    remotes = []
    for section in parser.sections():
        match = re.fullmatch(r'remote\s+"(.+)"', section)
        if match and parser.has_option(section, "url"):
            remotes.append({
                "name": match.group(1),
                "repository": sanitize_repository_location(parser.get(section, "url")),
            })
    return sorted(remotes, key=lambda item: (item["name"].lower(), item["repository"].lower()))


def collect_submodules(
    root: Path,
    files: list[Path],
    policy_config: dict,
) -> list[dict[str, str]]:
    module_path = root / ".gitmodules"
    if module_path not in files:
        return []
    parser = configparser.RawConfigParser()
    try:
        parser.read(module_path, encoding="utf-8")
    except (configparser.Error, OSError):
        return []
    modules = []
    for section in parser.sections():
        if not section.lower().startswith("submodule "):
            continue
        path = parser.get(section, "path", fallback="").replace("\\", "/")
        if not path or matches(path, policy_config["exclude_patterns"]):
            continue
        modules.append({
            "path": path,
            "repository": sanitize_repository_location(parser.get(section, "url", fallback="")),
        })
    return sorted(modules, key=lambda item: (item["path"].lower(), item["repository"].lower()))


def collect_gitlinks(root: Path, policy_config: dict) -> list[str]:
    if resolve_git_dir(root) is None:
        return []
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    gitlinks = []
    for line in result.stdout.splitlines():
        match = re.match(r"^160000\s+[0-9a-f]+\s+\d+\t(.+)$", line)
        if match:
            relative = match.group(1).replace("\\", "/")
            if not matches(relative, policy_config["exclude_patterns"]):
                gitlinks.append(relative)
    return sorted(set(gitlinks))


def top_level_yaml_fields(text: str, names: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        clean = strip_yaml_comment(line).rstrip()
        if not clean or clean[0].isspace():
            continue
        parsed = yaml_key_value(clean)
        if parsed is not None and parsed[0].lower() in names and parsed[1]:
            result[parsed[0].lower()] = parsed[1]
    return result


def cmake_git_dependencies(text: str) -> list[str]:
    repositories = []
    for call, arguments in iter_cmake_calls(text):
        if call not in {"fetchcontent_declare", "externalproject_add"}:
            continue
        tokens = cmake_tokens(arguments)
        for index, token in enumerate(tokens[:-1]):
            if token.upper() == "GIT_REPOSITORY":
                repositories.append(sanitize_repository_location(tokens[index + 1]))
    return sorted(set(repositories), key=str.lower)


def collect_external_repository_references(
    root: Path,
    files: list[Path],
    policy_config: dict,
) -> dict[str, list]:
    remotes = collect_git_remotes(root)
    self_repositories = {
        repository
        for item in remotes
        for repository in github_repositories(item["repository"])
    }
    first_party_docs = []
    self_links = []
    embedded_attribution = []
    component_provenance = []
    component_dependencies = []
    local_component_dependencies = []
    git_dependencies = []
    ci_uses = []

    for path in files:
        if is_policy_excluded(path, root, policy_config):
            continue
        relative = rel(path, root)
        ownership = classify(relative, policy_config)
        suffix = path.suffix.lower()
        content = ""
        if suffix == ".md" or path.name == "idf_component.yml" or path.name == "CMakeLists.txt" or suffix in {".cmake", ".yml", ".yaml"}:
            content = safe_read(path, limit=160_000)

        if suffix == ".md" and content:
            repositories = github_repositories(content)
            if repositories and ownership in AUDITED_OWNERSHIP:
                first_party_docs.append({"path": relative, "repositories": repositories})
                for repository in repositories:
                    if repository in self_repositories:
                        self_links.append({"path": relative, "repository": repository})
                if "components" in {part.lower() for part in Path(relative).parts}:
                    for repository in repositories:
                        if repository not in self_repositories:
                            component_provenance.append({
                                "path": relative,
                                "repository": repository,
                                "source": "first_party_component_documentation",
                            })
            elif repositories and ownership in UPSTREAM_OWNERSHIP:
                embedded_attribution.append({"path": relative, "repositories": repositories})

        if path.name == "idf_component.yml" and content:
            for name, metadata in sorted(parse_manifest_dependencies(content).items()):
                if metadata.get("git"):
                    git_dependencies.append({
                        "path": relative,
                        "repository": sanitize_repository_location(metadata["git"]),
                        "source": "idf_component.yml dependency",
                    })
                elif metadata.get("path"):
                    local_component_dependencies.append({
                        "path": relative,
                        "component": name,
                        "local_path": metadata["path"],
                    })
                else:
                    component_dependencies.append({"path": relative, "component": name})
            for key, value in top_level_yaml_fields(content, {"repository", "url"}).items():
                component_provenance.append({
                    "path": relative,
                    "repository": sanitize_repository_location(value),
                    "source": f"idf_component.yml {key}",
                })

        if (path.name == "CMakeLists.txt" or suffix == ".cmake") and content:
            for repository in cmake_git_dependencies(content):
                git_dependencies.append({
                    "path": relative,
                    "repository": repository,
                    "source": "CMake git dependency",
                })

        if relative.lower().startswith(".github/workflows/") and suffix in {".yml", ".yaml"}:
            for match in re.finditer(r"(?im)^\s*-?\s*uses\s*:\s*[\"']?([^\s\"'#]+)", content):
                uses = match.group(1)
                if not uses.startswith("./"):
                    ci_uses.append({"path": relative, "uses": uses})

    def unique_dicts(items: list[dict], keys: tuple[str, ...]) -> list[dict]:
        deduplicated = {tuple(item.get(key, "") for key in keys): item for item in items}
        return [deduplicated[key] for key in sorted(deduplicated)]

    return {
        "remotes": remotes,
        "self_links": unique_dicts(self_links, ("path", "repository")),
        "submodules": collect_submodules(root, files, policy_config),
        "gitlinks": collect_gitlinks(root, policy_config),
        "first_party_documentation": unique_dicts(first_party_docs, ("path",)),
        "component_repository_provenance": unique_dicts(
            component_provenance, ("path", "repository", "source")
        ),
        "component_registry_dependencies": unique_dicts(
            component_dependencies, ("path", "component")
        ),
        "local_component_dependencies": unique_dicts(
            local_component_dependencies, ("path", "component", "local_path")
        ),
        "git_dependencies": unique_dicts(git_dependencies, ("path", "repository", "source")),
        "ci_uses": unique_dicts(ci_uses, ("path", "uses")),
        "embedded_upstream_attribution": unique_dicts(embedded_attribution, ("path",)),
    }


def active_key_value(line: str) -> tuple[str, str] | None:
    match = re.match(r"\s*[\"']?([A-Za-z0-9_./-]+)[\"']?\s*[:=]\s*(.*?)\s*,?\s*$", line)
    if not match:
        return None
    key, value = match.group(1), match.group(2).strip().strip('"\'').lower()
    if not value or value in {"0", "false", "n", "no", "none", "null", "off", "disabled"}:
        return None
    return key, value


def has_affirmative_target_evidence(root: Path, path: Path, content: str, target: str) -> bool:
    if has_part(path, root, INACTIVE_DIR_NAMES):
        return False
    cleaned = strip_source_comments(content)
    upper = target.upper()
    name = path.name.lower()
    if name.startswith("sdkconfig"):
        patterns = (
            re.compile(rf"(?im)^\s*CONFIG_IDF_TARGET\s*=\s*[\"']?{target}[\"']?\s*$"),
            re.compile(rf"(?im)^\s*CONFIG_IDF_TARGET_{upper}\s*=\s*y\s*$"),
        )
        return any(pattern.search(cleaned) for pattern in patterns)
    if path.name == "CMakeLists.txt" or path.suffix.lower() == ".cmake":
        return bool(re.search(
            rf"(?i)\bset\s*\(\s*IDF_TARGET\s+[\"']?{target}[\"']?\s*\)",
            cleaned,
        ))
    return False


def has_affirmative_feature_evidence(root: Path, path: Path, content: str, feature: str) -> bool:
    if has_part(path, root, INACTIVE_DIR_NAMES):
        return False
    pattern = FEATURE_PATTERNS[feature]
    cleaned = strip_source_comments(content)
    suffix = path.suffix.lower()
    if path.name == "CMakeLists.txt" or suffix == ".cmake":
        terms = extract_cmake_dependency_terms(cleaned)
        return any(pattern.search(term) for term in terms)

    if path.name == "idf_component.yml":
        return any(pattern.search(name) for name in manifest_dependency_names(content))

    if path.name.lower().startswith("sdkconfig"):
        for line in cleaned.splitlines():
            parsed = active_key_value(line)
            if parsed is not None and pattern.search(parsed[0]):
                return True
        return False

    return False


def detect_target_evidence(
    root: Path,
    files: list[Path],
    max_text_files: int,
    policy_config: dict,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    confirmed: dict[str, list[str]] = {target: [] for target in TARGET_PATTERNS}
    hints: dict[str, list[str]] = {target: [] for target in TARGET_PATTERNS}
    inspected = 0
    for path in files:
        if is_policy_excluded(path, root, policy_config):
            continue
        if not is_text_candidate(path):
            continue
        relative = rel(path, root)
        ownership = classify(relative, policy_config)
        if ownership in UPSTREAM_OWNERSHIP:
            continue
        if inspected >= max_text_files:
            continue
        content = safe_read(path, limit=120_000)
        text = relative + "\n" + content
        inspected += 1
        for target, pattern in TARGET_PATTERNS.items():
            if not pattern.search(text):
                continue
            if len(hints[target]) < 12:
                hints[target].append(relative)
            if ownership in AUDITED_OWNERSHIP and has_affirmative_target_evidence(
                root, path, content, target
            ):
                if len(confirmed[target]) < 12:
                    confirmed[target].append(relative)
    confirmed_result = {target: hits for target, hits in confirmed.items() if hits}
    hint_result: dict[str, list[str]] = {}
    for target, hits in hints.items():
        unconfirmed = [path for path in hits if path not in set(confirmed_result.get(target, []))]
        if unconfirmed:
            hint_result[target] = unconfirmed
    return confirmed_result, hint_result


def detect_feature_evidence(
    root: Path,
    files: list[Path],
    max_text_files: int,
    policy_config: dict,
    target_hits: dict[str, list[str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    confirmed: dict[str, list[str]] = {name: [] for name in FEATURE_PATTERNS}
    hints: dict[str, list[str]] = {name: [] for name in FEATURE_PATTERNS}
    inspected = 0
    for path in files:
        relative = rel(path, root)
        if is_policy_excluded(path, root, policy_config):
            continue
        if classify(relative, policy_config) not in AUDITED_OWNERSHIP:
            continue
        if not is_text_candidate(path) or inspected >= max_text_files:
            continue
        content = safe_read(path, limit=80_000)
        searchable = relative + "\n" + content
        inspected += 1
        for feature, pattern in FEATURE_PATTERNS.items():
            if not pattern.search(searchable):
                continue
            if len(hints[feature]) < 12:
                hints[feature].append(relative)
            if has_affirmative_feature_evidence(root, path, content, feature):
                if len(confirmed[feature]) < 12:
                    confirmed[feature].append(relative)

    if "p4_c6_hosted_wifi" in confirmed and "esp32p4" not in target_hits:
        confirmed["p4_c6_hosted_wifi"] = []

    confirmed_result = {name: hits for name, hits in confirmed.items() if hits}
    hint_result: dict[str, list[str]] = {}
    for name, hits in hints.items():
        unconfirmed = [path for path in hits if path not in set(confirmed_result.get(name, []))]
        if unconfirmed:
            hint_result[name] = unconfirmed
    return confirmed_result, hint_result


def detect_layout_issues(
    root: Path,
    top_level: list[str],
    dirs: list[Path],
    idf_projects_by_role: dict[str, list[str]],
    arduino_sketches: list[str],
) -> list[str]:
    issues = []
    examples = root / "examples"
    first_party_examples = idf_projects_by_role.get("first_party_example", [])
    if first_party_examples and not (examples / "esp-idf").is_dir():
        issues.append("Missing canonical examples/esp-idf/ root")
    if arduino_sketches and not (examples / "arduino").is_dir():
        issues.append("Missing canonical examples/arduino/ root for detected first-party Arduino sketches")
    versioned = []
    for path in dirs:
        if "examples" in {part.lower() for part in path.relative_to(root).parts} and re.search(r"(?i)(esp[-_ ]?idf|arduino).*(v?\d+\.\d+)", path.name):
            versioned.append(rel(path, root))
    if versioned:
        issues.append("Version-suffixed example roots detected: " + ", ".join(sorted(versioned)[:12]))
    odd_names = [name for name in top_level if re.search(r"(?i)firm\s*ware|firmware", name) and name != "firmware/"]
    if odd_names:
        issues.append("Non-canonical firmware root names detected: " + ", ".join(odd_names[:12]))
    return issues


def detect_conditional_scope_opportunities(
    root: Path,
    github_templates: list[str],
    license_files: list[str],
) -> list[str]:
    opportunities: list[str] = []
    for required in ["config", "docs", ".github"]:
        if not (root / required).exists():
            opportunities.append(f"Missing {required}/; consider only if platform-style normalization is in scope")
    for required_file in ["CONTRIBUTING.md", "SUPPORT.md"]:
        if not (root / required_file).exists():
            opportunities.append(f"Missing {required_file}; consider only if public governance is in scope")
    if not (root / "SECURITY.md").exists():
        opportunities.append(
            "Missing SECURITY.md; consider only if public governance is in scope and GitHub private vulnerability reporting or another maintainer-confirmed private channel can be verified"
        )
    if not license_files:
        opportunities.append(
            "No repository license file detected; ask the user or repository owner to choose licensing only if governance is in scope"
        )
    if not any(path.lower().startswith(".github/issue_template/") for path in github_templates):
        opportunities.append("Missing .github/ISSUE_TEMPLATE bug report template; consider only if public issue reports are in scope")
    if ".github/pull_request_template.md" not in {path.lower() for path in github_templates}:
        opportunities.append("Missing .github/pull_request_template.md; consider only if public pull requests are in scope")
    return opportunities


def classify_shapes(data: dict) -> list[str]:
    shapes = []
    if any(
        path == "examples/esp-idf" or path.startswith("examples/esp-idf/")
        for path in data["example_ci_idf_projects"]
    ) or any(path.startswith("examples/arduino/") for path in data["arduino_sketches"]):
        shapes.append("Already or partially platform-style")
    if any("Version-suffixed" in item for item in data["layout_issues"]):
        shapes.append("Versioned or inconsistent example roots")
    elif any(
        not path.startswith("examples/esp-idf/")
        for path in data["example_ci_idf_projects"]
    ):
        shapes.append("Legacy or non-canonical ESP-IDF example roots")
    if "p4_c6_hosted_wifi" in data["confirmed_features"]:
        shapes.append("P4 host with C6 Wi-Fi slave / hosted Wi-Fi")
    if "brookesia" in data["confirmed_features"]:
        shapes.append("Brookesia or rich UI firmware")
    if data["arduino_sketches"]:
        shapes.append("Arduino sketches with possible bundled libraries")
    if data["hardware_reference_files"]:
        shapes.append("Hardware references available for pin audit")
    if data["binary_files"]:
        shapes.append("Factory binaries or firmware artifacts")
    if data["release_packaging_evidence"]:
        shapes.append("Release packaging and CI artifacts")
    if data["github_templates"]:
        shapes.append("Public collaboration templates")
    return shapes


def make_inventory(root: Path, max_files: int, max_text_files: int, policy_config: dict | None = None) -> dict:
    root = root if root.is_absolute() else root.resolve()
    policy_config = dict(policy_config or load_config(None))
    dynamic_upstream_roots = discover_dynamic_upstream_roots(root)
    if dynamic_upstream_roots:
        dynamic_patterns = []
        for upstream_root in sorted(dynamic_upstream_roots, key=str.lower):
            dynamic_patterns.extend((upstream_root, f"{upstream_root}/**"))
        policy_config["classification_rules"] = [
            {"category": "embedded_upstream", "patterns": dynamic_patterns}
        ] + list(policy_config["classification_rules"])
    dirs, files, truncated = scan_tree(root, max_files=max_files, policy_config=policy_config)
    files_by_dir, dir_set = build_indexes(root, dirs, files)
    top_level = collect_top_level(root, policy_config)
    target_hits, unverified_target_hints = detect_target_evidence(
        root, files, max_text_files=max_text_files, policy_config=policy_config
    )
    confirmed_features, unverified_feature_hints = detect_feature_evidence(
        root,
        files,
        max_text_files=max_text_files,
        policy_config=policy_config,
        target_hits=target_hits,
    )
    idf_projects_by_role = collect_idf_projects_by_role(
        root, dirs, files_by_dir, dir_set, policy_config
    )
    idf_projects = flatten_idf_projects(idf_projects_by_role)
    arduino_sketches = collect_arduino_sketches(root, files, policy_config)
    upstream_arduino_sketches = collect_upstream_arduino_sketches(root, files, policy_config)
    local_component_candidates, upstream_component_dirs = collect_component_candidates(
        root, dirs, files_by_dir, policy_config
    )
    hardware_reference_files = collect_hardware_reference_files(root, files, policy_config)
    firmware_inventory, immutable_delivery_artifacts = collect_firmware_inventory(
        root, files, idf_projects_by_role, policy_config
    )
    release_packaging_evidence = collect_release_packaging_evidence(
        root, files, policy_config
    )
    license_files = collect_license_files(root, files, policy_config)
    data = {
        "repo": root.name,
        "scan_truncated": truncated,
        "scanned_files": len(files),
        "top_level": top_level,
        "targets": sorted(target_hits),
        "target_hits": target_hits,
        "unverified_target_hints": unverified_target_hints,
        "idf_projects": idf_projects,
        "idf_projects_by_role": idf_projects_by_role,
        "example_ci_idf_projects": idf_projects_by_role["first_party_example"],
        "firmware_idf_projects_excluded_from_example_ci": idf_projects_by_role["maintained_firmware"],
        "arduino_sketches": arduino_sketches,
        "upstream_arduino_sketches": upstream_arduino_sketches,
        "local_component_candidates": local_component_candidates,
        "upstream_component_dirs": upstream_component_dirs,
        "manifests": collect_manifests(root, files, policy_config),
        "ci_files": collect_ci_files(root, files, policy_config),
        "release_files": release_packaging_evidence,
        "release_packaging_evidence": release_packaging_evidence,
        "github_templates": collect_github_templates(root, files, policy_config),
        "hardware_reference_files": hardware_reference_files,
        "hardware_reference_groups": group_hardware_references(hardware_reference_files),
        "binary_files": collect_binary_files(root, files, policy_config),
        "firmware_inventory": firmware_inventory,
        "immutable_delivery_artifacts": immutable_delivery_artifacts,
        "external_repository_references": collect_external_repository_references(
            root, files, policy_config
        ),
        "license_files": license_files,
        "confirmed_features": confirmed_features,
        "unverified_feature_hints": unverified_feature_hints,
        "layout_issues": [],
        "conditional_scope_opportunities": [],
    }
    data["layout_issues"] = detect_layout_issues(
        root, top_level, dirs, idf_projects_by_role, arduino_sketches
    )
    data["conditional_scope_opportunities"] = detect_conditional_scope_opportunities(
        root, data["github_templates"], license_files
    )
    data["shapes"] = classify_shapes(data)
    return data


def bullet_list(items: Iterable[str], max_items: int) -> str:
    values = list(items)
    if not values:
        return "- None detected\n"
    shown = values[:max_items]
    text = "".join(f"- `{item}`\n" for item in shown)
    if len(values) > max_items:
        text += f"- ... {len(values) - max_items} more\n"
    return text


def record_list(items: list[dict], fields: tuple[str, ...], max_items: int) -> str:
    if not items:
        return "- None detected\n"
    lines = []
    for item in items[:max_items]:
        values = []
        for field in fields:
            value = item.get(field, "")
            if isinstance(value, list):
                value = ", ".join(value)
            if value:
                values.append(f"{field}={value}")
        lines.append("- " + "; ".join(values) + "\n")
    if len(items) > max_items:
        lines.append(f"- ... {len(items) - max_items} more\n")
    return "".join(lines)


def format_markdown(data: dict, max_items: int) -> str:
    out = []
    out.append(f"# Repository Inventory: {data['repo']}\n")
    out.append(f"\nScanned files: {data['scanned_files']}\n")
    if data["scan_truncated"]:
        out.append("\nWarning: scan hit the max-files limit; rerun with a higher limit if needed.\n")
    out.append("\n## Detected Shapes\n")
    out.append(bullet_list(data["shapes"], max_items))
    out.append("\n## Targets\n")
    out.append(bullet_list(data["targets"], max_items))
    if data["target_hits"]:
        out.append("\n### Target Evidence\n")
        for target, hits in sorted(data["target_hits"].items()):
            out.append(f"#### {target}\n")
            out.append(bullet_list(hits, max_items))
    if data["unverified_target_hints"]:
        out.append("\n### Unverified Target Hints\n")
        out.append("Documentation/history mentions do not select build targets without implementation confirmation.\n")
        for target, hits in sorted(data["unverified_target_hints"].items()):
            out.append(f"#### {target}\n")
            out.append(bullet_list(hits, max_items))
    out.append("\n## Layout Issues\n")
    out.append(bullet_list(data["layout_issues"], max_items))
    out.append("\n## Conditional Scope Opportunities\n")
    out.append("These are not defects unless the user selects the corresponding modernization scope.\n")
    out.append(bullet_list(data["conditional_scope_opportunities"], max_items))
    out.append("\n## Hardware References By Board/Project Group\n")
    if data["hardware_reference_groups"]:
        for group, paths in data["hardware_reference_groups"].items():
            out.append(f"### {group}\n")
            out.append(bullet_list(paths, max_items))
    else:
        out.append("- None detected; this is not a defect unless hardware-facing work is explicitly in scope.\n")
    out.append("\n## ESP-IDF Projects By Role\n")
    for role in IDF_PROJECT_ROLES:
        out.append(f"### {role}\n")
        out.append(bullet_list(data["idf_projects_by_role"][role], max_items))
    out.append("\n### Default ESP-IDF Example CI Selection\n")
    out.append("Only `first_party_example` projects enter default example CI. Maintained firmware, root applications, test apps, and embedded upstream projects remain inventoried but require explicit routing.\n")
    out.append(bullet_list(data["example_ci_idf_projects"], max_items))
    out.append("\n## Arduino Sketches\n")
    out.append(bullet_list(data["arduino_sketches"], max_items))
    out.append("\n## Upstream Arduino Sketches Excluded From Product CI\n")
    out.append(bullet_list(data["upstream_arduino_sketches"], max_items))
    out.append("\n## Local Component Candidates Requiring Review\n")
    out.append("Directory placement does not prove reuse, removability, or managed-component equivalence.\n")
    out.append(bullet_list(data["local_component_candidates"], max_items))
    out.append("\n## Upstream Component Directories\n")
    out.append(bullet_list(data["upstream_component_dirs"], max_items))
    out.append("\n## Component Manifests\n")
    out.append(bullet_list(data["manifests"], max_items))
    out.append("\n## CI Files\n")
    out.append(bullet_list(data["ci_files"], max_items))
    out.append("\n## Positive Release-Packaging Evidence\n")
    out.append("Documentation such as `docs/firmware.md` is not packaging evidence by itself.\n")
    out.append(bullet_list(data["release_packaging_evidence"], max_items))
    out.append("\n## Recognized Repository License Files\n")
    out.append("The inventory recognizes common LICENSE/COPYING filenames but never selects a license.\n")
    out.append(bullet_list(data["license_files"], max_items))
    out.append("\n## GitHub Templates\n")
    out.append(bullet_list(data["github_templates"], max_items))
    out.append("\n## Confirmed Feature Evidence\n")
    out.append("Only active first-party target/build/dependency evidence in this section may select a capability-specific shape.\n")
    if data["confirmed_features"]:
        for feature, hits in sorted(data["confirmed_features"].items()):
            out.append(f"### {feature}\n")
            out.append(bullet_list(hits, max_items))
    else:
        out.append("- None detected\n")
    if data["unverified_feature_hints"]:
        out.append("\n## Unverified Feature Hints\n")
        out.append("These keyword-only or documentation-only hits must not expand scope, CI, docs, or TODOs without independent confirmation.\n")
        for feature, hits in sorted(data["unverified_feature_hints"].items()):
            out.append(f"### {feature}\n")
            out.append(bullet_list(hits, max_items))
    out.append("\n## Mixed Firmware Inventory\n")
    if data["firmware_inventory"]:
        for group, inventory in data["firmware_inventory"].items():
            out.append(f"### {group}\n")
            for key in (
                "first_party_markdown", "source_projects", "build_config", "binaries",
                "resources", "packaging_scripts",
            ):
                out.append(f"#### {key}\n")
                out.append(bullet_list(inventory[key], max_items))
            out.append("#### archives\n")
            out.append(record_list(inventory["archives"], ("path", "kind"), max_items))
    else:
        out.append("- None detected\n")
    out.append("\n## Immutable Delivery Boundaries\n")
    out.append("Checked-in `.bin` files and archives positively classified as delivery or SD resources are immutable by default. Test and unknown archives remain visible for review but are not promoted to delivery artifacts; archives are never assumed to be firmware binaries.\n")
    out.append(record_list(data["immutable_delivery_artifacts"], ("path", "kind"), max_items))
    out.append("\n## Waveshare Firmware Binaries (.bin only)\n")
    out.append(bullet_list(data["binary_files"], max_items))
    out.append("\n## External Repository References\n")
    external = data["external_repository_references"]
    for key, fields in (
        ("remotes", ("name", "repository")),
        ("self_links", ("path", "repository")),
        ("submodules", ("path", "repository")),
        ("gitlinks", ()),
        ("first_party_documentation", ("path", "repositories")),
        ("component_repository_provenance", ("path", "repository", "source")),
        ("component_registry_dependencies", ("path", "component")),
        ("local_component_dependencies", ("path", "component", "local_path")),
        ("git_dependencies", ("path", "repository", "source")),
        ("ci_uses", ("path", "uses")),
        ("embedded_upstream_attribution", ("path", "repositories")),
    ):
        out.append(f"### {key}\n")
        if key == "gitlinks":
            out.append(bullet_list(external[key], max_items))
        else:
            out.append(record_list(external[key], fields, max_items))
    out.append("Repository links and attribution are inventory evidence only; they never select product targets or feature scope.\n")
    out.append("\n## Suggested Next Checks\n")
    out.append("- Confirm each selected framework and optional capability from repository evidence or explicit user scope; omit absent surfaces.\n")
    out.append("- Resolve framework versions and migration guides only for the selected support matrix.\n")
    out.append("- Classify local component candidates before checking managed equivalence; directory placement alone is not removal evidence.\n")
    out.append("- For hardware-facing changes, audit affected pin/config constants against local schematics or hardware references.\n")
    out.append("- If a hardware-facing change lacks references, ask the user to provide them before claiming pin validation is complete.\n")
    out.append("- Confirm default example CI contains only `first_party_example`; route maintained firmware, test apps, root applications, and embedded upstream projects explicitly.\n")
    out.append("- Keep inventoried firmware projects, `.bin`, and archives outside default CI and unchanged; when relevant, report one maintainer-aware deferred direction until explicit firmware scope is provided.\n")
    out.append("- Add optional source-built example-CI artifacts only when explicitly useful, keep outputs ignored, and do not infer packaging from documentation alone.\n")
    out.append("- Check whether GitHub issue, pull request, and governance files are missing.\n")
    return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory a Waveshare ESP32-family repository.")
    parser.add_argument("repo", type=Path, help="Path to a cloned repository")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--max-items", type=int, default=30)
    parser.add_argument("--max-files", type=int, default=50_000)
    parser.add_argument("--max-text-files", type=int, default=2_000)
    parser.add_argument("--config", type=Path, help="optional JSON ownership policy used by audit_markdown.py")
    args = parser.parse_args()
    if not args.repo.exists() or not args.repo.is_dir():
        parser.error(f"repository path does not exist or is not a directory: {args.repo}")
    try:
        policy_config = load_config(args.config)
    except AuditError as exc:
        parser.error(str(exc))
    data = make_inventory(
        args.repo,
        max_files=args.max_files,
        max_text_files=args.max_text_files,
        policy_config=policy_config,
    )
    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(data, args.max_items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
