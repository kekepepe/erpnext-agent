import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rehearsal",ROOT/"scripts/phase0-rehearse-opening.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class NativeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads((mod.FIX/"mapping-clean-site.json").read_text())
        self.mapped=mod.preflight.prepare(self.cfg, mod.FIX/"opening-mapping-example.csv")
        self.detail=json.loads((mod.FIX/"opening-vouchers-example.json").read_text())

    def test_reject_unexplained_allocation_and_duplicate_refs(self):
        for change in ("settled","payment_ref"):
            detail=copy.deepcopy(self.detail)
            detail["payable"][change]=3 if change=="settled" else detail["receivable"]["payment_ref"]
            with self.assertRaises(ValueError):
                mod.validate_details(self.cfg,detail,self.mapped)

    def test_second_warehouse_conversion_and_duplicate_external_invoices(self):
        cfg = json.loads((mod.FIX/"mapping-expanded.json").read_text())
        detail = json.loads((mod.FIX/"vouchers-expanded.json").read_text())
        source = mod.preflight.prepare(cfg, mod.FIX/"opening-expanded.csv")
        mod.validate_details(cfg,detail,source)
        invalid = copy.deepcopy(detail)
        invalid["stock"][1]["factor"] = 40
        with self.assertRaises(ValueError):
            mod.validate_details(cfg,invalid,source)
        detail["receivable"][1]["ref"] = detail["receivable"][0]["ref"]
        with self.assertRaisesRegex(ValueError,"外部单号重复"):
            mod.validate_details(cfg,detail,source)

    def test_preserve_unmapped_nonzero_and_net_party_credits(self):
        reports={name:{"result":[]} for name in mod.report.REPORTS}
        co,day=self.cfg["company"],self.cfg["cutoff"]
        balance=dict(currency="CNY",to_date=day,is_group_account=0,closing_debit=0,closing_credit=0)
        reports["Trial Balance"]["result"]=[dict(balance,account="控制科目"),dict(balance,account="未知借方",closing_debit=5),
                                            dict(balance,account="未知贷方",closing_credit=5),
                                            dict(balance,account="分组",is_group_account=1,closing_debit=5)]
        party=dict(currency="CNY",posting_date=day,party="客户")
        reports["Accounts Receivable"]={"add_total_row":True,"result":[dict(party,voucher_no="发票",outstanding=15),
                                                                      dict(party,voucher_no="贷项",outstanding=-3),["合计",12]]}
        rows=mod.report.normalize(reports,co,day,{"控制科目"})
        self.assertEqual(len(rows),4)
        self.assertEqual(rows["ar",co,"客户","",""]["amount"],12)
        self.assertEqual(rows["gl",co,"未知贷方","",""]["credit"],5)
        reports["Accounts Receivable"]["result"][0]["posting_date"]="2026-11-01"
        with self.assertRaises(ValueError):
            mod.report.normalize(reports,co,day,{"控制科目"})

    def test_preflight_rejects_wrong_asof_and_replaced_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            target=root/"target.csv"
            (root/"reports.json").write_text("{}")
            target.write_text("untrusted")
            meta={k:self.cfg[k] for k in ("company","currency","cutoff")}
            meta.update(time_zone="Asia/Shanghai",sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.iterdir()})
            def write(): (root/"manifest.json").write_text(json.dumps(meta))
            meta["cutoff"]="2026-11-01"
            write()
            with self.assertRaisesRegex(ValueError,"截止日"):
                mod.preflight.verify_target(self.cfg,self.mapped,target)
            meta["cutoff"]=self.cfg["cutoff"]
            write()
            (root/"reports.json").write_text("changed")
            with self.assertRaisesRegex(ValueError,"摘要"):
                mod.preflight.verify_target(self.cfg,self.mapped,target)
