"""Read-only workbench permission isolation regression (no database access)."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

PATH = Path(__file__).resolve().parents[1] / 'apps/erpnext_zh/erpnext_zh/workbench.py'

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.frappe = types.SimpleNamespace(
            whitelist=lambda: lambda fn: fn,
            session=types.SimpleNamespace(user='buyer@example.invalid'),
            PermissionError=PermissionError,
            throw=Mock(side_effect=PermissionError),
            db=types.SimpleNamespace(get_value=Mock(return_value='System User')),
            has_permission=Mock(return_value=False),
            get_roles=Mock(return_value=[]),
            get_doc=Mock(return_value=types.SimpleNamespace(disabled=False, ref_doctype='GL Entry', is_permitted=lambda: False)),
            get_meta=Mock(return_value=types.SimpleNamespace(issingle=False)),
            get_list=Mock(return_value=[]),
            _=lambda value: value,
        )
        self.patch = patch.dict(sys.modules, {'frappe': self.frappe})
        self.patch.start(); self.addCleanup(self.patch.stop)
        spec = importlib.util.spec_from_file_location('workbench_test_target', PATH)
        self.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)

    def test_guest_and_website_users_are_denied_before_queries(self):
        self.frappe.session.user = 'Guest'
        with self.assertRaises(PermissionError): self.module.get_context()
        self.frappe.get_list.assert_not_called()
        self.frappe.session.user = 'customer@example.invalid'
        self.frappe.db.get_value.return_value = 'Website User'
        with self.assertRaises(PermissionError): self.module.get_context()

    def test_no_permissions_has_no_navigation_or_recent_documents(self):
        result = self.module.get_context()
        self.assertEqual(result['groups'], []); self.assertEqual(result['recent'], [])
        self.assertFalse(result['can_view_actions']); self.frappe.get_list.assert_not_called()

    def test_permission_queries_are_bounded_and_doctype_deduplicated(self):
        self.frappe.has_permission.side_effect = lambda dt, permission: dt == 'Purchase Receipt' and permission == 'read'
        self.frappe.get_list.return_value = [{'name': 'PR-1', 'modified': '2026-10-28', 'docstatus': 0}]
        result = self.module.get_context()
        self.assertEqual([g['id'] for g in result['groups']], ['purchase'])
        items = result['groups'][0]['items']
        self.assertEqual([i['filters']['is_return'] for i in items], [0, 1])
        self.assertTrue(all(not i['can_create'] for i in items))
        self.frappe.get_list.assert_called_once_with('Purchase Receipt', fields=['name','modified','docstatus'], order_by='modified desc', page_length=3)
        self.assertEqual(len(result['recent']), 1)

    def test_permissions_are_not_cached_across_sessions(self):
        self.frappe.has_permission.side_effect = lambda dt, permission: dt == 'Item'
        self.assertTrue(self.module.get_context()['groups'])
        self.frappe.session.user = 'other@example.invalid'
        self.frappe.has_permission.side_effect = lambda dt, permission: False
        self.assertEqual(self.module.get_context()['groups'], [])

    def test_tools_require_target_and_import_job_permissions(self):
        permissions = {("Purchase Order", "read"), ("Purchase Order", "create"),
                       ("Purchase Order", "import"), ("Purchase Order", "print")}
        self.frappe.has_permission.side_effect = lambda dt, perm: (dt, perm) in permissions
        self.frappe.get_meta.return_value.allow_import = True
        def purchase_order():
            return self.module.allowed_catalog()[0]["items"][0]
        self.assertTrue(purchase_order()["can_print"])
        self.assertFalse(purchase_order()["can_export"])
        self.assertFalse(purchase_order()["can_import"])
        permissions.update({("Data Import", "create"), ("Purchase Order", "export")})
        self.assertTrue(purchase_order()["can_import"])
        self.assertTrue(purchase_order()["can_export"])
        self.frappe.get_meta.return_value.allow_import = False
        self.assertFalse(purchase_order()["can_import"])

    def test_report_requires_both_report_roles_and_doctype_permission(self):
        self.frappe.get_doc.return_value.is_permitted = lambda: True
        self.assertEqual(self.module.allowed_catalog(), [])
        self.frappe.has_permission.side_effect = lambda dt, permission: dt == 'GL Entry' and permission == 'report'
        self.assertEqual(len(next(group for group in self.module.allowed_catalog() if group['id'] == 'reports')['items']), 7)
        self.frappe.get_doc.return_value.disabled = True
        self.assertEqual(self.module.allowed_catalog(), [])

if __name__ == '__main__': unittest.main()
