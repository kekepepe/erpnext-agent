"""Offline unit tests for the W6 Business API v1 adapter."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "hardware_erp"


def load_business_api():
    fake_frappe = types.ModuleType("frappe")
    fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
    fake_frappe.PermissionError = type("PermissionError", (Exception,), {})
    fake_frappe.whitelist = lambda *a, **kw: (lambda fn: fn)
    fake_frappe.session = types.SimpleNamespace(user="Guest", data=types.SimpleNamespace(csrf_token="tok-1"))
    fake_frappe.db = types.SimpleNamespace(get_value=MagicMock(return_value="System User"))
    fake_frappe.conf = {}
    fake_frappe.get_request_header = MagicMock(return_value=None)

    fake_model = types.ModuleType("frappe.model")
    fake_workflow = types.ModuleType("frappe.model.workflow")
    fake_workflow.get_workflow = MagicMock()
    fake_workflow.is_transition_condition_satisfied = MagicMock()

    modules = {
        "frappe": fake_frappe,
        "frappe.model": fake_model,
        "frappe.model.workflow": fake_workflow,
    }
    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(
            "business_api_test_target", APP_ROOT / "hardware_erp" / "business_api.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, fake_frappe


api, _STUB_FRAPPE = load_business_api()


class BusinessApiUnitTests(unittest.TestCase):
    def test_parse_route_handles_valid_and_invalid_paths(self):
        self.assertEqual(api.parse_route("entry-options"), ("entry_options", None))
        self.assertEqual(api.parse_route("/entry-options/"), ("entry_options", None))
        self.assertEqual(api.parse_route("drafts"), ("drafts", None))
        self.assertEqual(api.parse_route("drafts/MAT-PRE-2026-00001"), ("draft", "MAT-PRE-2026-00001"))
        self.assertIsNone(api.parse_route("drafts/a/b"))
        self.assertIsNone(api.parse_route("unknown"))
        self.assertIsNone(api.parse_route(""))

    def test_format_quantity_normalizes_decimal_strings(self):
        self.assertEqual(api.format_quantity(12.0), "12")
        self.assertEqual(api.format_quantity("12.500000"), "12.5")
        self.assertEqual(api.format_quantity("0.125"), "0.125")
        self.assertEqual(api.format_quantity(100), "100")

    def test_canonical_digest_is_key_order_independent(self):
        a = {"kind": "purchase_receipt", "lines": [{"quantity": "2", "productId": "X"}]}
        b = {"lines": [{"productId": "X", "quantity": "2"}], "kind": "purchase_receipt"}
        self.assertEqual(api.canonical_digest(a), api.canonical_digest(b))

    def test_validate_payload_shape_accepts_valid_create_and_update(self):
        body = {
            "kind": "purchase_receipt",
            "companyId": "R1合成发布验证公司",
            "partnerId": "R1合成供应商",
            "postingDate": "2026-11-24",
            "lines": [{"productId": "R1-DEMO-SCREW", "warehouseId": "R1测试主仓 - R1D", "quantity": "12.5"}],
        }
        api.validate_payload_shape(body, updating=False)
        api.validate_payload_shape({**body, "revision": 1}, updating=True)

    def test_validate_payload_shape_rejects_extra_fields_and_bad_quantities(self):
        bad = {
            "kind": "sales_delivery",
            "companyId": "C1",
            "partnerId": "P1",
            "postingDate": "2026-02-30",
            "status": "submitted",
            "lines": [
                {"productId": "I1", "warehouseId": "W1", "quantity": "0", "rate": 10},
                {"productId": "", "warehouseId": "W1", "quantity": "1234567890"},
            ],
        }
        with self.assertRaises(api.ApiError) as ctx:
            api.validate_payload_shape(bad, updating=True)
        self.assertEqual(ctx.exception.status, 422)
        paths = {item["path"] for item in ctx.exception.error["issues"]}
        self.assertEqual(
            paths,
            {"status", "postingDate", "revision", "lines.0.rate", "lines.0.quantity", "lines.1.productId", "lines.1.quantity"},
        )

    def test_serialize_draft_maps_purchase_and_sales_fields(self):
        row = types.SimpleNamespace(item_code="R1-DEMO-SCREW", warehouse="R1测试主仓 - R1D", qty=5.0)
        pr = types.SimpleNamespace(
            name="MAT-PRE-2026-00001",
            company="R1合成发布验证公司",
            supplier="R1合成供应商",
            posting_date="2026-11-24",
            custom_w6_revision=2,
            items=[row],
            get=lambda k, d=None: getattr(pr, k, d),
        )
        result = api.serialize_draft(pr, "purchase_receipt")
        self.assertEqual(
            result,
            {
                "id": "MAT-PRE-2026-00001",
                "kind": "purchase_receipt",
                "companyId": "R1合成发布验证公司",
                "partnerId": "R1合成供应商",
                "postingDate": "2026-11-24",
                "lines": [{"productId": "R1-DEMO-SCREW", "warehouseId": "R1测试主仓 - R1D", "quantity": "5"}],
                "revision": 2,
                "status": "draft",
            },
        )

    def test_require_auth_rejects_guest_website_user_and_missing_csrf(self):
        fake_frappe = types.SimpleNamespace(
            session=types.SimpleNamespace(user="Guest", data=types.SimpleNamespace(csrf_token="tok-1")),
            db=types.SimpleNamespace(get_value=MagicMock(return_value="System User")),
            conf={},
            get_request_header=MagicMock(return_value=None),
        )
        with patch.object(api, "frappe", fake_frappe), patch.dict(sys.modules, {"frappe": fake_frappe}):
            with self.assertRaises(api.ApiError) as ctx:
                api._require_auth(is_write=False)
            self.assertEqual(ctx.exception.status, 401)

            fake_frappe.session.user = "web@example.invalid"
            fake_frappe.db.get_value.return_value = "Website User"
            with self.assertRaises(api.ApiError) as ctx:
                api._require_auth(is_write=False)
            self.assertEqual(ctx.exception.status, 403)

            fake_frappe.db.get_value.return_value = "System User"
            self.assertEqual(api._require_auth(is_write=False), "web@example.invalid")
            with self.assertRaises(api.ApiError) as ctx:
                api._require_auth(is_write=True)
            self.assertEqual(ctx.exception.status, 403)

            fake_frappe.get_request_header.return_value = "tok-1"
            self.assertEqual(api._require_auth(is_write=True), "web@example.invalid")


if __name__ == "__main__":
    unittest.main()
