#!/usr/bin/env python3
"""Reproduce native price conflicts with isolated, synthetic master data."""

import argparse
import os

from phase0_api import ERPNextAPI, validate_disposable_url

COMPANY = "R1合成发布验证公司"
WAREHOUSE = "R1测试主仓 - R1D"
ITEM = "R1-W4-PRICE-CHECK"
CUSTOMER = "R1-W4-PRICE-CUSTOMER"
SUPPLIER = "R1-W4-PRICE-SUPPLIER"


def check(api, apply):
    def ensure(doctype, name, fields, filters=None):
        if filters is None:
            existing = api.get_doc(doctype, name)
        else:
            matches = api.list_docs(doctype, ["name"], filters, 2)
            if len(matches) > 1:
                raise ValueError(f"Duplicate fixture: {doctype} {name}")
            existing = api.get_doc(doctype, matches[0]["name"]) if matches else None
        if not existing:
            if not apply:
                raise ValueError(f"Missing fixture: {doctype} {name}")
            existing = api.insert(doctype, fields)
        for key, value in fields.items():
            actual = existing.get(key)
            if isinstance(value, list):
                matches = len(actual or ()) == len(value) and all(
                    all(row.get(k) == v for k, v in expected.items())
                    for row, expected in zip(actual, value)
                )
            else:
                matches = actual == value
            if not matches:
                raise ValueError(f"Fixture differs: {doctype} {name} {key}")
        return existing["name"]

    team = api.get_doc("Company", COMPANY)
    if not team or team["abbr"] != "R1D":
        raise ValueError("Isolated R1 fixture company is required.")

    ensure("Item", ITEM, {
        "item_code": ITEM, "item_name": "R1-W4 合成价格测试商品", "item_group": "R1合成五金",
        "stock_uom": "Piece", "is_sales_item": 1, "is_purchase_item": 1,
        "uoms": [{"uom": "Piece", "conversion_factor": 1}, {"uom": "Box", "conversion_factor": 50}],
    })

    for buying in (False, True):
        party_type = "Supplier" if buying else "Customer"
        party_field = party_type.lower()
        party = SUPPLIER if buying else CUSTOMER
        price_list = "R1-W4-采购档位" if buying else "R1-W4-销售档位"
        ensure("Price List", price_list, {
            "price_list_name": price_list, "currency": "CNY", "buying": int(buying),
            "selling": int(not buying), "enabled": 1, "price_not_uom_dependent": 1,
        })
        party_values = {
            party_field + "_name": party, party_field + "_type": "Company", "default_currency": "CNY",
            "default_price_list": price_list,
            party_field + "_group": "All Supplier Groups" if buying else "R1合成客户组",
        }
        if not buying:
            party_values["territory"] = "China"
        party = ensure(party_type, party, party_values)
        for uom, party_price, rate in [("Piece", False, 100), ("Piece", True, 90), ("Box", False, 4900)]:
            fields = {"item_code": ITEM, "price_list": price_list, "uom": uom, "price_list_rate": rate}
            filters = [[key, "=", val] for key, val in fields.items() if key != "price_list_rate"]
            if party_price:
                fields[party_field] = party
                filters.append([party_field, "=", party])
            else:
                filters.append([party_field, "is", "not set"])
            ensure("Item Price", f"{uom} {party_price}", fields, filters)

        rules = []
        for suffix, priority, rate in [("低优先", "1", 80), ("高优先", "10", 75)]:
            title = f"R1-W4-{party_type}-{suffix}"
            rules.append(ensure("Pricing Rule", title, {
                "title": title, "company": COMPANY, "currency": "CNY", "apply_on": "Item Code",
                "price_or_product_discount": "Price", "applicable_for": party_type, party_field: party,
                "buying": int(buying), "selling": int(not buying), "items": [{"item_code": ITEM}],
                "min_qty": 10, "priority": priority, "rate": rate, "rate_or_discount": "Rate",
                "for_price_list": price_list, "valid_from": "2026-01-01", "valid_upto": "2026-12-31",
            }, [["title", "=", title]]))

        for qty, uom, day, selected, expected_price, expected_rule_rate in [
            (9, "Piece", "2026-11-22", party, 90, None),
            (10, "Piece", "2026-11-22", party, 90, 75),
            (10, "Piece", "2027-01-01", party, 90, None),
            (1, "Piece", "2026-11-22", None, 100, None),
            (1, "Box", "2026-11-22", None, 4900, None),
            (1, "Box", "2026-11-22", party, 4900, 3750),
        ]:
            context = {
                "doctype": "Purchase Order" if buying else "Sales Order",
                "company": COMPANY, "item_code": ITEM, party_field: selected,
                "transaction_date": day, "price_list": price_list, "currency": "CNY",
                "price_list_currency": "CNY", "conversion_rate": 1, "plc_conversion_rate": 1,
                "qty": qty, "uom": uom, "warehouse": WAREHOUSE, "ignore_party": True,
            }
            result = api.call("erpnext.stock.get_item_details.get_item_details", {"ctx": context})
            native_rules = result.get("pricing_rules") or ""
            if expected_rule_rate is None:
                assert not native_rules, (context, native_rules)
            else:
                assert rules[-1] in native_rules and rules[0] not in native_rules, (context, native_rules)
            shown = result.get("price_list_rate")
            expected = expected_price if expected_rule_rate is None else expected_rule_rate
            assert shown == expected, (context, shown, expected)
            print(f"PASS {party_type} {qty} {uom} {day}: price {shown}, rule {native_rules or 'none'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-fixtures", action="store_true")
    args = parser.parse_args()
    url = validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://127.0.0.1:18081"))
    if args.apply_fixtures and url.endswith(":8080"):
        raise ValueError("Use an isolated validation site for writing pricing fixtures.")
    api = ERPNextAPI(url)
    api.login(os.environ.get("PHASE0_USERNAME", "Administrator"), os.environ.get("PHASE0_PASSWORD", "admin"))
    check(api, args.apply_fixtures)


if __name__ == "__main__":
    main()
