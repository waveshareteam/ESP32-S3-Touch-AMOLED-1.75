from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
SCRIPT_PATH = SCRIPTS / "audit_ci_routing.py"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("waveshare_audit_ci_routing", SCRIPT_PATH)
assert SPEC and SPEC.loader
audit_ci_routing = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit_ci_routing
SPEC.loader.exec_module(audit_ci_routing)


class CiRoutingAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.write("README.md", "# Synthetic product repository\n")
        self.write_idf_project("examples/esp-idf/alpha")
        self.write_idf_project("examples/esp-idf/beta")
        self.write("examples/arduino/SketchA/SketchA.ino", "void setup() {}\n")
        self.write("examples/arduino/SketchB/SketchB.ino", "void setup() {}\n")
        self.write("examples/arduino/libraries/Synthetic/src/Synthetic.cpp", "void helper() {}\n")
        self.write("firmware/device/CMakeLists.txt", "project(device_firmware)\n")
        self.write("firmware/device/main/CMakeLists.txt", "idf_component_register()\n")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write(self, relative: str, content: str | bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")

    def write_idf_project(self, relative: str) -> None:
        self.write(f"{relative}/CMakeLists.txt", "project(synthetic_example)\n")
        self.write(f"{relative}/main/CMakeLists.txt", "idf_component_register(SRCS main.c)\n")
        self.write(f"{relative}/main/main.c", "void app_main(void) {}\n")

    @staticmethod
    def changes(*paths: str, status: str = "M") -> list:
        return [audit_ci_routing.Change(status, path) for path in paths]

    def route(self, changes: list, config: dict | None = None) -> dict:
        return audit_ci_routing.route_changes(
            self.root,
            changes,
            config or audit_ci_routing.load_routing_config(None),
            audit_ci_routing.load_ownership_config(None),
            max_files=500,
            max_text_files=100,
        )

    def run_cli(self, changed_lines: str, *extra: str) -> subprocess.CompletedProcess[str]:
        changed = self.root / "changed.txt"
        changed.write_text(changed_lines, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(self.root),
                "--changed-files-from",
                str(changed),
                *extra,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def test_markdown_at_root_example_sketch_library_and_firmware_routes_no_builds(self) -> None:
        report = self.route(
            self.changes(
                "README.md",
                "examples/esp-idf/alpha/README.md",
                "examples/arduino/SketchA/README.md",
                "examples/arduino/libraries/Synthetic/README.md",
                "firmware/device/README.md",
            )
        )
        self.assertTrue(report["scope"]["docs_only"])
        self.assertFalse(report["scope"]["example_build_required"])
        self.assertTrue(report["scope"]["firmware_touched"])
        self.assertEqual("none", report["esp_idf"]["mode"])
        self.assertEqual("none", report["arduino"]["mode"])

    def test_direct_source_changes_select_only_affected_projects(self) -> None:
        report = self.route(
            self.changes(
                "examples/esp-idf/alpha/main/main.c",
                "examples/arduino/SketchB/SketchB.ino",
            )
        )
        self.assertEqual("selected", report["esp_idf"]["mode"])
        self.assertEqual(["examples/esp-idf/alpha"], report["esp_idf"]["selected"])
        self.assertEqual("selected", report["arduino"]["mode"])
        self.assertEqual(
            ["examples/arduino/SketchB/SketchB.ino"],
            report["arduino"]["selected"],
        )

    def test_shared_library_source_selects_all_arduino_but_readme_selects_none(self) -> None:
        readme = self.route(
            self.changes("examples/arduino/libraries/Synthetic/README.md")
        )
        self.assertEqual("none", readme["arduino"]["mode"])

        source = self.route(
            self.changes("examples/arduino/libraries/Synthetic/src/Synthetic.cpp")
        )
        self.assertEqual("all", source["arduino"]["mode"])
        self.assertEqual(2, len(source["arduino"]["selected"]))
        self.assertEqual("none", source["esp_idf"]["mode"])

    def test_workflow_change_selects_all_available_frameworks(self) -> None:
        report = self.route(self.changes(".github/workflows/examples.yml"))
        self.assertEqual("all", report["esp_idf"]["mode"])
        self.assertEqual("all", report["arduino"]["mode"])

    def test_firmware_source_binary_and_archive_never_enter_example_matrix(self) -> None:
        report = self.route(
            self.changes(
                "firmware/device/main/main.c",
                "firmware/device/factory.bin",
                "firmware/device/sd-resources.zip",
            )
        )
        self.assertFalse(report["scope"]["docs_only"])
        self.assertTrue(report["scope"]["firmware_touched"])
        self.assertTrue(report["scope"]["release_review_required"])
        self.assertFalse(report["scope"]["example_build_required"])
        self.assertEqual("none", report["esp_idf"]["mode"])
        self.assertEqual("none", report["arduino"]["mode"])

    def test_unknown_complete_path_is_conservative_all_and_strict_mode_fails(self) -> None:
        report = self.route(self.changes("shared/generated_input.dat"))
        self.assertEqual(["shared/generated_input.dat"], report["unknown_paths"])
        self.assertEqual("all", report["esp_idf"]["mode"])
        self.assertEqual("all", report["arduino"]["mode"])

        process = self.run_cli("M\tshared/generated_input.dat\n", "--strict-unknown")
        self.assertEqual(1, process.returncode)
        self.assertIn("unknown non-document paths", process.stderr)

    def test_empty_changed_scope_is_operational_error_not_fallback_all(self) -> None:
        process = self.run_cli("\n", "--format", "json")
        self.assertEqual(2, process.returncode)
        self.assertEqual("", process.stdout)
        self.assertIn("changed-file scope is empty", process.stderr)

    def test_rename_preserves_old_source_impact(self) -> None:
        change = audit_ci_routing.Change(
            "R",
            "docs/retired-example.md",
            "examples/esp-idf/alpha/main/retired.c",
        )
        report = self.route([change])
        self.assertFalse(report["scope"]["docs_only"])
        self.assertEqual(["examples/esp-idf/alpha"], report["esp_idf"]["selected"])

    def test_config_extensions_are_narrow_and_do_not_replace_defaults(self) -> None:
        config_path = self.root / "routing.json"
        config_path.write_text(
            json.dumps(
                {
                    "build_override_patterns": ["examples/esp-idf/alpha/resources/build-input.md"],
                    "documentation_asset_patterns": ["public-assets/**"],
                    "ignore_build_patterns": [".github/workflows/docs.yml"],
                    "esp_idf_shared_patterns": ["shared/idf/**"],
                }
            ),
            encoding="utf-8",
        )
        config = audit_ci_routing.load_routing_config(config_path)
        report = self.route(
            self.changes("public-assets/hero.png", ".github/workflows/docs.yml"),
            config,
        )
        self.assertFalse(report["scope"]["docs_only"])
        self.assertFalse(report["scope"]["example_build_required"])

        shared = self.route(self.changes("shared/idf/compat.h"), config)
        self.assertEqual("all", shared["esp_idf"]["mode"])
        self.assertEqual("none", shared["arduino"]["mode"])

        override = self.route(
            self.changes("examples/esp-idf/alpha/resources/build-input.md"), config
        )
        self.assertFalse(override["scope"]["docs_only"])
        self.assertEqual(["examples/esp-idf/alpha"], override["esp_idf"]["selected"])

        with self.assertRaises(audit_ci_routing.RoutingError):
            bad = self.root / "bad-routing.json"
            bad.write_text('{"repository_specific_magic": []}', encoding="utf-8")
            audit_ci_routing.load_routing_config(bad)

        with self.assertRaises(audit_ci_routing.RoutingError):
            escaping = self.root / "escaping-routing.json"
            escaping.write_text(
                '{"documentation_patterns": ["../outside/**"]}', encoding="utf-8"
            )
            audit_ci_routing.load_routing_config(escaping)

    def test_cli_exact_docs_only_contract_and_json_output(self) -> None:
        process = self.run_cli(
            "M\tREADME.md\nM\texamples/esp-idf/alpha/README.md\n",
            "--expect-docs-only",
            "--expect-no-example-builds",
            "--format",
            "json",
        )
        self.assertEqual(0, process.returncode, process.stderr or process.stdout)
        report = json.loads(process.stdout)
        self.assertTrue(report["scope"]["docs_only"])
        self.assertFalse(report["scope"]["example_build_required"])

        source = self.run_cli(
            "M\texamples/esp-idf/alpha/main/main.c\n",
            "--expect-no-example-builds",
        )
        self.assertEqual(1, source.returncode)
        self.assertIn("example builds were selected", source.stderr)

    def test_repository_routing_config_extends_the_generic_defaults(self) -> None:
        path = SKILL_ROOT / "config" / "ci-routing.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(audit_ci_routing.DEFAULT_CONFIG), set(raw))
        loaded = audit_ci_routing.load_routing_config(path)
        self.assertIn("*.md", loaded["documentation_patterns"])
        self.assertIn("firmware/**", loaded["firmware_patterns"])
        self.assertIn("scripts/audit_markdown.py", loaded["ignore_build_patterns"])


if __name__ == "__main__":
    unittest.main()
