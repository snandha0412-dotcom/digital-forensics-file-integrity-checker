import json
import tempfile
import unittest
from pathlib import Path

from integrity_checker import (
    compare_inventory,
    create_baseline,
    load_baseline,
    verify_directory,
)


class IntegrityCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "evidence"
        self.root.mkdir()
        (self.root / "alpha.txt").write_text("original", encoding="utf-8")
        self.baseline = Path(self.temp.name) / "baseline.json"

    def test_create_and_verify_clean_baseline(self):
        create_baseline(self.root, self.baseline)
        result = verify_directory(self.root, self.baseline)
        self.assertEqual(result["status"], "CLEAN")
        self.assertEqual(result["checked_files"], 1)

    def test_detect_modified_added_and_missing(self):
        create_baseline(self.root, self.baseline)
        (self.root / "alpha.txt").write_text("changed", encoding="utf-8")
        (self.root / "new.txt").write_text("new", encoding="utf-8")
        result = verify_directory(self.root, self.baseline)
        self.assertEqual(result["modified"], ["alpha.txt"])
        self.assertEqual(result["added"], ["new.txt"])
        self.assertEqual(result["missing"], [])

        (self.root / "alpha.txt").unlink()
        result = verify_directory(self.root, self.baseline)
        self.assertIn("alpha.txt", result["missing"])

    def test_compare_inventory(self):
        result = compare_inventory(
            {"a": {"sha256": "1"}, "b": {"sha256": "2"}},
            {"a": {"sha256": "9"}, "c": {"sha256": "3"}},
        )
        self.assertEqual(result, {
            "added": ["c"], "modified": ["a"], "missing": ["b"]
        })

    def test_reject_invalid_baseline(self):
        self.baseline.write_text('{"schema_version": 99, "files": {}}', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_baseline(self.baseline)


if __name__ == "__main__":
    unittest.main()
