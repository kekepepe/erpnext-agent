"""Read-only draft totals using the same ERPNext calculator as document save."""

import frappe
from erpnext.accounts.doctype.pricing_rule.utils import get_applied_pricing_rules
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

from hardware_erp.trade_fields import TRADE_DOCUMENTS, calculate_line_amounts

HEADER_FIELDS = (
    "company", "currency", "conversion_rate", "transaction_date", "posting_date",
    "bill_date", "tax_category", "is_return", "return_against", "is_debit_note",
    "apply_discount_on", "additional_discount_percentage", "discount_amount",
    "disable_rounded_total", "is_cash_or_non_trade_discount", "ignore_pricing_rule",
)
ITEM_FIELDS = (
    "item_code", "qty", "rate", "price_list_rate", "discount_percentage",
    "discount_amount", "margin_type", "margin_rate_or_amount", "is_alternative",
    "item_tax_template", "pricing_rules", "weight_per_unit", "weight_uom",
)
TAX_FIELDS = (
    "account_head", "charge_type", "row_id", "rate", "tax_amount", "included_in_print_rate",
    "included_in_paid_amount", "category", "add_deduct_tax", "dont_recompute_tax",
)


def selected_fields(values, names):
    return {name: values[name] for name in names if name in values}


@frappe.whitelist(methods=["POST"])
@frappe.read_only()
def preview(draft: dict | str):
    draft = frappe.parse_json(draft)
    if not isinstance(draft, dict):
        frappe.throw("请提供有效的单据草稿。")
    doctype = draft.get("doctype")
    if doctype not in TRADE_DOCUMENTS:
        frappe.throw("该单据类型暂不支持金额预览。")

    name = draft.get("name")
    if name:
        saved = frappe.get_doc(doctype, name)
        saved.check_permission("write")
        if saved.docstatus != 0:
            return None

    # The native shipping rule adds its own derived tax/expense rows. Special
    # invoices require the posting/advance context and remain on saved totals.
    if any(draft.get(field) for field in ("shipping_rule", "is_pos", "is_consolidated")):
        return None

    source_rows = draft.get("items") or []
    taxes = draft.get("taxes") or []
    if len(source_rows) > 500 or len(taxes) > 100:
        return None
    if not draft.get("company") or not draft.get("currency") or not source_rows:
        return None
    if any(not row.get("item_code") or not row.get("uom") for row in source_rows):
        return None

    doc = frappe.get_doc({
        "doctype": doctype,
        **selected_fields(draft, HEADER_FIELDS),
        "items": [selected_fields(row, ITEM_FIELDS) for row in source_rows],
        "taxes": [selected_fields(row, TAX_FIELDS) for row in taxes],
    })
    if not name or saved.company != doc.company:
        doc.check_permission("create")
    if doc.get("return_against"):
        frappe.get_doc(doctype, doc.return_against).check_permission("read")

    # Native row calculation reads pricing rules and tax templates. Check linked
    # document permissions before using these values in a request-side calculation.
    linked = {("Item", row.item_code) for row in doc.items}
    linked.update(("Item Tax Template", row.item_tax_template) for row in doc.items if row.item_tax_template)
    if not doc.ignore_pricing_rule:
        for row in doc.items:
            linked.update(("Pricing Rule", rule) for rule in get_applied_pricing_rules(row.pricing_rules))
    for dt, value in linked:
        frappe.get_doc(dt, value).check_permission("read")

    calculate_taxes_and_totals(doc)
    calculate_line_amounts(doc)
    return {
        "rows": [
            {
                "net_rate": row.net_rate,
                "net_amount": row.net_amount,
                "gross_rate": row.custom_trade_gross_rate,
                "gross_amount": row.custom_trade_gross_amount,
                "tax_percent": row.custom_trade_tax_percent,
            }
            for row in doc.items
        ],
        "net_total": doc.net_total,
        "tax_total": doc.total_taxes_and_charges,
        "grand_total": doc.grand_total,
    }
