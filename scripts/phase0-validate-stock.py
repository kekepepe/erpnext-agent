#!/usr/bin/env python3
"""Execute and verify the remaining synthetic Phase 0 stock cases."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable

from phase0_api import ERPNextAPI


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIOS = ROOT / "phase0" / "stock-validation.json"
DEFAULT_DATASET = ROOT / "phase0" / "synthetic-data.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def find_doc(
    api: ERPNextAPI,
    doctype: str,
    filters: list[list[Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any] | None:
    for candidate in api.list_docs(doctype, ["name", "docstatus"], filters, 500):
        document = api.get_doc(doctype, candidate["name"])
        if document and document.get("docstatus") != 2 and predicate(document):
            return document
    return None


def ensure_submitted(api: ERPNextAPI, document: dict[str, Any]) -> dict[str, Any]:
    if document.get("docstatus") == 1:
        return document
    return api.submit(document)


def stock_balance(api: ERPNextAPI, item_code: str, warehouse: str) -> float:
    rows = api.list_docs(
        "Bin",
        ["name", "actual_qty"],
        [
            ["Bin", "item_code", "=", item_code],
            ["Bin", "warehouse", "=", warehouse],
        ],
    )
    return float(rows[0]["actual_qty"]) if rows else 0.0


def validate_opening_stock(
    api: ERPNextAPI,
    config: dict[str, Any],
    dataset: dict[str, Any],
) -> dict[str, Any]:
    document_name = config["opening_stock_document"]
    document = api.get_doc("Stock Reconciliation", document_name)
    if not document or document.get("docstatus") != 1:
        raise RuntimeError(f"Opening stock document is not submitted: {document_name}")
    expected = {
        item["item_code"]: (
            float(item["opening_stock"]),
            float(item["purchase_price"]),
        )
        for item in dataset["items"]
        if item["opening_stock"] > 0
    }
    actual = {
        row["item_code"]: (float(row["qty"]), float(row["valuation_rate"]))
        for row in document.get("items", [])
    }
    if actual != expected:
        raise RuntimeError("Opening Stock document rows differ from the dataset")
    ledger_rows = api.list_docs(
        "Stock Ledger Entry",
        [
            "name",
            "item_code",
            "warehouse",
            "actual_qty",
            "valuation_rate",
            "qty_after_transaction",
        ],
        [
            ["Stock Ledger Entry", "voucher_no", "=", document_name],
            ["Stock Ledger Entry", "is_cancelled", "=", 0],
        ],
        500,
    )
    if any(row["warehouse"] != config["main_warehouse"] for row in ledger_rows):
        raise RuntimeError("Opening Stock ledger contains an unexpected warehouse")
    # Stock Reconciliation stores the resulting balance in qty_after_transaction.
    # Its opening-stock ledger rows can report actual_qty as zero, so using that
    # field would reject a correct opening balance on ERPNext v16.
    ledger = {
        row["item_code"]: (
            float(row["qty_after_transaction"]),
            float(row["valuation_rate"]),
        )
        for row in ledger_rows
    }
    if ledger != expected:
        raise RuntimeError("Opening Stock ledger rows differ from the dataset")
    return {"document": document_name, "rows": len(actual), "ledger_rows": len(ledger)}


def ensure_delivery_note(
    api: ERPNextAPI,
    config: dict[str, Any],
    scenario: dict[str, Any],
    submit: bool,
) -> dict[str, Any]:
    filters = [
        ["Delivery Note", "company", "=", config["company"]],
        ["Delivery Note", "customer", "=", scenario["customer"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            rows[0].get("item_code") == scenario["item_code"]
            and float(rows[0].get("qty", 0)) == float(
                scenario.get("qty", scenario.get("attempted_qty"))
            )
            and rows[0].get("warehouse") == config["main_warehouse"]
        )

    document = find_doc(api, "Delivery Note", filters, matches)
    if document is None:
        qty = scenario.get("qty", scenario.get("attempted_qty"))
        document = api.insert(
            "Delivery Note",
            {
                "customer": scenario["customer"],
                "company": config["company"],
                "posting_date": date.today().isoformat(),
                "selling_price_list": "Standard Selling",
                "set_warehouse": config["main_warehouse"],
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "qty": qty,
                        "uom": scenario["uom"],
                        "conversion_factor": 1,
                        "rate": scenario["rate"],
                        "warehouse": config["main_warehouse"],
                    }
                ],
            },
        )
        print(f"CREATED Delivery Note draft: {document['name']}")
    else:
        print(f"EXISTS  Delivery Note: {document['name']}")
    if not submit:
        return document
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Delivery Note was not submitted: {submitted['name']}")
    return submitted


def ensure_transfer(api: ERPNextAPI, config: dict[str, Any]) -> dict[str, Any]:
    scenario = config["transfer"]
    filters = [
        ["Stock Entry", "company", "=", config["company"]],
        ["Stock Entry", "stock_entry_type", "=", "Material Transfer"],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            rows[0].get("item_code") == scenario["item_code"]
            and float(rows[0].get("qty", 0)) == float(scenario["qty"])
            and rows[0].get("s_warehouse") == config["main_warehouse"]
            and rows[0].get("t_warehouse") == config["secondary_warehouse"]
        )

    document = find_doc(api, "Stock Entry", filters, matches)
    if document is None:
        document = api.insert(
            "Stock Entry",
            {
                "company": config["company"],
                "stock_entry_type": "Material Transfer",
                "purpose": "Material Transfer",
                "posting_date": date.today().isoformat(),
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "qty": scenario["qty"],
                        "s_warehouse": config["main_warehouse"],
                        "t_warehouse": config["secondary_warehouse"],
                    }
                ],
            },
        )
        print(f"CREATED Stock Entry transfer: {document['name']}")
    else:
        print(f"EXISTS  Stock Entry transfer: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Stock Entry was not submitted: {submitted['name']}")
    return submitted


def ensure_reconciliation(api: ERPNextAPI, config: dict[str, Any]) -> dict[str, Any]:
    scenario = config["reconciliation"]
    filters = [
        ["Stock Reconciliation", "company", "=", config["company"]],
        ["Stock Reconciliation", "purpose", "=", "Stock Reconciliation"],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            rows[0].get("item_code") == scenario["item_code"]
            and rows[0].get("warehouse") == config["main_warehouse"]
            and float(rows[0].get("qty", 0)) == float(scenario["target_qty"])
            and float(rows[0].get("valuation_rate", 0))
            == float(scenario["valuation_rate"])
        )

    document = find_doc(api, "Stock Reconciliation", filters, matches)
    if document is None:
        document = api.insert(
            "Stock Reconciliation",
            {
                "company": config["company"],
                "purpose": "Stock Reconciliation",
                "posting_date": date.today().isoformat(),
                "expense_account": config["stock_adjustment_account"],
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "warehouse": config["main_warehouse"],
                        "qty": scenario["target_qty"],
                        "valuation_rate": scenario["valuation_rate"],
                    }
                ],
            },
        )
        print(f"CREATED Stock Reconciliation: {document['name']}")
    else:
        print(f"EXISTS  Stock Reconciliation: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(
            f"Stock Reconciliation was not submitted: {submitted['name']}"
        )
    row = submitted.get("items", [None])[0]
    if not row or float(row.get("valuation_rate", 0)) != float(
        scenario["valuation_rate"]
    ):
        raise RuntimeError("Stock Reconciliation valuation rate is incorrect")
    return submitted


def validate_insufficient_stock(api: ERPNextAPI, config: dict[str, Any]) -> str:
    scenario = config["zero_stock"]
    if stock_balance(api, scenario["item_code"], config["main_warehouse"]) != 0:
        raise RuntimeError("The zero-stock item unexpectedly has available quantity")
    draft = ensure_delivery_note(api, config, scenario, submit=False)
    if draft.get("docstatus") == 1:
        raise RuntimeError("ERPNext allowed the zero-stock Delivery Note to submit")
    try:
        api.submit(draft)
    except RuntimeError as error:
        message = str(error)
        expected_markers = ("NegativeStockError", "negative stock", "Insufficient stock")
        if not any(marker.lower() in message.lower() for marker in expected_markers):
            raise
        print(f"EXPECTED REJECTION Delivery Note: {draft['name']}")
        return draft["name"]
    raise RuntimeError("ERPNext did not reject the zero-stock Delivery Note")


def warehouse_balances(api: ERPNextAPI, warehouse: str) -> dict[str, float]:
    rows = api.list_docs(
        "Bin",
        ["name", "item_code", "actual_qty"],
        [["Bin", "warehouse", "=", warehouse]],
        500,
    )
    return {
        row["item_code"]: float(row["actual_qty"])
        for row in rows
        if float(row["actual_qty"]) != 0
    }


def validate(api: ERPNextAPI, config: dict[str, Any], dataset: dict[str, Any]) -> None:
    opening_evidence = validate_opening_stock(api, config, dataset)
    tracked = config["expected_final_stock"]
    baseline = {
        item_code: {
            warehouse: stock_balance(api, item_code, warehouse)
            for warehouse in warehouses
        }
        for item_code, warehouses in tracked.items()
    }

    delivery = ensure_delivery_note(api, config, config["delivery"], submit=True)
    transfer = ensure_transfer(api, config)
    reconciliation = ensure_reconciliation(api, config)
    rejected_delivery = validate_insufficient_stock(api, config)

    final_stock = {
        item_code: {
            warehouse: stock_balance(api, item_code, warehouse)
            for warehouse in warehouses
        }
        for item_code, warehouses in tracked.items()
    }
    expected_stock = {
        item_code: {warehouse: float(qty) for warehouse, qty in warehouses.items()}
        for item_code, warehouses in tracked.items()
    }
    if final_stock != expected_stock:
        raise RuntimeError(
            f"Final stock does not match expected values: {final_stock}"
        )

    main_balances = warehouse_balances(api, config["main_warehouse"])
    secondary_balances = warehouse_balances(api, config["secondary_warehouse"])
    if secondary_balances.get(config["transfer"]["item_code"]) != float(
        config["transfer"]["qty"]
    ):
        raise RuntimeError("Warehouse-level transfer balance is incorrect")

    evidence = {
        "opening_stock": opening_evidence,
        "baseline_stock": baseline,
        "delivery_note": delivery["name"],
        "stock_transfer": transfer["name"],
        "stock_reconciliation": reconciliation["name"],
        "zero_stock_item": config["zero_stock"]["item_code"],
        "rejected_delivery_note": rejected_delivery,
        "final_stock": final_stock,
        "main_warehouse_nonzero_items": len(main_balances),
        "secondary_warehouse_balances": secondary_balances,
    }
    print("EVIDENCE " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    print("OK: Phase 0 remaining stock validation passed")


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
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_json(args.scenarios)
        dataset = load_json(args.dataset)
        api = ERPNextAPI(args.base_url)
        api.login(args.username, args.password)
        validate(api, config, dataset)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
