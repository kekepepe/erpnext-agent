import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("opening_reconciliation", ROOT / "scripts/phase0-reconcile-opening.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class OpeningReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.sample = (ROOT / 'phase0/migration/opening-example.csv').read_text()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'snapshot.csv'

    def read(self, data):
        self.path.write_text(data)
        return module.snapshot(self.path)

    def test_same_total_different_party_does_not_match(self):
        original = self.read(self.sample)
        self.assertNotEqual(original, self.read(self.sample.replace("示例客户", "其他客户")))
        self.assertNotEqual(original, self.read(self.sample.replace("20.00", "20.01")))

    def test_bad_input_cannot_reconcile_to_itself(self):
        for data in [self.sample + self.sample.splitlines()[1] + "\n",
                     self.sample.replace("20.00", "NaN"), self.sample.replace("35.00", "34.00", 1),
                     self.sample.replace("示例仓,件", "示例仓,")]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.read(data)
