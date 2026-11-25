"""Same-origin W6 receipt/delivery entry page inside ERPNext."""

import frappe

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/w6-entry"
        raise frappe.Redirect
    if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
        frappe.throw("仅系统用户可以访问出入库录单。", frappe.PermissionError)
    context.no_header = 1
    context.no_footer = 1
    context.title = "五金进销存 · 出入库录单"
    context.csrf_token = frappe.sessions.get_csrf_token()
