"""Offline tests for conservative source triage, not UI acceptance."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("phase0-audit-language-ui.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LanguageAuditTests(unittest.TestCase):
    def test_python_literal_and_context(self):
        source = '\nfrappe._("Save", context="button")\n_("First " "second")\n_(key)\n_(f"Hello {name}")\n'
        self.assertEqual(list(audit.python_messages(source)), [(2, "Save", "button"), (3, "First second", None)])

    def test_visible_prose_preserves_acronyms(self):
        self.assertEqual(audit.visible('<p>自定义 CSS 帮助</p><pre>english_code()</pre><a href="https://example.com">说明</a>'), '自定义 CSS 帮助 说明')
        self.assertEqual(audit.visible('<style>body{color:red}</style><script>run()</script>保存 {0}'), '保存')

    def test_context_fallback_and_residuals(self):
        row = dict(kind="gettext", source="Save", context="button")
        self.assertEqual(audit.classify(row, {"Save": "保存", "Save:button": "储存"}), ("translated", "储存"))
        self.assertEqual(audit.classify(row, {}), ("missing_or_identity", None))
        self.assertEqual(audit.classify(row, {"Save": "保存 CSS"}), ("latin_in_translation", "保存 CSS"))
        self.assertEqual(audit.classify(dict(kind="template_candidate"), {}), ("needs_runtime_review", None))


if __name__ == "__main__":
    unittest.main()
