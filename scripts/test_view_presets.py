"""Offline unit tests for DEC-020 data-driven job-view presets."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "hardware_erp"))

from hardware_erp import view_presets as vp  # noqa: E402


class ViewPresetTests(unittest.TestCase):
    def test_validate_preset_config_normalizes_and_rejects_invalid(self):
        cfg = vp.validate_preset_config({
            "role": "  R1测试岗位  ",
            "kind": "purchase_receipt",
            "visibleFields": ["partnerId", "productId", "quantity"],
            "editableFields": ["companyId", "partnerId", "quantity"],  # companyId hidden -> stripped
            "requiredFields": ["partnerId"],
            "actions": ["saveDraft"],
            "lockReasons": {"companyId": "不可查看公司"},
        })
        self.assertEqual(cfg["role"], "R1测试岗位")
        self.assertEqual(cfg["editableFields"], ["partnerId", "quantity"])

        with self.assertRaises(ValueError):
            vp.validate_preset_config({"role": "", "kind": "purchase_receipt"})
        with self.assertRaises(ValueError):
            vp.validate_preset_config({"role": "R", "kind": "bad_kind"})
        with self.assertRaises(ValueError):
            vp.validate_preset_config({
                "role": "R", "kind": "purchase_receipt",
                "visibleFields": ["unknownField"], "editableFields": [], "requiredFields": [], "actions": [],
            })

    def test_resolve_effective_preset_respects_native_authority_and_merges_roles(self):
        pr_presets = [p for p in vp.DEFAULT_PRESETS if p["kind"] == "purchase_receipt"]

        # Stock maker with native create -> full edit & saveDraft
        maker = vp.resolve_effective_preset(pr_presets, {"R1库存经办"}, can_save_native=True)
        self.assertIn("saveDraft", maker["actions"])
        self.assertEqual(maker["matchedRoles"], ["R1库存经办"])

        # Stock maker if native permission is revoked -> saveDraft MUST be denied
        revoked = vp.resolve_effective_preset(pr_presets, {"R1库存经办"}, can_save_native=False)
        self.assertNotIn("saveDraft", revoked["actions"])
        self.assertIn("saveDraft", revoked["lockReasons"])

        # Stock manager -> read-only with explicit lock reason
        mgr = vp.resolve_effective_preset(pr_presets, {"R1库存复核"}, can_save_native=False)
        self.assertEqual(mgr["editableFields"], [])
        self.assertEqual(mgr["actions"], [])
        self.assertIn("R1库存复核", mgr["lockReasons"]["saveDraft"])

    def test_check_write_against_preset_blocks_locked_fields_and_actions(self):
        preset = {
            "visibleFields": ["companyId", "partnerId", "postingDate", "productId", "warehouseId", "quantity"],
            "editableFields": ["quantity"],
            "actions": ["saveDraft"],
            "lockReasons": {
                "postingDate": "此岗位不可修改单据日期。",
                "addRow": "此岗位不可新增行。",
            },
        }
        existing = {
            "companyId": "C1",
            "partnerId": "S1",
            "postingDate": "2026-11-24",
            "lines": [{"productId": "I1", "warehouseId": "W1", "quantity": "3"}],
        }

        # Changing editable quantity only -> allowed
        ok_payload = {**existing, "lines": [{"productId": "I1", "warehouseId": "W1", "quantity": "5"}]}
        self.assertIsNone(vp.check_write_against_preset(preset, ok_payload, existing))

        # Tampering locked header postingDate -> blocked with specific message
        bad_date = {**existing, "postingDate": "2026-11-23"}
        err = vp.check_write_against_preset(preset, bad_date, existing)
        self.assertEqual(err, ("PRESET_FIELD_LOCKED", "此岗位不可修改单据日期。"))

        # Adding a row when addRow is disallowed -> blocked
        added_row = {**existing, "lines": existing["lines"] + [{"productId": "I1", "warehouseId": "W1", "quantity": "1"}]}
        err2 = vp.check_write_against_preset(preset, added_row, existing)
        self.assertEqual(err2, ("PRESET_ACTION_DENIED", "此岗位不可新增行。"))

    def test_filter_draft_by_preset_strips_hidden_fields(self):
        draft = {
            "id": "MAT-PRE-1",
            "kind": "purchase_receipt",
            "companyId": "C1",
            "partnerId": "S1",
            "postingDate": "2026-11-24",
            "lines": [{"productId": "I1", "warehouseId": "W1", "quantity": "3"}],
            "revision": 1,
            "status": "draft",
        }
        preset = {"visibleFields": ["partnerId", "productId", "quantity"]}
        filtered = vp.filter_draft_by_preset(draft, preset)
        self.assertNotIn("companyId", filtered)
        self.assertNotIn("postingDate", filtered)
        self.assertEqual(filtered["partnerId"], "S1")
        self.assertEqual(filtered["lines"], [{"productId": "I1", "quantity": "3"}])


if __name__ == "__main__":
    unittest.main()
