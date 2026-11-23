"""Offline regression for presentation-only localization."""
import importlib.util
import json
import re
import sys
from html.parser import HTMLParser
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("printing", ROOT / "apps/erpnext_zh/erpnext_zh/printing.py")
printing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(printing)
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("localize", ROOT / "scripts/phase0-localize.py")
localize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(localize)


class ChineseMoneyTests(unittest.TestCase):
    def test_business_titles_preserve_transaction_direction(self):
        cases = [
            ({"doctype":"Payment Entry","payment_type":"Pay","party_type":"Customer"}, "付款单"),
            ({"doctype":"Payment Entry","payment_type":"Receive","party_type":"Supplier"}, "收款单"),
            ({"doctype":"Payment Entry","payment_type":"Internal Transfer"}, "资金转账单"),
            ({"doctype":"Stock Entry","purpose":"Material Transfer"}, "库存调拨单"),
            ({"doctype":"Stock Entry","purpose":"Material Receipt"}, "其他入库单"),
            ({"doctype":"Stock Entry","purpose":"Material Issue"}, "其他出库单"),
            ({"doctype":"Purchase Receipt","is_return":1}, "采购退货单"),
            ({"doctype":"Delivery Note","is_return":1}, "销售退货单"),
            ({"doctype":"Purchase Invoice","is_return":1}, "采购退货账务单"),
            ({"doctype":"Sales Invoice","is_return":1}, "销售贷项通知单"),
            ({"doctype":"Sales Invoice","is_return":0}, "销售发票"),
            ({"doctype":"Stock Reconciliation"}, "库存盘点调整单"),
        ]
        for doc, expected in cases:
            original = doc.copy()
            with self.subTest(doc=doc):
                self.assertEqual(printing.business_title(doc), expected)
                self.assertEqual(doc, original)

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


class PresentationTextTests(unittest.TestCase):
    def test_controlled_translation_sources_and_targets_are_nonempty(self):
        for filename in (
            "overrides.json",
            "catalog-names.json",
            "field-labels.json",
            "ui-overrides.json",
        ):
            entries = json.loads((ROOT / "phase0/localization" / filename).read_text())
            self.assertTrue(all(key and value for key, value in entries.items()), filename)

    def test_markup_only_identity_is_not_a_translation(self):
        source = '<div id="stock-levels-placeholder"></div>'
        self.assertEqual(source, localize.localize_help_prose(source))

    def test_native_help_prose_and_examples(self):
        sources = json.loads((ROOT / "phase0/localization/print-help-source.json").read_text())
        prose = json.loads((ROOT / "phase0/localization/print-help-prose.json").read_text())
        class Code(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=False)
                self.hidden = 0
                self.code = []
                self.text = []
                self.links = []
            def handle_starttag(self, tag, attrs):
                if tag in {"pre", "code"}:
                    self.hidden += 1
                self.links.extend(v for k, v in attrs if k in {"href", "src"})
            def handle_endtag(self, tag):
                if tag in {"pre", "code"}:
                    self.hidden -= 1
            def handle_data(self, data):
                (self.code if self.hidden else self.text).append(data)
            def handle_entityref(self, name):
                self.handle_data("&" + name + ";")
            def handle_charref(self, name):
                self.handle_data("&#" + name + ";")
        self.assertEqual(len(sources), 2)
        for source in sources.values():
            original, translated = Code(), Code()
            original.feed(source)
            translated.feed(localize.localize_help_prose(source, prose))
            self.assertEqual(translated.code, original.code)
            self.assertEqual(translated.links, original.links)
            self.assertFalse(re.search(r"[A-Za-z]", "".join(translated.text)))

    def test_help_preserves_code_links_and_entities(self):
        value = '<h3>自定义 CSS 帮助</h3><a href="https://example.com/Jinja">Jinja 模板</a><pre><code>CSS &lt;doc&gt; Jinja</code></pre><!--CSS-->'
        expected = '<h3>自定义 样式 帮助</h3><a href="https://example.com/Jinja">打印模板 模板</a><pre><code>CSS &lt;doc&gt; Jinja</code></pre><!--CSS-->'
        self.assertEqual(localize.localize_help_prose(value), expected)
        self.assertEqual(localize.localize_help_prose(expected), expected)

    def test_field_help_translates_prose_preserving_technical_values(self):
        entries = localize.field_help_entries()
        self.assertTrue(any("over-billing" in source for source in entries))
        for source, target in entries.items():
            with self.subTest(source=source):
                self.assertEqual(sorted(localize.PLACEHOLDER.findall(source)),
                                 sorted(localize.PLACEHOLDER.findall(target)))
                self.assertEqual(re.findall(r'href="([^"]+)"', source),
                                 re.findall(r'href="([^"]+)"', target))
                prose = re.sub(r"<code>.*?</code>", "", target, flags=re.DOTALL)
                self.assertNotRegex(re.sub(r"<[^>]+>", "", prose), r"[A-Za-z]")

    def test_ui_overlay_placeholders_and_chinese(self):
        entries = json.loads((ROOT / "phase0/localization/ui-overrides.json").read_text())
        for source, target in entries.items():
            with self.subTest(source=source):
                self.assertEqual(sorted(localize.PLACEHOLDER.findall(source)), sorted(localize.PLACEHOLDER.findall(target)))
                self.assertFalse(re.search(r"[A-Za-z]", re.sub(r"<[^>]+>", "", target)))


if __name__ == "__main__":
    unittest.main()
