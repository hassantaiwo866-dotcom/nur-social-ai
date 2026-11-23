import tempfile
import unittest
from pathlib import Path

from production_reliability import new_run_manifest, update_stage, record_failure, save_run_manifest


class ProductionReliabilityTests(unittest.TestCase):
    def test_run_manifest_records_stage_progress(self):
        manifest = new_run_manifest("test-run")
        update_stage(manifest, "editorial", "completed", "Plan created")
        self.assertEqual(manifest["status"], "running")
        self.assertEqual(manifest["stages"][0]["stage"], "editorial")

    def test_failure_is_persistable_and_keeps_manual_review_flag(self):
        manifest = new_run_manifest("test-run")
        update_stage(manifest, "render", "started")
        record_failure(manifest, RuntimeError("render failed"))
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["error"]["type"], "RuntimeError")
        self.assertTrue(manifest["manual_review_required"])

    def test_manifest_write_is_atomic_and_readable(self):
        manifest = new_run_manifest("test-run")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            save_run_manifest(path, manifest)
            self.assertTrue(path.exists())
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
