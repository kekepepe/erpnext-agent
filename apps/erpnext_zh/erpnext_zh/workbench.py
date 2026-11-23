"""Read-only workbench. Native permissions remain authoritative on every route."""
import json
from pathlib import Path
import frappe

CATALOG = json.loads(Path(__file__).with_name("workbench_catalog.json").read_text())

PRICE_TIERS = json.loads(Path(__file__).with_name("price_tiers.json").read_text())

def allowed_catalog():
    groups = []
    can_manage_imports = frappe.has_permission("Data Import", "create")
    for group in CATALOG:
        if group["id"] == "settings" and "System Manager" not in frappe.get_roles():
            continue
        items = []
        for source in group["items"]:
            item = dict(source)
            if "report" in item:
                report = frappe.get_doc("Report", item["report"])
                if report.disabled or not report.is_permitted():
                    continue
                if not frappe.has_permission(report.ref_doctype, "report"):
                    continue
                item["can_export"] = bool(frappe.has_permission(report.ref_doctype, "export"))
                item["can_print"] = bool(frappe.has_permission(report.ref_doctype, "print"))
            else:
                dt = item["doctype"]
                if not frappe.has_permission(dt, "read"):
                    continue
                meta = frappe.get_meta(dt)
                item["single"] = bool(meta.issingle)
                item["can_create"] = bool(frappe.has_permission(dt, "create"))
                if group["id"] != "settings":
                    item["can_import"] = bool(
                        getattr(meta, "allow_import", False) and can_manage_imports
                        and item["can_create"] and frappe.has_permission(dt, "import")
                    )
                    item["can_export"] = bool(frappe.has_permission(dt, "export"))
                    item["can_print"] = bool(frappe.has_permission(dt, "print"))
            items.append(item)
        if items:
            groups.append(dict(id=group["id"], label=group["label"], items=items))
    return groups

@frappe.whitelist()
def get_context():
    if frappe.session.user == "Guest":
        frappe.throw("请先登录", frappe.PermissionError)
    if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
        frappe.throw("仅系统用户可以访问工作台", frappe.PermissionError)
    groups = allowed_catalog()
    recent = []
    seen = set()
    for group in groups:
        if group["id"] not in ("purchase", "sales", "stock", "payment"):
            continue
        for item in group["items"]:
            if "doctype" not in item:
                continue
            dt = item["doctype"]
            if dt in seen:
                continue
            seen.add(dt)
            # get_list applies user permissions and permission query conditions.
            for doc in frappe.get_list(dt, fields=["name", "modified", "docstatus"],
                                       order_by="modified desc", page_length=3):
                recent.append(dict(doc, doctype=dt, label=frappe._(dt)))
    recent.sort(key=lambda doc: str(doc["modified"]), reverse=True)
    return dict(user=frappe.session.user, groups=groups, recent=recent[:12], price_tiers=PRICE_TIERS,
                can_view_actions=bool(frappe.has_permission("Workflow Action", "read")))
