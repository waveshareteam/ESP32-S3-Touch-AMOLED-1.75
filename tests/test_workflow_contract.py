from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "examples.yml"


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_quality_job_runs_complete_diff_routing_and_compact_outputs(self) -> None:
        self.assertIn("fetch-depth: 0", self.workflow)
        self.assertIn("--find-renames", self.workflow)
        self.assertIn("--routing-config config/ci-routing.json", self.workflow)
        self.assertIn("--ownership-config config/markdown-audit.json", self.workflow)
        self.assertIn("--strict-unknown", self.workflow)
        self.assertIn("json.dumps(report[\"esp_idf\"][\"selected\"], separators=(\",\", \":\"))", self.workflow)

    def test_routing_outputs_control_both_discovery_jobs(self) -> None:
        self.assertIn("needs: quality", self.workflow)
        self.assertIn("needs.quality.outputs.idf-selectors", self.workflow)
        self.assertIn("needs.quality.outputs.arduino-selectors", self.workflow)
        self.assertEqual(2, self.workflow.count("--allow-empty"))
        self.assertIn("--selector \"${{ github.event.inputs.target || 'all' }}\"", self.workflow)
        self.assertIn("Unknown workflow_dispatch selector", self.workflow)

    def test_manual_selector_accepts_arduino_directory_name_and_path(self) -> None:
        self.assertIn("arduino_directories = {path.rsplit(\"/\", 1)[0] for path in arduino_sketches}", self.workflow)
        self.assertIn("idf_projects | arduino_sketches | arduino_directories | selector_names", self.workflow)
        self.assertIn("<<'PY'\n          import json", self.workflow)
        self.assertIn("\n          PY\n          fi", self.workflow)

    def test_workflow_keeps_release_matrix_and_pr_concurrency(self) -> None:
        for value in ("v5.5.4,v6.0.2", "--arduino-core 3.3.10", "tags: [\"v*\"]", "cancel-in-progress"):
            self.assertIn(value, self.workflow)


if __name__ == "__main__":
    unittest.main()
