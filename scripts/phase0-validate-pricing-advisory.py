#!/usr/bin/env python3
"""Validate 1A pricing advisory: priority order, source labels, history window & minimum-sale check."""

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


def price_quote(api: ERPNextAPI, body: dict):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if api.csrf_token:
        headers["X-Frappe-CSRF-Token"] = api.csrf_token
    req = urllib.request.Request(f"{api.base_url}{PREFIX}/price-quote", data=data, headers=headers, method="POST")
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
    warehouse = access["warehouses"][0]
    item_code = baseline["item"]["item_code"]
    customer = baseline["customer"]
    supplier = baseline["supplier"]
    selling_pl = baseline["selling_price_list"]
    buying_pl = baseline["buying_price_list"]

    admin = ERPNextAPI(base)
    admin.login(admin_user, admin_password)

    sales = ERPNextAPI(base)
    sales.login(access["users"]["sales"]["email"], role_password)

    sales_mgr = ERPNextAPI(base)
    sales_mgr.login(access["users"]["sales_manager"]["email"], role_password)

    purchase = ERPNextAPI(base)
    purchase.login(access["users"]["purchase"]["email"], role_password)

    item_doc = admin.get_doc("Item", item_code)
    assert item_doc is not None, f"Missing R1 item {item_code}"
    original_min_sale = item_doc.get("custom_trade_minimum_sale") or 0

    tag = uuid4().hex[:8]
    created_item_prices: list[str] = []
    created_rules: list[str] = []
    so_name = None
    so_approved = False

    try:
        admin.update("Item", item_code, {"custom_trade_minimum_sale": 85})

        # Create temporary customer-specific price (90) and quantity pricing rule (min_qty=10 -> 75)
        party_ip = admin.insert("Item Price", {
            "item_code": item_code,
            "price_list": selling_pl,
            "uom": "Piece",
            "customer": customer,
            "price_list_rate": 90,
            "valid_from": "2026-01-01",
        })
        party_ip_name = party_ip["name"]
        created_item_prices.append(party_ip_name)

        rule_doc = admin.insert("Pricing Rule", {
            "title": f"R1-1A-TMP-RULE-{tag}",
            "company": company,
            "currency": "CNY",
            "apply_on": "Item Code",
            "price_or_product_discount": "Price",
            "applicable_for": "Customer",
            "customer": customer,
            "selling": 1,
            "buying": 0,
            "items": [{"item_code": item_code}],
            "min_qty": 10,
            "priority": "10",
            "rate": 75,
            "rate_or_discount": "Rate",
            "for_price_list": selling_pl,
            "valid_from": "2026-01-01",
            "valid_upto": "2026-12-31",
        })
        created_rules.append(rule_doc["name"])

        # 1. Sales: party_price (90) vs pricing_rule (75 < min 85) vs expired rule (90) vs tier_price (100) vs Box (3750 -> 75/pc)
        status, r_party = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "partnerId": customer,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "9",
            "uom": "Piece",
            "priceList": selling_pl,
            "warehouseId": warehouse,
        })
        assert status == 200, (status, r_party)
        d = r_party["data"]
        assert d["selected"]["source"] == "party_price" and d["selected"]["rate"] == "90.00", d
        assert [c["source"] for c in d["candidates"][:2]] == ["party_price", "tier_price"], d
        assert d["minimumSale"]["belowMinimumSale"] is False, d

        status, r_rule = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "partnerId": customer,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "10",
            "uom": "Piece",
            "priceList": selling_pl,
            "warehouseId": warehouse,
        })
        assert status == 200, (status, r_rule)
        d_rule = r_rule["data"]
        assert d_rule["selected"]["source"] == "pricing_rule" and d_rule["selected"]["rate"] == "75.00", d_rule
        assert d_rule["minimumSale"]["belowMinimumSale"] is True and d_rule["minimumSale"]["warning"], d_rule

        status, r_expired = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "partnerId": customer,
            "productId": item_code,
            "postingDate": "2027-01-01",
            "quantity": "10",
            "uom": "Piece",
            "priceList": selling_pl,
            "warehouseId": warehouse,
        })
        assert status == 200 and r_expired["data"]["selected"]["source"] == "party_price", r_expired

        status, r_tier = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "1",
            "uom": "Piece",
            "priceList": selling_pl,
            "warehouseId": warehouse,
        })
        assert status == 200 and r_tier["data"]["selected"]["source"] == "tier_price" and r_tier["data"]["selected"]["rate"] == "100.00", r_tier

        status, r_box = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "partnerId": customer,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "1",
            "uom": "Box",
            "priceList": selling_pl,
            "warehouseId": warehouse,
        })
        assert status == 200, (status, r_box)
        assert r_box["data"]["selected"]["source"] == "pricing_rule" and r_box["data"]["selected"]["rate"] == "3750.00", r_box
        assert r_box["data"]["minimumSale"]["belowMinimumSale"] is True and r_box["data"]["minimumSale"]["stockUomRate"] == "75.00", r_box
        print("PASS 1: sales pricing_rule / party_price / tier_price / expiry / Box UOM / minimum-sale warning verified")

        # 2. Purchase direction check (tier_price=60, no sales minimum warning)
        status, r_buy = price_quote(purchase, {
            "kind": "purchase",
            "companyId": company,
            "partnerId": supplier,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "1",
            "uom": "Piece",
            "priceList": buying_pl,
            "warehouseId": warehouse,
        })
        assert status == 200 and r_buy["data"]["selected"]["source"] == "tier_price" and r_buy["data"]["selected"]["rate"] == "60.00", r_buy
        assert r_buy["data"]["minimumSale"]["belowMinimumSale"] is False
        print("PASS 2: purchase tier_price verified")

        # 3. Historical transaction price & configurable window + proposedRate warning + historical immutability
        so = sales.insert("Sales Order", {
            "company": company,
            "customer": customer,
            "transaction_date": "2026-11-20",
            "delivery_date": "2026-11-30",
            "currency": "CNY",
            "selling_price_list": selling_pl,
            "items": [{"item_code": item_code, "qty": 2, "uom": "Piece", "rate": 88, "warehouse": warehouse}],
        })
        so_name = so["name"]
        apply_workflow(sales_mgr, "Sales Order", so_name, "批准")
        so_approved = True

        status, r_hist = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "partnerId": customer,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "2",
            "uom": "Piece",
            "priceList": selling_pl,
            "priorityOrder": ["history_price", "party_price", "tier_price"],
            "historyWindowDays": 30,
        })
        assert status == 200, (status, r_hist)
        assert r_hist["data"]["selected"]["source"] == "history_price", r_hist
        assert r_hist["data"]["selected"]["rate"] == "88.00", r_hist
        assert r_hist["data"]["selected"]["referenceDoc"] == so_name, r_hist

        # Outside 2-day window -> falls back to party_price (90.00); manual proposedRate 80 triggers min-sale warning
        status, r_hist_out = price_quote(sales, {
            "kind": "sales",
            "companyId": company,
            "partnerId": customer,
            "productId": item_code,
            "postingDate": "2026-11-24",
            "quantity": "2",
            "uom": "Piece",
            "priceList": selling_pl,
            "priorityOrder": ["history_price", "party_price", "tier_price"],
            "historyWindowDays": 2,
            "proposedRate": "80.00",
        })
        assert status == 200, (status, r_hist_out)
        assert r_hist_out["data"]["selected"]["source"] == "party_price" and r_hist_out["data"]["selected"]["rate"] == "90.00", r_hist_out
        assert r_hist_out["data"]["minimumSale"]["belowMinimumSale"] is True, r_hist_out

        # Historical immutability: mutating Item Price does NOT change saved Sales Order rate (88)
        admin.update("Item Price", party_ip_name, {"price_list_rate": 95})
        saved_so_check = admin.get_doc("Sales Order", so_name)
        assert float(saved_so_check["items"][0]["rate"]) == 88.0, saved_so_check["items"][0]
        print("PASS 3: history_price window, proposedRate min-sale warning, and historical doc immutability verified")

    finally:
        for rule_name in created_rules:
            try:
                admin.request("DELETE", ERPNextAPI.resource_path("Pricing Rule", rule_name))
            except Exception:
                pass
        for ip_name in created_item_prices:
            try:
                admin.request("DELETE", ERPNextAPI.resource_path("Item Price", ip_name))
            except Exception:
                pass
        if so_name:
            try:
                if so_approved:
                    apply_workflow(sales_mgr, "Sales Order", so_name, "撤销")
                else:
                    admin.request("DELETE", ERPNextAPI.resource_path("Sales Order", so_name))
            except Exception:
                pass
        try:
            admin.update("Item", item_code, {"custom_trade_minimum_sale": original_min_sale})
        except Exception:
            pass

    print(f"ALL 1A PRICING ADVISORY CHECKS PASSED on {base}")


if __name__ == "__main__":
    main()
