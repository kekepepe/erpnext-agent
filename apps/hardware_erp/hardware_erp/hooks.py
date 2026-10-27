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
