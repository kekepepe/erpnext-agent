import hashlib as _hashlib
from pathlib import Path as _Path


def _asset(path):
    # Native nginx serves /assets with a long cache lifetime. Content versions
    # ensure an ordinary Desk reload sees updated presentation code and styles.
    digest = _hashlib.sha256((_Path(__file__).parent / "public" / path).read_bytes()).hexdigest()[:16]
    return f"/assets/erpnext_zh/{path}?v={digest}"


app_name = "erpnext_zh"
app_title = "简体中文展示"
app_publisher = "ERPNext Agent Project"
app_description = "Simplified Chinese presentation without core or business-rule changes"
app_email = "localization@example.invalid"
app_license = "MIT"
required_apps = ["erpnext"]
boot_session = "erpnext_zh.boot.localize_titles"
app_include_js = [_asset("js/" + name + ".js") for name in ["presentation", "form_display", "workbench", "workbench_data_tools", "workbench_form", "trade_forms"]]
jinja = {"methods": ["erpnext_zh.printing.chinese_money", "erpnext_zh.printing.business_title"]}

app_include_css = [_asset("css/workbench.css")]

doctype_list_js = {doctype: "public/js/workbench_list.js" for doctype in [
    "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Sales Order",
    "Delivery Note", "Sales Invoice", "Stock Entry", "Stock Reconciliation", "Payment Entry",
    "Quotation", "Item", "Item Group", "Customer", "Supplier", "Warehouse", "UOM", "Item Price", "Price List",
]}
