"""Configure native imports and keep transaction imports on the draft workflow."""

from hardware_erp.trade_fields import TRADE_DOCUMENTS

TRANSACTIONS = (*TRADE_DOCUMENTS, "Stock Entry", "Stock Reconciliation", "Payment Entry")


def configure():
    from frappe import get_meta
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    if not get_meta("Stock Reconciliation").allow_import:
        make_property_setter("Stock Reconciliation", None, "allow_import", 1, "Check", for_doctype=True)


def keep_draft(doc, method=None):
    import frappe

    if doc.reference_doctype in TRANSACTIONS and frappe.utils.cint(doc.submit_after_import):
        frappe.throw("业务单据请先导入草稿，再按原有流程提交。")
