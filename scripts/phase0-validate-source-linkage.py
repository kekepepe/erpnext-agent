#!/usr/bin/env python3
"""Validate 2A source-document linkage and remaining-quantity rules on a disposable R1 site.

Exercises:
1. Native Quotation -> Sales Order mapping preserves customer, item, UOM and prevdoc_docname.
2. Unauthorized role (r1.sales) rejected with 403 on purchase_receipt source-orders.
3. Unapproved Draft Purchase Order is hidden from /source-orders and rejected (422) on draft creation.
4. Approved Purchase Order (qty=10) appears in /source-orders with remainingQty="10".
5. Over-quantity receipt (qty=11) rejected (422).
6. Partial Purchase Receipt (qty=4) linked via Business API writes native purchase_order &
   purchase_order_item; after approval, /source-orders updates to fulfilledQty="4", remainingQty="6".
7. Closed Purchase Order disappears from /source-orders and is rejected (422) on draft creation.
8. Cleans up synthetic test documents via native R1 cancellation workflows so stock/GL return to zero.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

from phase0_api import ERPNextAPI, validate_disposable_url

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/business/v1"


def raw_request(api: ERPNextAPI, method: str, path: str, body=None, key: str | None = None):
    data = None
    headers = {"Accept": "application/json"}
    if api.csrf_token:
        headers["X-Frappe-CSRF-Token"] = api.csrf_token
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if key is not None:
        headers["Idempotency-Key"] = key
    req = urllib.request.Request(f"{api.base_url}{PREFIX}{path}", data=data, headers=headers, method=method)
    try:
        with api.opener.open(req, timeout=30) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {"raw": raw}
        return err.code, parsed


def apply_workflow(api: ERPNextAPI, doctype: str, name: str, action: str):
    doc = api.get_doc(doctype, name)
    return api.call("frappe.model.workflow.apply_workflow", {"doc": doc, "action": action})


def main():
    base = validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"))
    role_password = os.environ.get("PHASE0_ROLE_PASSWORD", "p0-local-only")
    admin_user = os.environ.get("PHASE0_USERNAME", "Administrator")
    admin_password = os.environ.get("PHASE0_PASSWORD", "admin")

    access = json.loads((ROOT / "phase0/release-access.json").read_text())
    baseline = json.loads((ROOT / "phase0/release-baseline.json").read_text())

    company = access["company"]
    main_wh = access["warehouses"][0]
    supplier = baseline["supplier"]
    customer = baseline["customer"]
    item_code = baseline["item"]["item_code"]

    admin = ERPNextAPI(base)
    admin.login(admin_user, admin_password)

    purchase = ERPNextAPI(base)
    purchase.login(access["users"]["purchase"]["email"], role_password)

    purchase_mgr = ERPNextAPI(base)
    purchase_mgr.login(access["users"]["purchase_manager"]["email"], role_password)

    sales = ERPNextAPI(base)
    sales.login(access["users"]["sales"]["email"], role_password)

    stock = ERPNextAPI(base)
    stock.login(access["users"]["stock"]["email"], role_password)

    stock_mgr = ERPNextAPI(base)
    stock_mgr.login(access["users"]["stock_manager"]["email"], role_password)

    finance_rev = ERPNextAPI(base)
    finance_rev.login(access["users"]["finance_reviewer"]["email"], role_password)

    # 1. Native Quotation -> Sales Order mapping traceability
    qtn = admin.insert("Quotation", {
        "company": company,
        "quotation_to": "Customer",
        "party_name": customer,
        "transaction_date": "2026-11-24",
        "valid_till": "2026-12-24",
        "currency": "CNY",
        "selling_price_list": baseline["selling_price_list"],
        "items": [{"item_code": item_code, "qty": 2, "uom": "Piece", "rate": 100}],
    })
    qtn_name = qtn["name"]
    so_name = None
    try:
        admin.submit(admin.get_doc("Quotation", qtn_name))
        mapped_so = admin.call("erpnext.selling.doctype.quotation.quotation.make_sales_order", {"source_name": qtn_name})
        mapped_so["delivery_date"] = "2026-11-30"
        mapped_so["items"][0]["warehouse"] = main_wh
        saved_so = sales.insert("Sales Order", mapped_so)
        so_name = saved_so["name"]
        assert saved_so["customer"] == customer
        assert saved_so["items"][0]["item_code"] == item_code
        assert saved_so["items"][0]["uom"] == "Piece"
        assert saved_so["items"][0]["prevdoc_docname"] == qtn_name
        assert int(saved_so["docstatus"]) == 0
        print(f"PASS 1: Quotation {qtn_name} -> Sales Order {so_name} traceability verified")
    finally:
        if so_name:
            try:
                admin.request("DELETE", ERPNextAPI.resource_path("Sales Order", so_name))
            except Exception:
                pass
        try:
            qdoc = admin.get_doc("Quotation", qtn_name)
            if qdoc and int(qdoc["docstatus"]) == 1:
                admin.cancel(qdoc)
            elif qdoc and int(qdoc["docstatus"]) == 0:
                admin.request("DELETE", ERPNextAPI.resource_path("Quotation", qtn_name))
        except Exception:
            pass

    # 2. Unauthorized role (r1.sales) denied on purchase_receipt source-orders
    status, denied = raw_request(sales, "GET", "/source-orders?kind=purchase_receipt")
    assert status == 403, f"Expected 403 for sales on purchase source-orders, got {status}: {denied}"
    print("PASS 2: unauthorized role rejected with 403 on /source-orders")

    # 3-7. Purchase Order -> Partial Purchase Receipt -> Remaining Qty -> Closed PO rejection
    po = purchase.insert("Purchase Order", {
        "company": company,
        "supplier": supplier,
        "transaction_date": "2026-11-24",
        "schedule_date": "2026-11-30",
        "currency": "CNY",
        "buying_price_list": baseline["buying_price_list"],
        "items": [{"item_code": item_code, "qty": 10, "uom": "Piece", "rate": 60, "warehouse": main_wh}],
    })
    po_name = po["name"]
    po_item_name = po["items"][0]["name"]
    pr_name = None
    po_closed = False
    po_approved = False
    pr_approved = False

    try:
        # 3. Unapproved Draft PO must NOT appear in /source-orders and MUST be rejected on POST /drafts
        status, src_resp = raw_request(stock, "GET", "/source-orders?kind=purchase_receipt")
        assert status == 200, src_resp
        assert not any(o["id"] == po_name for o in src_resp["data"]["orders"]), "Draft PO leaked into /source-orders"

        draft_link_payload = {
            "kind": "purchase_receipt",
            "companyId": company,
            "partnerId": supplier,
            "postingDate": "2026-11-24",
            "lines": [{
                "productId": item_code,
                "warehouseId": main_wh,
                "quantity": "4",
                "sourceOrderId": po_name,
                "sourceOrderItemId": po_item_name,
            }],
        }
        status, err = raw_request(stock, "POST", "/drafts", draft_link_payload, key=f"draftpo-{uuid4().hex}")
        assert status == 422, f"Expected 422 for unapproved PO link, got {status}: {err}"
        print("PASS 3: unapproved Draft PO hidden from /source-orders and rejected (422)")

        # 4. Approve PO via R1 workflow -> appears in /source-orders with remainingQty="10"
        apply_workflow(purchase_mgr, "Purchase Order", po_name, "批准")
        po_approved = True

        status, src_resp = raw_request(stock, "GET", "/source-orders?kind=purchase_receipt")
        assert status == 200, src_resp
        matched = next((o for o in src_resp["data"]["orders"] if o["id"] == po_name), None)
        assert matched is not None, f"Approved PO {po_name} missing from /source-orders"
        assert matched["lines"][0]["orderedQty"] == "10"
        assert matched["lines"][0]["fulfilledQty"] == "0"
        assert matched["lines"][0]["remainingQty"] == "10"
        print("PASS 4: approved PO listed with remainingQty=10")

        # 5. Over-quantity receipt (qty=11) rejected with 422
        over_payload = {
            **draft_link_payload,
            "lines": [{**draft_link_payload["lines"][0], "quantity": "11"}],
        }
        status, over_err = raw_request(stock, "POST", "/drafts", over_payload, key=f"over-{uuid4().hex}")
        assert status == 422, f"Expected 422 for over-quantity receipt, got {status}: {over_err}"
        print("PASS 5: over-quantity receipt rejected (422)")

        # 6. Partial receipt (qty=4) linked natively; after approval remainingQty becomes 6
        status, created = raw_request(stock, "POST", "/drafts", draft_link_payload, key=f"part-{uuid4().hex}")
        assert status == 201, f"Expected 201 for linked partial PR, got {status}: {created}"
        pr_name = created["data"]["id"]
        assert created["data"]["lines"][0]["sourceOrderId"] == po_name
        assert created["data"]["lines"][0]["sourceOrderItemId"] == po_item_name

        native_pr = admin.get_doc("Purchase Receipt", pr_name)
        assert native_pr["items"][0]["purchase_order"] == po_name
        assert native_pr["items"][0]["purchase_order_item"] == po_item_name

        apply_workflow(stock_mgr, "Purchase Receipt", pr_name, "批准")
        pr_approved = True

        status, src_after = raw_request(stock, "GET", "/source-orders?kind=purchase_receipt")
        assert status == 200, src_after
        matched_after = next((o for o in src_after["data"]["orders"] if o["id"] == po_name), None)
        assert matched_after is not None, "Partially received PO missing from /source-orders"
        assert matched_after["lines"][0]["fulfilledQty"] == "4"
        assert matched_after["lines"][0]["remainingQty"] == "6"
        print("PASS 6: partial receipt updated PO remainingQty 10 -> 6 with native link preserved")

        # 7. Close PO -> disappears from /source-orders and rejected (422) on new draft
        purchase_mgr.call(
            "erpnext.buying.doctype.purchase_order.purchase_order.update_status",
            {"status": "Closed", "name": po_name},
        )
        po_closed = True

        status, src_closed = raw_request(stock, "GET", "/source-orders?kind=purchase_receipt")
        assert status == 200, src_closed
        assert not any(o["id"] == po_name for o in src_closed["data"]["orders"]), "Closed PO leaked into /source-orders"

        status, closed_err = raw_request(stock, "POST", "/drafts", draft_link_payload, key=f"closed-{uuid4().hex}")
        assert status == 422, f"Expected 422 for closed PO link, got {status}: {closed_err}"
        print("PASS 7: closed PO hidden from /source-orders and rejected (422)")

    finally:
        # Reverse cleanup via native R1 workflows so stock/GL return to zero
        if po_closed:
            try:
                purchase_mgr.call(
                    "erpnext.buying.doctype.purchase_order.purchase_order.update_status",
                    {"status": "Submitted", "name": po_name},
                )
            except Exception:
                pass
        if pr_name:
            try:
                if pr_approved:
                    apply_workflow(purchase_mgr, "Purchase Receipt", pr_name, "申请撤销")
                    apply_workflow(finance_rev, "Purchase Receipt", pr_name, "财务撤销")
                else:
                    admin.request("DELETE", ERPNextAPI.resource_path("Purchase Receipt", pr_name))
            except Exception:
                pass
        try:
            if po_approved:
                apply_workflow(purchase_mgr, "Purchase Order", po_name, "撤销")
            else:
                admin.request("DELETE", ERPNextAPI.resource_path("Purchase Order", po_name))
        except Exception:
            pass

    print(f"ALL 2A SOURCE LINKAGE CHECKS PASSED on {base}")


if __name__ == "__main__":
    main()
