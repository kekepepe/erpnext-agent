#!/usr/bin/env python3
"""Validate the W6 Business API v1 ERPNext adapter against a disposable site.

Exercises:
1. Unauthenticated (401) and missing CSRF (403) rejection.
2. Native role permission rejection (sales maker denied on receipt/delivery;
   stock manager gets saveDraft=False and 403 on write).
3. Warehouse User Permission out-of-scope rejection (403 without leaking existence).
4. Authorized stock maker creates Purchase Receipt & Delivery Note drafts (201),
   reads them back (200), verifies native docstatus=0, workflow_state=Pending,
   and ZERO Stock Ledger Entry / GL Entry created.
5. Concurrent replay with same Idempotency-Key creates only one native draft;
   same key with altered payload returns 409 IDEMPOTENCY_CONFLICT.
6. Draft update increments revision (1 -> 2), replays cleanly with same key,
   and rejects stale revision (409 STALE_REVISION) while preserving revision 2.
7. Cross-user GET returns 404 (no existence leak).
8. Cleans up synthetic test drafts and temporary warehouse restriction.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from phase0_api import ERPNextAPI, validate_disposable_url


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/business/v1"


def raw_request(api: ERPNextAPI, method: str, path: str, body=None, key: str | None = None, include_csrf: bool = True):
    data = None
    headers = {"Accept": "application/json"}
    if include_csrf and api.csrf_token:
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


def main():
    base = validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"))
    role_password = os.environ.get("PHASE0_ROLE_PASSWORD", "p0-local-only")
    admin_user = os.environ.get("PHASE0_USERNAME", "Administrator")
    admin_password = os.environ.get("PHASE0_PASSWORD", "admin")

    access = json.loads((ROOT / "phase0/release-access.json").read_text())
    baseline = json.loads((ROOT / "phase0/release-baseline.json").read_text())

    company = access["company"]
    main_wh, aux_wh = access["warehouses"][0], access["warehouses"][1]
    supplier = baseline["supplier"]
    customer = baseline["customer"]
    item_code = baseline["item"]["item_code"]

    # 1. Guest rejected with 401
    guest = ERPNextAPI(base)
    status, body = raw_request(guest, "GET", "/entry-options?kind=purchase_receipt", include_csrf=False)
    assert status == 401, f"Expected 401 for guest, got {status}: {body}"
    print("PASS 1: guest rejected with 401")

    # Log in real R1 roles + admin for verification/cleanup
    admin = ERPNextAPI(base)
    admin.login(admin_user, admin_password)

    stock = ERPNextAPI(base)
    stock.login(access["users"]["stock"]["email"], role_password)

    stock_mgr = ERPNextAPI(base)
    stock_mgr.login(access["users"]["stock_manager"]["email"], role_password)

    sales = ERPNextAPI(base)
    sales.login(access["users"]["sales"]["email"], role_password)

    # 2. Missing CSRF rejected on write
    pr_payload = {
        "kind": "purchase_receipt",
        "companyId": company,
        "partnerId": supplier,
        "postingDate": "2026-11-24",
        "lines": [{"productId": item_code, "warehouseId": main_wh, "quantity": "3"}],
    }
    status, body = raw_request(stock, "POST", "/drafts", pr_payload, key=f"nocsrf-{uuid4().hex}", include_csrf=False)
    assert status in (400, 403), f"Expected 400/403 without CSRF, got {status}: {body}"
    print(f"PASS 2: missing CSRF rejected ({status})")

    # 3. Role permissions: sales denied (403); stock_manager read-only (saveDraft=False, write 403)
    for kind in ("purchase_receipt", "sales_delivery"):
        status, body = raw_request(sales, "GET", f"/entry-options?kind={kind}")
        assert status == 403, f"Expected 403 for sales on {kind}, got {status}: {body}"
        status, body = raw_request(stock_mgr, "GET", f"/entry-options?kind={kind}")
        assert status == 200, f"Expected 200 for stock_manager on {kind}, got {status}: {body}"
        assert body["data"]["capabilities"]["saveDraft"] is False, f"stock_manager must not have saveDraft on {kind}"

    status, body = raw_request(stock_mgr, "POST", "/drafts", pr_payload, key=f"mgr-{uuid4().hex}")
    assert status == 403, f"Expected 403 for stock_manager POST, got {status}: {body}"
    print("PASS 3: native role permissions enforced (sales 403, stock_manager read-only)")

    created_docs: list[tuple[str, str]] = []
    temp_wh_perm_deleted = False
    removed_perm_payload = None
    try:
        # 4. Authorized stock maker options & draft creation (PR + DN) + zero SLE/GL
        for kind, doctype, partner in (
            ("purchase_receipt", "Purchase Receipt", supplier),
            ("sales_delivery", "Delivery Note", customer),
        ):
            status, opts = raw_request(stock, "GET", f"/entry-options?kind={kind}")
            assert status == 200 and opts["data"]["capabilities"]["saveDraft"] is True, opts
            assert any(c["id"] == company for c in opts["data"]["companies"]), opts
            assert any(p["id"] == partner for p in opts["data"]["partners"]), opts
            assert any(w["id"] == main_wh for w in opts["data"]["warehouses"]), opts
            assert any(i["id"] == item_code for i in opts["data"]["products"]), opts

            # Verify native ERPNext UOM whole-number validation surfaces as 422
            fractional = {
                "kind": kind,
                "companyId": company,
                "partnerId": partner,
                "postingDate": "2026-11-24",
                "lines": [{"productId": item_code, "warehouseId": main_wh, "quantity": "2.5"}],
            }
            status, frac_err = raw_request(stock, "POST", "/drafts", fractional, key=f"frac-{uuid4().hex}")
            assert status == 422 and frac_err["error"]["code"] == "VALIDATION_ERROR", (status, frac_err)

            payload = {
                "kind": kind,
                "companyId": company,
                "partnerId": partner,
                "postingDate": "2026-11-24",
                "lines": [{"productId": item_code, "warehouseId": main_wh, "quantity": "3"}],
            }
            create_key = f"w6-create-{kind}-{uuid4().hex}"

            # 5. Concurrent replay test
            def _post():
                return raw_request(stock, "POST", "/drafts", payload, key=create_key)

            with ThreadPoolExecutor(2) as pool:
                r1_fut = pool.submit(_post)
                r2_fut = pool.submit(_post)
                r1 = r1_fut.result()
                r2 = r2_fut.result()

            assert r1[0] == 201, f"Expected 201 on {kind} create, got {r1}"
            assert r1 == r2, f"Concurrent replay mismatch: {r1} != {r2}"
            draft = r1[1]["data"]
            doc_id = draft["id"]
            created_docs.append((doctype, doc_id))
            assert draft["revision"] == 1 and draft["status"] == "draft", draft
            assert draft["lines"][0]["quantity"] == "3", draft

            # Read back via Business API
            status, read_back = raw_request(stock, "GET", f"/drafts/{doc_id}")
            assert status == 200 and read_back == r1[1], (status, read_back)

            # Verify native document state & zero SLE/GL
            native_doc = admin.get_doc(doctype, doc_id)
            assert native_doc is not None and int(native_doc["docstatus"]) == 0, native_doc
            assert native_doc.get("workflow_state") == "Pending", native_doc
            sle = admin.list_docs("Stock Ledger Entry", ["name"], [["voucher_no", "=", doc_id]], limit=5)
            gle = admin.list_docs("GL Entry", ["name"], [["voucher_no", "=", doc_id]], limit=5)
            assert sle == [] and gle == [], f"Draft must not post SLE/GL: sle={sle}, gle={gle}"

            # Conflicting payload with same Idempotency-Key -> 409
            changed = {**payload, "postingDate": "2026-11-23"}
            status, conflict = raw_request(stock, "POST", "/drafts", changed, key=create_key)
            assert status == 409 and conflict["error"]["code"] == "IDEMPOTENCY_CONFLICT", (status, conflict)

            # 6. Update draft: revision 1 -> 2, replay, stale revision
            update_key = f"w6-update-{kind}-{uuid4().hex}"
            update_payload = {**payload, "postingDate": "2026-11-23", "revision": 1}
            status, updated = raw_request(stock, "PUT", f"/drafts/{doc_id}", update_payload, key=update_key)
            assert status == 200 and updated["data"]["revision"] == 2, (status, updated)
            assert updated["data"]["postingDate"] == "2026-11-23", updated

            # Replay same update key -> returns revision 2 (no stale error)
            status, replayed = raw_request(stock, "PUT", f"/drafts/{doc_id}", update_payload, key=update_key)
            assert status == 200 and replayed == updated, (status, replayed)

            # Stale revision with new key -> 409 STALE_REVISION
            status, stale = raw_request(stock, "PUT", f"/drafts/{doc_id}", update_payload, key=f"stale-{uuid4().hex}")
            assert status == 409 and stale["error"]["code"] == "STALE_REVISION", (status, stale)

            # Verify revision 2 preserved
            status, after_stale = raw_request(stock, "GET", f"/drafts/{doc_id}")
            assert status == 200 and after_stale == updated, (status, after_stale)

            # 7. Cross-user isolation: sales GET -> 404 (no existence leak)
            status, not_found = raw_request(sales, "GET", f"/drafts/{doc_id}")
            assert status == 404, f"Expected 404 for unauthorized GET, got {status}: {not_found}"

        print("PASS 4-7: PR & DN create/read/update, concurrent replay, conflict, stale revision, zero SLE/GL, 404 isolation")

        # 8. Warehouse out-of-scope rejection: temporarily revoke aux_wh User Permission for r1.stock
        aux_perms = admin.list_docs(
            "User Permission",
            ["name", "user", "allow", "for_value", "apply_to_all_doctypes"],
            [
                ["user", "=", access["users"]["stock"]["email"]],
                ["allow", "=", "Warehouse"],
                ["for_value", "=", aux_wh],
            ],
            limit=5,
        )
        if aux_perms:
            removed_perm_payload = aux_perms[0]
            admin.request("DELETE", ERPNextAPI.resource_path("User Permission", removed_perm_payload["name"]))
            temp_wh_perm_deleted = True

            # Confirm entry-options no longer lists aux_wh
            status, scoped_opts = raw_request(stock, "GET", "/entry-options?kind=purchase_receipt")
            assert status == 200, scoped_opts
            assert not any(w["id"] == aux_wh for w in scoped_opts["data"]["warehouses"]), scoped_opts

            # Confirm POST targeting aux_wh is rejected with 403
            forbidden_wh_payload = {
                **pr_payload,
                "lines": [{"productId": item_code, "warehouseId": aux_wh, "quantity": "1"}],
            }
            status, wh_err = raw_request(stock, "POST", "/drafts", forbidden_wh_payload, key=f"wh403-{uuid4().hex}")
            assert status == 403, f"Expected 403 for out-of-scope warehouse, got {status}: {wh_err}"
            print("PASS 8: out-of-scope warehouse rejected with 403 and hidden from options")

        # 9. Verify hosted W6 page responds 200 with CSRF meta for logged-in user
        page_html = stock.get_text("/w6-entry")
        assert 'meta name="csrf-token"' in page_html and "/assets/erpnext_zh/w6/app.js" in page_html
        print("PASS 9: /w6-entry hosted page renders with CSRF token")

    finally:
        # Restore aux_wh User Permission if temporarily removed
        if temp_wh_perm_deleted and removed_perm_payload:
            admin.insert(
                "User Permission",
                {
                    "user": removed_perm_payload["user"],
                    "allow": removed_perm_payload["allow"],
                    "for_value": removed_perm_payload["for_value"],
                    "apply_to_all_doctypes": removed_perm_payload.get("apply_to_all_doctypes", 1),
                },
            )
        # Clean up synthetic draft docs
        for doctype, doc_id in created_docs:
            try:
                admin.request("DELETE", ERPNextAPI.resource_path(doctype, doc_id))
            except Exception:
                pass

    print(f"ALL W6 ADAPTER CHECKS PASSED on {base}")


if __name__ == "__main__":
    main()
