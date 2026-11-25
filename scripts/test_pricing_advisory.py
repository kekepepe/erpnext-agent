"""Offline unit tests for 1A pricing advisory resolution and minimum-sale checks."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "hardware_erp"


def load_pricing_advisory():
    fake_frappe = types.ModuleType("frappe")
    fake_frappe.whitelist = lambda *a, **kw: (lambda fn: fn)
    fake_frappe.read_only = lambda *a, **kw: (lambda fn: fn)
    with patch.dict(sys.modules, {"frappe": fake_frappe}):
        spec = importlib.util.spec_from_file_location(
            "pricing_advisory_test_target", APP_ROOT / "hardware_erp" / "pricing_advisory.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


pa = load_pricing_advisory()


class PricingAdvisoryUnitTests(unittest.TestCase):
    def test_format_rate_normalizes_currency_precision(self):
        self.assertEqual(pa.format_rate(100), "100.00")
        self.assertEqual(pa.format_rate("75.5"), "75.50")
        self.assertEqual(pa.format_rate("85.125000"), "85.125")

    def test_select_price_candidate_follows_custom_priority_order(self):
        candidates = {
            "pricing_rule": None,
            "party_price": {"source": "party_price", "rate": "90.00"},
            "tier_price": {"source": "tier_price", "rate": "100.00"},
            "history_price": {"source": "history_price", "rate": "88.00"},
            "item_default": {"source": "item_default", "rate": "110.00"},
        }
        selected, ordered = pa.select_price_candidate(candidates, list(pa.DEFAULT_PRIORITY_ORDER))
        self.assertEqual(selected["source"], "party_price")
        self.assertEqual([c["source"] for c in ordered], ["party_price", "tier_price", "history_price", "item_default"])

        # Custom order putting history_price ahead of party_price
        selected2, _ = pa.select_price_candidate(candidates, ["history_price", "party_price", "tier_price"])
        self.assertEqual(selected2["source"], "history_price")

        # No candidates -> source="none"
        empty, ordered_empty = pa.select_price_candidate({}, list(pa.DEFAULT_PRIORITY_ORDER))
        self.assertEqual(empty["source"], "none")
        self.assertIsNone(empty["rate"])
        self.assertEqual(ordered_empty, [])

    def test_check_minimum_sale_handles_stock_and_alt_uom(self):
        # Stock UOM: 80 < 85 -> warning
        res = pa.check_minimum_sale("80.00", "85.00", conversion_factor=1)
        self.assertTrue(res["belowMinimumSale"])
        self.assertIn("80.00", res["warning"])
        self.assertIn("85.00", res["warning"])

        # Box (50 pcs): 4500 / 50 = 90 >= 85 -> ok
        res_box_ok = pa.check_minimum_sale("4500.00", "85.00", conversion_factor=50)
        self.assertFalse(res_box_ok["belowMinimumSale"])
        self.assertEqual(res_box_ok["stockUomRate"], "90.00")
        self.assertIsNone(res_box_ok["warning"])

        # Box (50 pcs): 4000 / 50 = 80 < 85 -> warning
        res_box_low = pa.check_minimum_sale("4000.00", "85.00", conversion_factor=50)
        self.assertTrue(res_box_low["belowMinimumSale"])
        self.assertEqual(res_box_low["stockUomRate"], "80.00")

        # No minimum configured -> never warns
        res_none = pa.check_minimum_sale("10.00", 0)
        self.assertFalse(res_none["belowMinimumSale"])
        self.assertIsNone(res_none["minimumSaleRate"])

    def test_normalize_priority_order_rejects_unknown_sources(self):
        with self.assertRaises(ValueError):
            pa.normalize_priority_order(["unknown_source"])
        with self.assertRaises(ValueError):
            pa.normalize_priority_order([])


if __name__ == "__main__":
    unittest.main()
