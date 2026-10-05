"""Offline regression for presentation-only localization."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("printing", ROOT / "apps/erpnext_zh/erpnext_zh/printing.py")
printing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(printing)


class ChineseMoneyTests(unittest.TestCase):
    def test_currency_values(self):
        cases = {
            "0": "零元整", "0.01": "零元零壹分", "1": "壹元整",
            "10": "壹拾元整", "101": "壹佰零壹元整",
            "10001": "壹万零壹元整", "100000001": "壹亿零壹元整",
            "100010000": "壹亿零壹万元整", "100100000": "壹亿零壹拾万元整",
            "1234.56": "壹仟贰佰叁拾肆元伍角陆分",
            "-32.5": "负叁拾贰元伍角", "1.005": "壹元零壹分",
        }
        for amount, expected in cases.items():
            with self.subTest(amount=amount):
                self.assertEqual(printing.chinese_money(amount), expected)

    def test_range_limit(self):
        with self.assertRaises(ValueError):
            printing.chinese_money("10000000000000000")


if __name__ == "__main__":
    unittest.main()
