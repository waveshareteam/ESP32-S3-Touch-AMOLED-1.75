from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "discover_examples.py"
SPEC = importlib.util.spec_from_file_location("discover_examples", SCRIPT)
assert SPEC and SPEC.loader
discover_examples = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = discover_examples
SPEC.loader.exec_module(discover_examples)


class DiscoverExamplesTests(unittest.TestCase):
    def test_selector_accepts_name_and_repository_relative_path(self) -> None:
        items = [
            {"name": "alpha", "path": "examples/esp-idf/alpha"},
            {"name": "beta", "path": "examples/esp-idf/beta"},
        ]
        self.assertEqual([items[0]], discover_examples.select_items(items, "alpha", "project"))
        self.assertEqual([items[1]], discover_examples.select_items(items, "examples/esp-idf/beta", "project"))
        self.assertEqual([], discover_examples.select_items(items, "SketchA", "project", True))
        with self.assertRaises(SystemExit):
            discover_examples.select_items(items, "unknown", "project")

    def test_arduino_selector_accepts_directory_and_sketch_path(self) -> None:
        item = {
            "name": "SketchA",
            "path": "examples/arduino/SketchA",
            "sketch": "examples/arduino/SketchA/SketchA.ino",
        }
        for selector in ("SketchA", "examples/arduino/SketchA", item["sketch"]):
            self.assertEqual([item], discover_examples.select_items([item], selector, "sketch"))

    def test_routed_selection_is_validated_and_can_be_empty(self) -> None:
        items = [{"name": "alpha", "path": "examples/esp-idf/alpha"}]
        selectors = discover_examples.selectors_from_json('["examples/esp-idf/alpha"]', "project")
        self.assertEqual(items, discover_examples.select_routed_items(items, selectors, "project", False))
        self.assertEqual([], discover_examples.select_routed_items(items, [], "project", True))
        with self.assertRaises(SystemExit):
            discover_examples.select_routed_items(items, ["missing"], "project", True)

    def test_routed_arduino_sketch_path_selects_its_directory_once(self) -> None:
        item = {
            "name": "SketchA",
            "path": "examples/arduino/SketchA",
            "sketch": "examples/arduino/SketchA/SketchA.ino",
        }
        self.assertEqual(
            [item],
            discover_examples.select_routed_items([item], [item["sketch"]], "Arduino sketch", False),
        )
        with self.assertRaises(SystemExit):
            discover_examples.select_routed_items([item], ["examples/arduino/unknown.ino"], "Arduino sketch", True)

    def test_cli_writes_compact_github_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output.txt"
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--surface", "esp-idf", "--selectors-json", "[]",
                    "--allow-empty", "--github-output", str(output),
                ], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
            self.assertEqual({"include": []}, json.loads(values["matrix"]))
            self.assertEqual("0", values["count"])


if __name__ == "__main__":
    unittest.main()
