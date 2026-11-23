import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("migration", ROOT / "scripts/phase0-preflight-migration.py")
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "phase0/migration"
        self.config = json.loads((self.root / "mapping-example.json").read_text())
        self.source = self.root / "opening-mapping-example.csv"

    def test_different_company_mapping_preserves_amounts(self):
        original = migration.prepare(self.config, self.source)
        other = copy.deepcopy(self.config)
        other["company"] = "第二演练公司"
        other["ar"]["示例客户"] = "第二客户"
        mapped = migration.prepare(other, self.source)
        self.assertEqual(mapped["ar","第二演练公司","第二客户","",""], original["ar",self.config["company"],"R1合成客户","",""])

    def test_replaced_file_and_internally_balanced_wrong_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "modified.csv"
            path.write_text(self.source.read_text().replace("15.00", "15.01", 1))
            with self.assertRaisesRegex(ValueError, "校验值"):
                migration.prepare(self.config, path)
            self.config["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "控制科目不一致"):
                migration.prepare(self.config, path)

    def test_duplicate_target_warehouse(self):
        self.config["warehouses"]["示例分仓"] = self.config["warehouses"]["示例仓"]
        with self.assertRaisesRegex(ValueError, "相同目标"):
            migration.prepare(self.config, self.source)
