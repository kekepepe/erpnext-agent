"""Offline source patch guards; temporary files only, no ERP access."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "phase0/localization/patches/patch_core.py"
spec = importlib.util.spec_from_file_location("core_patch", path)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class SourcePatchTests(unittest.TestCase):
    def setUp(self):
        self.before = b'const label = "Save";\n'
        self.after = b'const label = __("Save");\n'
        self.spec = dict(path="apps/frappe/frappe/public/js/test.js",
                         before_sha256=patch.digest(self.before), after_sha256=patch.digest(self.after),
                         replacements=[['"Save"', '__("Save")']])

    def test_forward_and_exact_reverse(self):
        self.assertEqual(patch.transform(self.before, self.spec), self.after)
        self.assertEqual(patch.transform(self.after, self.spec, True), self.before)

    def test_drift_rejected(self):
        with self.assertRaises(ValueError):
            patch.transform(self.before + b"// upgrade", self.spec)

    def test_double_application_rejected(self):
        with self.assertRaises(ValueError):
            patch.transform(self.after, self.spec)

    def test_bad_replacement_rejected(self):
        self.spec["replacements"] = [["missing", "changed"]]
        with self.assertRaises(ValueError):
            patch.transform(self.before, self.spec)

    def test_bad_output_hash_rejected(self):
        self.spec["after_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            patch.transform(self.before, self.spec)

    def test_path_escape_rejected(self):
        self.spec["path"] = "../outside.js"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                patch.plans(Path(temp), dict(files=[self.spec]))

    def test_batch_failure_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / self.spec["path"]
            target.parent.mkdir(parents=True)
            target.write_bytes(self.before)
            bad = dict(self.spec, path="apps/frappe/frappe/public/js/missing.js")
            with self.assertRaises(FileNotFoundError):
                patch.plans(root, dict(files=[self.spec, bad]))
            self.assertEqual(target.read_bytes(), self.before)


if __name__ == "__main__":
    unittest.main()
