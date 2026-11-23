#!/usr/bin/env python3
"""Render unsaved synthetic variants with native print API; never insert or save."""
import copy
import importlib.util
import json
import os
import re
from pathlib import Path

from phase0_api import ERPNextAPI, validate_disposable_url

ROOT = Path(__file__).resolve().parents[1]


def main():
    api = ERPNextAPI(validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080")))
    api.login("Administrator", os.environ.get("PHASE0_PASSWORD", "admin"))
    spec = importlib.util.spec_from_file_location("localize", ROOT / "scripts/phase0-localize.py")
    localize = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(localize)
    _, terms = localize.dictionary(api)
    # Independent expected text, including refund direction and cancelled state.
    cases = [
        ("Payment Entry", {"payment_type":"Pay", "party_type":"Supplier"}, ["付款单","支付供应商","付款金额"], ["收款金额"]),
        ("Payment Entry", {"payment_type":"Receive", "party_type":"Customer"}, ["收款单","客户付款","收款金额"], ["付款金额"]),
        ("Payment Entry", {"payment_type":"Pay", "party_type":"Customer"}, ["付款单","退还客户","付款金额"], ["收款金额"]),
        ("Payment Entry", {"payment_type":"Receive", "party_type":"Supplier"}, ["收款单","供应商退款","收款金额"], ["付款金额"]),
        ("Payment Entry", {"payment_type":"Internal Transfer"}, ["资金转账单","企业内部账户划转","转出金额","转入金额"], ["付款金额","收款金额"]),
        ("Stock Entry", {"purpose":"Material Transfer"}, ["库存调拨单","来源","去向"], []),
        ("Stock Entry", {"purpose":"Material Receipt"}, ["其他入库单"], []),
        ("Stock Entry", {"purpose":"Material Issue"}, ["其他出库单"], []),
        ("Stock Reconciliation", {}, ["库存盘点调整单","盘点价值差额"], []),
        ("Purchase Receipt", {"is_return":1}, ["采购退货单"], []),
        ("Delivery Note", {"is_return":1}, ["销售退货单"], []),
        ("Purchase Invoice", {"is_return":1,"update_stock":0}, ["采购退货账务单","不更新库存","不代表已开具税务发票"], []),
        ("Sales Invoice", {"is_return":1,"update_stock":1}, ["销售贷项通知单","同时更新库存","不代表已开具税务发票"], []),
        ("Purchase Order", {"docstatus":2,"workflow_state":"Rejected"}, ["已撤销","含税总额","舍入后金额"], ["已拒绝"]),
    ]
    sources = {}
    rendered, denied = 0, 0
    for dt, changes, expected, forbidden in cases:
        if dt not in sources:
            rows = api.list_docs(dt, ["name"], [["company","=","Phase Zero Hardware Trading Demo"],["docstatus","=",1]], 1)
            if not rows:
                raise ValueError("Missing synthetic source " + dt)
            sources[dt] = api.get_doc(dt, rows[0]["name"])
        doc = copy.deepcopy(sources[dt])
        doc.update(changes)
        # Server renders supplied JSON in memory; these are semantic previews,
        # not valid/approved business transactions and are never persisted.
        try:
            result = api.request("POST", "/api/method/frappe.www.printview.get_html_and_style", {
                "doc":json.dumps(doc), "print_format":terms[dt]+"（简体中文）", "no_letterhead":1,
            })["message"]
        except RuntimeError as error:
            if doc["docstatus"] == 2 and "HTTP 403" in str(error) and "PermissionError" in str(error) and "不允许打印已取消的单据" in str(error):
                denied += 1
                continue
            raise
        if doc["docstatus"] == 2:
            raise ValueError("Cancelled print unexpectedly permitted; review native print policy")
        html = result.get("html") or ""
        if any(text not in html for text in expected) or any(text in html for text in forbidden):
            raise ValueError("Print semantics mismatch " + dt + " " + json.dumps(changes))
        if not re.search(r"<h1>[^<]+</h1>", html):
            raise ValueError("Missing document heading")
        rendered += 1
    for dt, original in sources.items():
        if api.get_doc(dt, original["name"]) != original:
            raise ValueError("Source changed during read-only print verification " + dt)
    print(json.dumps({"unsaved_native_previews":rendered,"cancelled_print_denied":denied,"source_documents_unchanged":len(sources),"result":"PASS"}))


if __name__ == "__main__":
    main()
