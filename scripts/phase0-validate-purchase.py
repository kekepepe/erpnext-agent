#!/usr/bin/env python3
"""Execute and verify the synthetic Phase 0 purchase-flow scenarios."""

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
DEFAULT_SCENARIOS = ROOT / "phase0" / "purchase-validation.json"


def load_scenarios(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        config = json.load(file)
    required = {"full", "partial", "alternate_uom"}
    if set(config.get("scenarios", {})) != required:
        raise ValueError(f"Purchase scenarios must be exactly: {sorted(required)}")
    return config


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


def item_signature(document: dict[str, Any]) -> set[tuple[str, float, str]]:
    return {
        (row["item_code"], float(row["qty"]), row["uom"])
        for row in document.get("items", [])
    }


def ensure_submitted(api: ERPNextAPI, document: dict[str, Any]) -> dict[str, Any]:
    if document.get("docstatus") == 1:
        return document
    return api.submit(document)


def ensure_purchase_order(
    api: ERPNextAPI,
    company: str,
    warehouse: str,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    expected = {(scenario["item_code"], float(scenario["qty"]), scenario["uom"])}
    filters = [
        ["Purchase Order", "company", "=", company],
        ["Purchase Order", "supplier", "=", scenario["supplier"]],
    ]
    document = find_doc(
        api, "Purchase Order", filters, lambda doc: item_signature(doc) == expected
    )
    if document is None:
        today = date.today().isoformat()
        document = api.insert(
            "Purchase Order",
            {
                "supplier": scenario["supplier"],
                "company": company,
                "transaction_date": today,
                "schedule_date": today,
                "buying_price_list": "Standard Buying",
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "qty": scenario["qty"],
                        "uom": scenario["uom"],
                        "conversion_factor": scenario["conversion_factor"],
                        "rate": scenario["rate"],
                        "warehouse": warehouse,
                        "schedule_date": today,
                    }
                ],
            },
        )
        print(f"CREATED Purchase Order: {document['name']}")
    else:
        print(f"EXISTS  Purchase Order: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted["docstatus"] != 1:
        raise RuntimeError(f"Purchase Order was not submitted: {submitted['name']}")
    return submitted


def ensure_purchase_receipt(
    api: ERPNextAPI,
    company: str,
    purchase_order: dict[str, Any],
    qty: float,
    is_return: bool = False,
    return_against: str | None = None,
) -> dict[str, Any]:
    item_code = purchase_order["items"][0]["item_code"]
    expected_qty = -abs(float(qty)) if is_return else float(qty)
    filters = [
        ["Purchase Receipt", "company", "=", company],
        ["Purchase Receipt", "supplier", "=", purchase_order["supplier"]],
        ["Purchase Receipt", "is_return", "=", int(is_return)],
    ]

    def matches(document: dict[str, Any]) -> bool:
        if is_return and document.get("return_against") != return_against:
            return False
        rows = document.get("items", [])
        return len(rows) == 1 and (
            rows[0].get("item_code") == item_code
            and float(rows[0].get("qty", 0)) == expected_qty
            and (
                is_return
                or rows[0].get("purchase_order") == purchase_order["name"]
            )
        )

    document = find_doc(api, "Purchase Receipt", filters, matches)
    if document is None:
        if is_return:
            mapped = api.call(
                "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_return",
                {"source_name": return_against},
            )
        else:
            mapped = api.call(
                "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
                {"source_name": purchase_order["name"]},
            )
        if not mapped or len(mapped.get("items", [])) != 1:
            raise RuntimeError("ERPNext did not map exactly one Purchase Receipt item")
        mapped.pop("name", None)
        mapped["posting_date"] = date.today().isoformat()
        row = mapped["items"][0]
        row["qty"] = expected_qty
        row["received_qty"] = expected_qty
        row["stock_qty"] = expected_qty * float(row["conversion_factor"])
        document = api.insert("Purchase Receipt", mapped)
        action = "Purchase Return" if is_return else "Purchase Receipt"
        print(f"CREATED {action}: {document['name']}")
    else:
        action = "Purchase Return" if is_return else "Purchase Receipt"
        print(f"EXISTS  {action}: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted["docstatus"] != 1:
        raise RuntimeError(f"Purchase Receipt was not submitted: {submitted['name']}")
    return submitted


def ensure_purchase_invoice(
    api: ERPNextAPI,
    company: str,
    source_doctype: str,
    source_name: str,
    supplier: str,
    bill_no: str,
) -> dict[str, Any]:
    filters = [
        ["Purchase Invoice", "company", "=", company],
        ["Purchase Invoice", "supplier", "=", supplier],
    ]
    document = find_doc(
        api,
        "Purchase Invoice",
        filters,
        lambda doc: doc.get("bill_no") == bill_no,
    )
    if document is None:
        if source_doctype == "Purchase Receipt":
            method = "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice"
        else:
            method = "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice"
        mapped = api.call(method, {"source_name": source_name})
        if not mapped or not mapped.get("items"):
            raise RuntimeError("ERPNext did not map Purchase Invoice items")
        mapped.pop("name", None)
        mapped["bill_no"] = bill_no
        mapped["bill_date"] = date.today().isoformat()
        mapped["posting_date"] = date.today().isoformat()
        document = api.insert("Purchase Invoice", mapped)
        print(f"CREATED Purchase Invoice: {document['name']}")
    else:
        print(f"EXISTS  Purchase Invoice: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted["docstatus"] != 1:
        raise RuntimeError(f"Purchase Invoice was not submitted: {submitted['name']}")
    return submitted


def ensure_payment(
    api: ERPNextAPI,
    company: str,
    invoice: dict[str, Any],
    cash_account: str,
    amount: float,
) -> dict[str, Any]:
    filters = [
        ["Payment Entry", "company", "=", company],
        ["Payment Entry", "party", "=", invoice["supplier"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        return any(
            row.get("reference_doctype") == "Purchase Invoice"
            and row.get("reference_name") == invoice["name"]
            and float(row.get("allocated_amount", 0)) == float(amount)
            for row in document.get("references", [])
        )

    document = find_doc(api, "Payment Entry", filters, matches)
    if document is None:
        mapped = api.call(
            "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
            {
                "dt": "Purchase Invoice",
                "dn": invoice["name"],
                "party_amount": amount,
                "bank_account": cash_account,
                "reference_date": date.today().isoformat(),
            },
        )
        if not mapped or not mapped.get("references"):
            raise RuntimeError("ERPNext did not map Payment Entry references")
        mapped.pop("name", None)
        mapped["posting_date"] = date.today().isoformat()
        document = api.insert("Payment Entry", mapped)
        print(f"CREATED Payment Entry: {document['name']}")
    else:
        print(f"EXISTS  Payment Entry: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted["docstatus"] != 1:
        raise RuntimeError(f"Payment Entry was not submitted: {submitted['name']}")
    return submitted


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


def validate(api: ERPNextAPI, config: dict[str, Any]) -> None:
    company = config["company"]
    warehouse = config["warehouse"]
    scenarios = config["scenarios"]
    baseline = {
        scenario["item_code"]: stock_balance(api, scenario["item_code"], warehouse)
        for scenario in scenarios.values()
    }

    full_po = ensure_purchase_order(api, company, warehouse, scenarios["full"])
    full_receipt = ensure_purchase_receipt(
        api, company, full_po, scenarios["full"]["qty"]
    )

    partial_po = ensure_purchase_order(api, company, warehouse, scenarios["partial"])
    partial_receipts = [
        ensure_purchase_receipt(api, company, partial_po, qty)
        for qty in scenarios["partial"]["receipt_quantities"]
    ]

    alternate_po = ensure_purchase_order(
        api, company, warehouse, scenarios["alternate_uom"]
    )
    alternate_receipt = ensure_purchase_receipt(
        api, company, alternate_po, scenarios["alternate_uom"]["qty"]
    )

    full_invoice = ensure_purchase_invoice(
        api,
        company,
        "Purchase Receipt",
        full_receipt["name"],
        scenarios["full"]["supplier"],
        scenarios["full"]["supplier_invoice"],
    )
    partial_invoice = ensure_purchase_invoice(
        api,
        company,
        "Purchase Order",
        partial_po["name"],
        scenarios["partial"]["supplier"],
        scenarios["partial"]["supplier_invoice"],
    )

    full_payment = ensure_payment(
        api,
        company,
        full_invoice,
        config["cash_account"],
        float(full_invoice["grand_total"]),
    )
    partial_payment = ensure_payment(
        api,
        company,
        partial_invoice,
        config["cash_account"],
        float(scenarios["partial"]["partial_payment"]),
    )

    purchase_return = ensure_purchase_receipt(
        api,
        company,
        alternate_po,
        scenarios["alternate_uom"]["return_qty"],
        is_return=True,
        return_against=alternate_receipt["name"],
    )

    final_documents = {
        "full_po": api.get_doc("Purchase Order", full_po["name"]),
        "partial_po": api.get_doc("Purchase Order", partial_po["name"]),
        "alternate_po": api.get_doc("Purchase Order", alternate_po["name"]),
        "full_invoice": api.get_doc("Purchase Invoice", full_invoice["name"]),
        "partial_invoice": api.get_doc("Purchase Invoice", partial_invoice["name"]),
    }
    final_stock = {
        item_code: stock_balance(api, item_code, warehouse)
        for item_code in config["expected_final_stock"]
    }
    if final_stock != {
        key: float(value) for key, value in config["expected_final_stock"].items()
    }:
        raise RuntimeError(
            f"Final stock does not match expected values: {final_stock}"
        )

    full_invoice_final = final_documents["full_invoice"]
    partial_invoice_final = final_documents["partial_invoice"]
    if not full_invoice_final or float(full_invoice_final["outstanding_amount"]) != 0:
        raise RuntimeError("Full-payment invoice still has an outstanding amount")
    expected_partial_outstanding = float(partial_invoice["grand_total"]) - float(
        scenarios["partial"]["partial_payment"]
    )
    if not partial_invoice_final or float(
        partial_invoice_final["outstanding_amount"]
    ) != expected_partial_outstanding:
        raise RuntimeError("Partial-payment invoice outstanding amount is incorrect")

    evidence = {
        "baseline_stock": baseline,
        "purchase_orders": {
            key: {"name": value["name"], "status": final_documents[key]["status"]}
            for key, value in {
                "full_po": full_po,
                "partial_po": partial_po,
                "alternate_po": alternate_po,
            }.items()
        },
        "purchase_receipts": [
            full_receipt["name"],
            *[receipt["name"] for receipt in partial_receipts],
            alternate_receipt["name"],
        ],
        "purchase_invoice_full": {
            "name": full_invoice_final["name"],
            "grand_total": full_invoice_final["grand_total"],
            "outstanding_amount": full_invoice_final["outstanding_amount"],
        },
        "purchase_invoice_partial": {
            "name": partial_invoice_final["name"],
            "grand_total": partial_invoice_final["grand_total"],
            "outstanding_amount": partial_invoice_final["outstanding_amount"],
        },
        "payments": [full_payment["name"], partial_payment["name"]],
        "purchase_return": purchase_return["name"],
        "alternate_receipt_stock_qty": alternate_receipt["items"][0]["stock_qty"],
        "return_stock_qty": purchase_return["items"][0]["stock_qty"],
        "final_stock": final_stock,
    }
    print("EVIDENCE " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    print("OK: Phase 0 purchase-flow validation passed")


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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_scenarios(args.scenarios)
        api = ERPNextAPI(args.base_url)
        api.login(args.username, args.password)
        validate(api, config)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
