from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("waveshare_inventory_repo", SCRIPTS / "inventory_repo.py")
assert SPEC and SPEC.loader
inventory_repo = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory_repo
SPEC.loader.exec_module(inventory_repo)


class InventoryPolicyTests(unittest.TestCase):
    def inventory(
        self,
        files: dict[str, str | bytes],
        *,
        policy_config: dict | None = None,
        max_files: int = 500,
    ) -> dict:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        return inventory_repo.make_inventory(
            root,
            max_files=max_files,
            max_text_files=100,
            policy_config=policy_config or inventory_repo.load_config(None),
        )

    def test_upstream_library_content_does_not_pollute_product_inventory(self) -> None:
        data = self.inventory(
            {
                "README.md": "Demo product uses esp32s3; it does not use esp_hosted or a C6 slave.\n",
                "sdkconfig.defaults": 'CONFIG_IDF_TARGET="esp32s3"\n',
                "examples/arduino/01_demo/01_demo.ino": "// esp32s3 display\nvoid setup() {}\n",
                "examples/arduino/libraries/vendor/examples/hosted/hosted.ino": (
                    "// esp32p4 esp32-c6 esp_hosted remote_wifi\n"
                ),
                "examples/arduino/libraries/vendor/README.md": "esp32p4 hosted C6 Wi-Fi\n",
                "examples/arduino/libraries/vendor/scripts/release.py": "print('upstream')\n",
                "hardware/schematics/board.pdf": b"synthetic-board-reference",
                "examples/arduino/libraries/vendor/datasheet.pdf": b"synthetic-vendor-reference",
            }
        )

        self.assertIn("esp32s3", data["targets"])
        self.assertNotIn("esp32p4", data["targets"])
        self.assertNotIn("p4_c6_hosted_wifi", data["confirmed_features"])
        self.assertIn("p4_c6_hosted_wifi", data["unverified_feature_hints"])
        self.assertEqual(["examples/arduino/01_demo/01_demo.ino"], data["arduino_sketches"])
        self.assertEqual(
            ["examples/arduino/libraries/vendor/examples/hosted/hosted.ino"],
            data["upstream_arduino_sketches"],
        )
        self.assertEqual(["hardware/schematics/board.pdf"], data["hardware_reference_files"])
        self.assertEqual([], data["release_packaging_evidence"])
        self.assertTrue(data["target_hits"]["esp32s3"])

    def test_negative_or_documentation_mentions_never_confirm_features(self) -> None:
        data = self.inventory(
            {
                "README.md": (
                    "This esp32p4 product does not use esp_hosted and has no sensor support. "
                    "Brookesia is mentioned only for comparison.\n"
                ),
                "assets/splash.bmp": b"synthetic-image",
            }
        )

        self.assertNotIn("esp32p4", data["targets"])
        self.assertIn("esp32p4", data["unverified_target_hints"])
        self.assertEqual({}, data["confirmed_features"])
        self.assertTrue(
            {"p4_c6_hosted_wifi", "brookesia", "sensors"}.issubset(
                data["unverified_feature_hints"]
            )
        )
        self.assertNotIn("P4 host with C6 Wi-Fi slave / hosted Wi-Fi", data["shapes"])
        self.assertNotIn("Brookesia or rich UI firmware", data["shapes"])

    def test_implementation_like_notes_do_not_confirm_features(self) -> None:
        data = self.inventory(
            {
                "docs/brookesia.yml": "note: This repository does not support Brookesia\n",
                "config/legacy.defaults": (
                    'LEGACY_NOTE="no sensor or esp_hosted support on esp32p4"\n'
                ),
                "archive/brookesia.c": '#include "esp_brookesia.h"\n',
            }
        )

        self.assertEqual([], data["targets"])
        self.assertEqual({}, data["confirmed_features"])
        self.assertTrue(
            {"p4_c6_hosted_wifi", "brookesia", "sensors"}.issubset(
                data["unverified_feature_hints"]
            )
        )
        self.assertEqual([], data["shapes"])

    def test_non_build_yaml_and_orphan_source_remain_hints(self) -> None:
        data = self.inventory(
            {
                "docs/catalog.yml": "brookesia_comparison: true\n",
                "scratch/brookesia.c": '#include "esp_brookesia.h"\n',
            }
        )

        self.assertEqual({}, data["confirmed_features"])
        self.assertIn("brookesia", data["unverified_feature_hints"])
        self.assertNotIn("Brookesia or rich UI firmware", data["shapes"])

    def test_unreferenced_project_source_does_not_confirm_feature(self) -> None:
        data = self.inventory(
            {
                "examples/esp-idf/demo/CMakeLists.txt": (
                    "cmake_minimum_required(VERSION 3.16)\nproject(demo)\n"
                ),
                "examples/esp-idf/demo/main/CMakeLists.txt": (
                    "idf_component_register(SRCS main.c)\n"
                ),
                "examples/esp-idf/demo/main/main.c": "void app_main(void) {}\n",
                "examples/esp-idf/demo/main/unused.c": '#include "esp_brookesia.h"\n',
            }
        )

        self.assertEqual({}, data["confirmed_features"])
        self.assertIn("brookesia", data["unverified_feature_hints"])
        self.assertNotIn("Brookesia or rich UI firmware", data["shapes"])

    def test_first_party_implementation_can_confirm_a_feature(self) -> None:
        data = self.inventory(
            {
                "CMakeLists.txt": "cmake_minimum_required(VERSION 3.16)\nproject(demo)\n",
                "main/CMakeLists.txt": (
                    "idf_component_register(SRCS main.c REQUIRES esp_wifi_remote)\n"
                ),
                "main/main.c": '#include "esp_wifi_remote.h"\nvoid app_main(void) {}\n',
                "sdkconfig.defaults": 'CONFIG_IDF_TARGET="esp32p4"\n',
            }
        )

        self.assertIn("p4_c6_hosted_wifi", data["confirmed_features"])
        self.assertIn("P4 host with C6 Wi-Fi slave / hosted Wi-Fi", data["shapes"])

    def test_active_manifest_can_confirm_brookesia(self) -> None:
        data = self.inventory(
            {
                "CMakeLists.txt": "cmake_minimum_required(VERSION 3.16)\nproject(demo)\n",
                "idf_component.yml": "dependencies:\n  espressif/esp_brookesia: '*'\n",
                "main/main.c": '#include "esp_brookesia.h"\nvoid app_main(void) {}\n',
            }
        )

        self.assertIn("brookesia", data["confirmed_features"])
        self.assertIn("Brookesia or rich UI firmware", data["shapes"])

    def test_disabled_target_config_does_not_confirm_target(self) -> None:
        data = self.inventory(
            {
                "sdkconfig.defaults": (
                    "# CONFIG_IDF_TARGET_ESP32P4 is not set\n"
                    'CONFIG_IDF_TARGET="esp32s3"\n'
                )
            }
        )

        self.assertEqual(["esp32s3"], data["targets"])
        self.assertIn("esp32p4", data["unverified_target_hints"])

    def test_readme_target_macro_is_not_target_confirmation(self) -> None:
        data = self.inventory(
            {"README.md": "Do not set CONFIG_IDF_TARGET_ESP32P4; this board is not P4.\n"}
        )

        self.assertEqual([], data["targets"])
        self.assertIn("esp32p4", data["unverified_target_hints"])

    def test_upstream_sketch_outside_libraries_is_not_product_arduino(self) -> None:
        data = self.inventory(
            {"third_party/vendor/examples/demo/demo.ino": "void setup() {}\n"}
        )

        self.assertEqual([], data["arduino_sketches"])
        self.assertEqual(
            ["third_party/vendor/examples/demo/demo.ino"],
            data["upstream_arduino_sketches"],
        )
        self.assertNotIn("Arduino sketches with possible bundled libraries", data["shapes"])

    def test_component_directory_is_neutral_until_reviewed(self) -> None:
        data = self.inventory(
            {
                "components/ProductFeature/CMakeLists.txt": "idf_component_register(SRCS feature.c)\n",
                "components/ProductFeature/feature.c": "void product_feature(void) {}\n",
                "third_party/vendor/components/Upstream/CMakeLists.txt": "idf_component_register()\n",
            }
        )

        self.assertEqual(["components/ProductFeature"], data["local_component_candidates"])
        self.assertEqual(
            ["third_party/vendor/components/Upstream"],
            data["upstream_component_dirs"],
        )
        self.assertTrue(all("component" not in item.lower() for item in data["shapes"]))

    def test_arduino_only_repo_does_not_report_missing_idf_or_schematic(self) -> None:
        data = self.inventory(
            {"examples/arduino/Demo/Demo.ino": "void setup() {}\n"}
        )

        self.assertFalse(any("examples/esp-idf" in item for item in data["layout_issues"]))
        self.assertFalse(any("schematic" in item.lower() for item in data["layout_issues"]))
        self.assertTrue(data["conditional_scope_opportunities"])
        self.assertTrue(
            all("if" in item.lower() or "only" in item.lower() for item in data["conditional_scope_opportunities"])
        )

    def test_idf_projects_are_role_classified_and_only_examples_enter_default_ci(self) -> None:
        data = self.inventory(
            {
                "CMakeLists.txt": "cmake_minimum_required(VERSION 3.16)\nproject(root_app)\n",
                "main/CMakeLists.txt": "idf_component_register(SRCS main.c)\n",
                "main/main.c": "void app_main(void) {}\n",
                "examples/esp-idf/demo/CMakeLists.txt": "project(example_demo)\n",
                "examples/esp-idf/demo/main/CMakeLists.txt": "idf_component_register(SRCS main.c)\n",
                "examples/esp-idf/demo/main/main.c": "void app_main(void) {}\n",
                "firmware/host/CMakeLists.txt": "project(host_firmware)\n",
                "firmware/host/main/CMakeLists.txt": "idf_component_register(SRCS main.c)\n",
                "firmware/host/main/main.c": "void app_main(void) {}\n",
                "firmware/host/coprocessor/CMakeLists.txt": "project(coprocessor)\n",
                "firmware/host/coprocessor/main/CMakeLists.txt": "idf_component_register(SRCS main.c)\n",
                "firmware/host/coprocessor/main/main.c": "void app_main(void) {}\n",
                "components/local/test_apps/unit/CMakeLists.txt": "project(component_test)\n",
                "components/local/test_apps/unit/main/CMakeLists.txt": "idf_component_register()\n",
                "third_party/vendor/demo/CMakeLists.txt": "project(upstream_demo)\n",
                "third_party/vendor/demo/main/CMakeLists.txt": "idf_component_register()\n",
            }
        )

        roles = data["idf_projects_by_role"]
        self.assertEqual(["."], roles["root_application"])
        self.assertEqual(["examples/esp-idf/demo"], roles["first_party_example"])
        self.assertEqual(
            ["firmware/host", "firmware/host/coprocessor"],
            roles["maintained_firmware"],
        )
        self.assertEqual(["components/local/test_apps/unit"], roles["test_app"])
        self.assertEqual(["third_party/vendor/demo"], roles["embedded_upstream"])
        self.assertEqual(["examples/esp-idf/demo"], data["example_ci_idf_projects"])
        self.assertEqual(
            ["firmware/host", "firmware/host/coprocessor"],
            data["firmware_idf_projects_excluded_from_example_ci"],
        )

    def test_firmware_only_project_does_not_require_canonical_examples_root(self) -> None:
        data = self.inventory(
            {
                "firmware/device/CMakeLists.txt": "project(device_firmware)\n",
                "firmware/device/main/CMakeLists.txt": "idf_component_register()\n",
            }
        )
        self.assertEqual(["firmware/device"], data["idf_projects_by_role"]["maintained_firmware"])
        self.assertFalse(any("examples/esp-idf" in issue for issue in data["layout_issues"]))

    def test_policy_exclude_patterns_apply_to_all_inventory_surfaces(self) -> None:
        config = inventory_repo.load_config(None)
        config["exclude_patterns"].append("private/**")
        data = self.inventory(
            {
                "sdkconfig.defaults": 'CONFIG_IDF_TARGET="esp32s3"\n',
                "private/sdkconfig.defaults": 'CONFIG_IDF_TARGET="esp32p4"\n',
                "private/CMakeLists.txt": "project(private_brookesia)\n",
                "private/main/CMakeLists.txt": "idf_component_register(REQUIRES esp_hosted)\n",
                "private/examples/demo.ino": "void setup() {}\n",
                "private/components/secret/idf_component.yml": "dependencies:\n  esp/brookesia: '*'\n",
                "private/hardware/secret.pdf": b"not-public",
                "private/firmware.bin": b"not-public",
                "private/release.zip": b"not-public",
                "private/docs.md": "https://github.com/example/private\n",
            },
            policy_config=config,
        )

        self.assertEqual(["esp32s3"], data["targets"])
        serialized = json.dumps(data, sort_keys=True)
        self.assertNotIn("private/", serialized)
        self.assertNotIn("private\\\\", serialized)

    def test_multiline_cmake_and_nested_manifest_dependencies_are_confirmed(self) -> None:
        data = self.inventory(
            {
                "CMakeLists.txt": "project(product)\n",
                "main/CMakeLists.txt": (
                    "idf_component_register(\n"
                    "  SRCS main.c\n"
                    "  INCLUDE_DIRS .\n"
                    "  REQUIRES\n"
                    "    esp_wifi_remote\n"
                    ")\n"
                ),
                "main/idf_component.yml": (
                    "dependencies:\n"
                    "  espressif/esp_brookesia:\n"
                    "    version: '^0.4'\n"
                    "    rules:\n"
                    "      - if: target in [esp32p4]\n"
                ),
                "sdkconfig.defaults": 'CONFIG_IDF_TARGET="esp32p4"\n',
            }
        )
        self.assertIn("p4_c6_hosted_wifi", data["confirmed_features"])
        self.assertIn("brookesia", data["confirmed_features"])

        source_only = self.inventory(
            {
                "CMakeLists.txt": "project(product)\n",
                "main/CMakeLists.txt": (
                    "idf_component_register(\n  SRCS brookesia.c\n  INCLUDE_DIRS .\n)\n"
                ),
            }
        )
        self.assertNotIn("brookesia", source_only["confirmed_features"])

    def test_mixed_firmware_inventory_and_bin_archive_boundaries(self) -> None:
        data = self.inventory(
            {
                "firmware/device/CMakeLists.txt": "project(device)\n",
                "firmware/device/main/CMakeLists.txt": "idf_component_register()\n",
                "firmware/device/coprocessor/CMakeLists.txt": "project(coprocessor)\n",
                "firmware/device/coprocessor/main/CMakeLists.txt": "idf_component_register()\n",
                "firmware/device/README.md": "# Firmware\n",
                "firmware/device/sdkconfig.defaults": 'CONFIG_IDF_TARGET="esp32s3"\n',
                "firmware/device/factory.bin": b"factory",
                "firmware/device/legacy.hex": b"hex",
                "firmware/device/debug.elf": b"elf",
                "firmware/device/update.uf2": b"uf2",
                "firmware/device/SD-Card-Media.zip": b"sd",
                "firmware/device/host-tests.tgz": b"tests",
                "firmware/device/factory-firmware.tar.gz": b"delivery",
                "firmware/device/misc.7z": b"unknown",
                "firmware/device/media/icon.png": b"image",
                "firmware/device/tools/package_firmware.py": "print('synthetic')\n",
            }
        )

        firmware = data["firmware_inventory"]["firmware/device"]
        self.assertEqual(
            ["firmware/device", "firmware/device/coprocessor"],
            firmware["source_projects"],
        )
        self.assertEqual(["firmware/device/factory.bin"], firmware["binaries"])
        self.assertEqual(["firmware/device/factory.bin"], data["binary_files"])
        archive_kinds = {item["path"]: item["kind"] for item in firmware["archives"]}
        self.assertEqual("sd_resource", archive_kinds["firmware/device/SD-Card-Media.zip"])
        self.assertEqual("test_resource", archive_kinds["firmware/device/host-tests.tgz"])
        self.assertEqual("delivery", archive_kinds["firmware/device/factory-firmware.tar.gz"])
        self.assertEqual("unknown", archive_kinds["firmware/device/misc.7z"])
        self.assertIn("firmware/device/media/icon.png", firmware["resources"])
        self.assertIn("firmware/device/tools/package_firmware.py", firmware["packaging_scripts"])
        immutable_paths = {item["path"] for item in data["immutable_delivery_artifacts"]}
        self.assertIn("firmware/device/factory.bin", immutable_paths)
        self.assertIn("firmware/device/SD-Card-Media.zip", immutable_paths)
        self.assertIn("firmware/device/factory-firmware.tar.gz", immutable_paths)
        self.assertNotIn("firmware/device/host-tests.tgz", immutable_paths)
        self.assertNotIn("firmware/device/misc.7z", immutable_paths)
        serialized = json.dumps({"binary_files": data["binary_files"], "firmware": firmware})
        self.assertNotIn("legacy.hex", serialized)
        self.assertNotIn("debug.elf", serialized)
        self.assertNotIn("update.uf2", serialized)

    def test_release_packaging_shape_requires_positive_evidence(self) -> None:
        docs_only = self.inventory({"docs/firmware.md": "# Firmware documentation\n"})
        self.assertEqual([], docs_only["release_packaging_evidence"])
        self.assertNotIn("Release packaging and CI artifacts", docs_only["shapes"])

        script = self.inventory({"scripts/package_firmware.py": "print('synthetic')\n"})
        self.assertEqual(["scripts/package_firmware.py"], script["release_packaging_evidence"])
        self.assertIn("Release packaging and CI artifacts", script["shapes"])

        archive = self.inventory({"firmware/SD-Card-Media.zip": b"synthetic"})
        self.assertEqual(["firmware/SD-Card-Media.zip"], archive["release_packaging_evidence"])

        test_archive = self.inventory({"tests/fixtures/input.zip": b"synthetic"})
        self.assertEqual([], test_archive["release_packaging_evidence"])
        self.assertNotIn("Release packaging and CI artifacts", test_archive["shapes"])

    def test_external_repository_references_are_separated_from_scope_evidence(self) -> None:
        completed = mock.Mock(
            returncode=0,
            stdout="160000 0123456789012345678901234567890123456789 0\tthird_party/module\n",
        )
        with mock.patch.object(inventory_repo.subprocess, "run", return_value=completed):
            data = self.inventory(
                {
                    ".git/config": (
                        '[remote "origin"]\n'
                        "  url = https://user:secret@github.com/waveshareteam/demo.git?token=secret\n"
                    ),
                    ".gitmodules": (
                        '[submodule "module"]\n'
                        "  path = third_party/module\n"
                        "  url = https://github.com/vendor/module.git\n"
                    ),
                    "README.md": (
                        "Self: https://github.com/waveshareteam/demo/releases\n"
                        "Upstream: https://github.com/espressif/esp-idf\n"
                    ),
                    "main/idf_component.yml": (
                        "repository: https://github.com/vendor/component\n"
                        "dependencies:\n"
                        "  espressif/esp_brookesia:\n"
                        "    version: '*'\n"
                        "  custom/component:\n"
                        "    git: https://github.com/custom/component.git\n"
                    ),
                    "cmake/dependency.cmake": (
                        "FetchContent_Declare(\n"
                        "  helper\n"
                        "  GIT_REPOSITORY https://github.com/helper/project.git\n"
                        ")\n"
                    ),
                    ".github/workflows/build.yml": (
                        "steps:\n  - uses: actions/checkout@v4\n  - uses: vendor/action@v2\n"
                    ),
                    "third_party/vendor/README.md": "Source: https://github.com/vendor/upstream\n",
                }
            )

        refs = data["external_repository_references"]
        self.assertEqual(
            [{"name": "origin", "repository": "https://github.com/waveshareteam/demo"}],
            refs["remotes"],
        )
        self.assertEqual(["third_party/module"], refs["gitlinks"])
        self.assertEqual("third_party/module", refs["submodules"][0]["path"])
        self.assertTrue(any(item["repository"] == "waveshareteam/demo" for item in refs["self_links"]))
        self.assertTrue(any(item["component"] == "espressif/esp_brookesia" for item in refs["component_registry_dependencies"]))
        self.assertTrue(any(item["repository"].endswith("custom/component") for item in refs["git_dependencies"]))
        self.assertTrue(any(item["repository"].endswith("helper/project") for item in refs["git_dependencies"]))
        self.assertTrue(any(item["uses"] == "actions/checkout@v4" for item in refs["ci_uses"]))
        self.assertTrue(refs["embedded_upstream_attribution"])
        self.assertNotIn("secret", json.dumps(refs))
        self.assertNotIn("p4_c6_hosted_wifi", data["confirmed_features"])

    def test_nested_external_component_manifest_does_not_pollute_first_party_references(self) -> None:
        data = self.inventory(
            {
                ".git/config": (
                    '[remote "origin"]\n'
                    "  url = https://github.com/example/product.git\n"
                ),
                "components/local_safe/README.md": (
                    "Product wrapper for [upstream](upstream/README.md).\n"
                ),
                "components/local_safe/upstream/CMakeLists.txt": (
                    'idf_component_register(SRCS "source.c" INCLUDE_DIRS ".")\n'
                ),
                "components/local_safe/upstream/idf_component.yml": (
                    "repository: https://github.com/vendor/upstream.git\n"
                    "version: 1.0.0\n"
                ),
                "components/local_safe/upstream/README.md": (
                    "Upstream source: https://github.com/vendor/upstream\n"
                ),
                "components/local_safe/upstream/LICENSE": "Synthetic license fixture.\n",
                "components/local_safe/upstream/source.c": "void upstream(void) {}\n",
                "components/local_safe/self/CMakeLists.txt": (
                    'idf_component_register(SRCS "source.c" INCLUDE_DIRS ".")\n'
                ),
                "components/local_safe/self/idf_component.yml": (
                    "repository: https://github.com/example/product/tree/main/components/local_safe/self\n"
                    "version: 1.0.0\n"
                ),
                "components/local_safe/self/README.md": (
                    "Product-owned component: https://github.com/example/product\n"
                ),
                "components/local_safe/self/LICENSE": "Synthetic license fixture.\n",
                "components/local_safe/self/source.c": "void local_source(void) {}\n",
            }
        )

        refs = data["external_repository_references"]
        first_party_paths = {item["path"] for item in refs["first_party_documentation"]}
        upstream_paths = {item["path"] for item in refs["embedded_upstream_attribution"]}
        self.assertIn("components/local_safe/self/README.md", first_party_paths)
        self.assertNotIn("components/local_safe/upstream/README.md", first_party_paths)
        self.assertIn("components/local_safe/upstream/README.md", upstream_paths)

    def test_malformed_remote_port_is_sanitized_without_leaking_credentials(self) -> None:
        completed = mock.Mock(returncode=0, stdout="")
        with mock.patch.object(inventory_repo.subprocess, "run", return_value=completed):
            data = self.inventory(
                {
                    ".git/config": (
                        '[remote "origin"]\n'
                        "  url = https://synthetic-user:synthetic-secret@example.invalid:not-a-port/repo.git\n"
                    )
                }
            )

        remotes = data["external_repository_references"]["remotes"]
        self.assertEqual(
            [{"name": "origin", "repository": "https://example.invalid/repo"}],
            remotes,
        )
        self.assertNotIn("synthetic-secret", json.dumps(remotes))

    def test_recursive_hardware_references_are_grouped_for_multiple_boards(self) -> None:
        data = self.inventory(
            {
                "boards/alpha/hardware/alpha.kicad_sch": b"alpha",
                "boards/beta/schematic/beta.pdf": b"beta",
                "hardware/gamma/pinout.md": "# Gamma pinout\n",
                "HARDWARE_REFERENCE.md": "# Shared hardware reference\n",
                "third_party/vendor/hardware/vendor.pdf": b"vendor",
            }
        )
        self.assertEqual(
            {
                "boards/alpha": ["boards/alpha/hardware/alpha.kicad_sch"],
                "boards/beta": ["boards/beta/schematic/beta.pdf"],
                "hardware/gamma": ["hardware/gamma/pinout.md"],
                "repository": ["HARDWARE_REFERENCE.md"],
            },
            data["hardware_reference_groups"],
        )
        self.assertFalse(any("missing" in issue.lower() and "schematic" in issue.lower() for issue in data["layout_issues"]))

    def test_common_license_and_copying_names_are_recognized_without_choosing_license(self) -> None:
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md", "COPYING.txt", "COPYING.LESSER"):
            with self.subTest(name=name):
                data = self.inventory({name: "Synthetic license fixture\n"})
                self.assertEqual([name], data["license_files"])
                self.assertFalse(
                    any("license file" in item.lower() for item in data["conditional_scope_opportunities"])
                )

        missing = self.inventory({"README.md": "# No license fixture\n"})
        message = next(
            item for item in missing["conditional_scope_opportunities"]
            if "license file" in item.lower()
        )
        self.assertIn("ask the user", message.lower())
        self.assertNotRegex(message, r"(?i)Apache|MIT|GPL|BSD")

    def test_missing_security_guidance_requires_a_verified_private_channel(self) -> None:
        missing = self.inventory({"README.md": "# Synthetic public repository\n"})
        message = next(
            item for item in missing["conditional_scope_opportunities"]
            if "SECURITY.md" in item
        )
        self.assertIn("private vulnerability reporting", message)
        self.assertIn("maintainer-confirmed private channel", message)

        present = self.inventory(
            {
                "README.md": "# Synthetic public repository\n",
                "SECURITY.md": "# Security\n\nUse the repository's verified private channel.\n",
            }
        )
        self.assertFalse(
            any("SECURITY.md" in item for item in present["conditional_scope_opportunities"])
        )

    def test_comment_stripping_preserves_urls_and_removes_ordinary_line_comments(self) -> None:
        cleaned = inventory_repo.strip_source_comments(
            "set(REPOSITORY https://github.com/example/project)\n"
            "set(VALUE enabled) // ordinary implementation note\n"
        )
        self.assertIn("https://github.com/example/project", cleaned)
        self.assertNotIn("ordinary implementation note", cleaned)

    def test_existing_max_file_truncation_behavior_is_preserved(self) -> None:
        data = self.inventory(
            {"one.txt": "1", "two.txt": "2", "three.txt": "3"},
            max_files=2,
        )
        self.assertTrue(data["scan_truncated"])
        self.assertEqual(2, data["scanned_files"])


if __name__ == "__main__":
    unittest.main()
