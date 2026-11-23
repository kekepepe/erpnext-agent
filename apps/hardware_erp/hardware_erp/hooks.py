from hardware_erp.trade_fields import TRADE_DOCUMENTS as _trade_documents


app_name = 'hardware_erp'
app_title = '审批边界守卫'
app_publisher = 'ERPNext Agent Project'
app_description = 'Server-side approval validation without ERPNext Core changes'
app_email = 'approval@example.invalid'
app_license = 'MIT'
required_apps = ['erpnext']

doc_events = {
    doctype: {
        'before_validate': 'hardware_erp.approval.check_before_validation',
        'before_submit': 'hardware_erp.approval.check_transition',
        'before_cancel': 'hardware_erp.approval.check_transition',
        'before_update_after_submit': 'hardware_erp.approval.check_before_validation',
    }
    for doctype in (
        'Purchase Order', 'Sales Order', 'Payment Entry', 'Purchase Receipt',
        'Delivery Note', 'Purchase Invoice', 'Sales Invoice', 'Stock Entry',
        'Stock Reconciliation',
    )
}


after_install = ["hardware_erp.trade_fields.after_install", "hardware_erp.data_import.configure"]

for _doctype in _trade_documents:
    _events = doc_events.setdefault(_doctype, {})
    _product_details = "hardware_erp.trade_fields.populate_product_details"
    _existing = _events.get("before_validate")
    _events["before_validate"] = [_existing, _product_details] if _existing else _product_details
    _events["before_save"] = "hardware_erp.trade_fields.calculate_line_amounts"
    _transition = _events.get("before_submit")
    _amounts = "hardware_erp.trade_fields.calculate_line_amounts"
    _events["before_submit"] = [_transition, _amounts] if _transition else _amounts

doc_events["Item"] = {"after_insert": "hardware_erp.trade_fields.create_initial_prices"}

doc_events["Data Import"] = {"before_validate": "hardware_erp.data_import.keep_draft"}
