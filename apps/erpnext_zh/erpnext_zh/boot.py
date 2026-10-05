import frappe


def localize_titles(bootinfo):
    """Translate presentation titles only; preserve app IDs, routes and permissions."""
    if frappe.local.lang != "zh":
        return
    for app in bootinfo.get("app_data", []):
        if app.get("app_title"):
            app["app_title"] = frappe._(app["app_title"])
