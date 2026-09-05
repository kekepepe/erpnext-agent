#!/usr/bin/env python3
"""Idempotently seed the disposable Phase 0 site through ERPNext REST APIs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from phase0_api import ERPNextAPI


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "phase0" / "synthetic-data.json"


def ensure_named_doc(
    api: ERPNextAPI,
    doctype: str,
    name: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    current = api.get_doc(doctype, name)
    if current is not None:
        print(f"EXISTS  {doctype}: {name}")
        return current
    created = api.insert(doctype, payload)
    print(f"CREATED {doctype}: {created['name']}")
    return created


def load_dataset(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        dataset = json.load(file)
    item_codes = [item["item_code"] for item in dataset["items"]]
    if len(item_codes) != 20 or len(set(item_codes)) != 20:
        raise ValueError("Phase 0 dataset must contain exactly 20 unique item codes")
    if len(dataset["suppliers"]) != 3 or len(dataset["customers"]) != 3:
        raise ValueError("Phase 0 dataset must contain 3 suppliers and 3 customers")
    if len(dataset["warehouses"]) < 2:
        raise ValueError("Phase 0 dataset must contain at least 2 warehouses")
    return dataset


def seed(api: ERPNextAPI, dataset: dict[str, Any]) -> None:
    company = dataset["company"]
    company_name = company["company_name"]
    company_payload = {
        key: value
        for key, value in company.items()
        if key != "tax_assumption"
    }
    ensure_named_doc(api, "Company", company_name, company_payload)

    for uom in dataset["uoms"]:
        ensure_named_doc(api, "UOM", uom["uom_name"], uom)

    for item_group in dataset["item_groups"]:
        ensure_named_doc(
            api,
            "Item Group",
            item_group,
            {
                "item_group_name": item_group,
                "parent_item_group": "All Item Groups",
                "is_group": 0,
            },
        )

    warehouse_names: list[str] = []
    for warehouse in dataset["warehouses"]:
        full_name = f"{warehouse['warehouse_name']} - {company['abbr']}"
        ensure_named_doc(
            api,
            "Warehouse",
            full_name,
            {
                "warehouse_name": warehouse["warehouse_name"],
                "company": company_name,
                "is_group": 0,
            },
        )
        warehouse_names.append(full_name)

    for supplier in dataset["suppliers"]:
        ensure_named_doc(
            api,
            "Supplier",
            supplier["supplier_name"],
            {
                "supplier_name": supplier["supplier_name"],
                "supplier_type": "Company",
                "supplier_group": supplier["supplier_group"],
                "country": company["country"],
            },
        )

    for customer in dataset["customers"]:
        ensure_named_doc(
            api,
            "Customer",
            customer["customer_name"],
            {
                "customer_name": customer["customer_name"],
                "customer_type": "Company",
                "customer_group": customer["customer_group"],
                "territory": company["country"],
            },
        )

    for item in dataset["items"]:
        payload = {
            "item_code": item["item_code"],
            "item_name": item["item_name"],
            "item_group": item["item_group"],
            "stock_uom": "Piece",
            "is_stock_item": 1,
            "description": f"Synthetic Phase 0 item. Scenario: {item['scenario']}",
            "uoms": item.get(
                "uoms", [{"uom": "Piece", "conversion_factor": 1}]
            ),
        }
        ensure_named_doc(api, "Item", item["item_code"], payload)

        for price_list, rate in (
            ("Standard Buying", item["purchase_price"]),
            ("Standard Selling", item["selling_price"]),
        ):
            existing_prices = api.list_docs(
                "Item Price",
                ["name"],
                [
                    ["Item Price", "item_code", "=", item["item_code"]],
                    ["Item Price", "price_list", "=", price_list],
                    ["Item Price", "uom", "=", "Piece"],
                ],
            )
            if existing_prices:
                print(f"EXISTS  Item Price: {item['item_code']} / {price_list}")
            else:
                created = api.insert(
                    "Item Price",
                    {
                        "item_code": item["item_code"],
                        "uom": "Piece",
                        "price_list": price_list,
                        "price_list_rate": rate,
                    },
                )
                print(f"CREATED Item Price: {created['name']}")

    stock_items = [
        {
            "item_code": item["item_code"],
            "warehouse": warehouse_names[0],
            "qty": item["opening_stock"],
            "valuation_rate": item["purchase_price"],
        }
        for item in dataset["items"]
        if item["opening_stock"] > 0
    ]
    expected_stock = {
        (row["item_code"], row["warehouse"], float(row["qty"]))
        for row in stock_items
    }
    reconciliation_candidates = api.list_docs(
        "Stock Reconciliation",
        ["name", "docstatus"],
        [
            ["Stock Reconciliation", "company", "=", company_name],
            ["Stock Reconciliation", "purpose", "=", "Opening Stock"],
            ["Stock Reconciliation", "docstatus", "=", 1],
        ],
    )
    existing_reconciliations = []
    for candidate in reconciliation_candidates:
        document = api.get_doc("Stock Reconciliation", candidate["name"])
        if document is None:
            continue
        actual_stock = {
            (row["item_code"], row["warehouse"], float(row["qty"]))
            for row in document.get("items", [])
        }
        if actual_stock == expected_stock:
            existing_reconciliations.append(document)
    if existing_reconciliations:
        print(
            "EXISTS  Submitted opening stock: "
            f"{existing_reconciliations[0]['name']}"
        )
    else:
        opening_account_name = f"Temporary Opening - {company['abbr']}"
        opening_account = api.get_doc("Account", opening_account_name)
        if opening_account is None or opening_account.get("root_type") not in {
            "Asset",
            "Liability",
        }:
            raise RuntimeError(
                "A valid Asset/Liability Temporary Opening account is required: "
                f"{opening_account_name}"
            )
        draft = api.insert(
            "Stock Reconciliation",
            {
                "company": company_name,
                "purpose": "Opening Stock",
                "expense_account": opening_account_name,
                "items": stock_items,
            },
        )
        submitted = api.submit(draft)
        print(f"CREATED Submitted opening stock: {submitted['name']}")

    print(
        "SUMMARY "
        f"company=1 warehouses={len(dataset['warehouses'])} "
        f"suppliers={len(dataset['suppliers'])} customers={len(dataset['customers'])} "
        f"items={len(dataset['items'])}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"),
    )
    parser.add_argument(
        "--username", default=os.environ.get("PHASE0_USERNAME", "Administrator")
    )
    parser.add_argument(
        "--password", default=os.environ.get("PHASE0_PASSWORD", "admin")
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dataset = load_dataset(args.dataset)
        api = ERPNextAPI(args.base_url)
        api.login(args.username, args.password)
        seed(api, dataset)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
