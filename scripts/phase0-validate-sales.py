#!/usr/bin/env python3
"""Execute and verify synthetic Phase 0 quote-to-cash scenarios."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

from phase0_api import ERPNextAPI


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIOS = ROOT / "phase0" / "sales-validation.json"


def load_scenarios(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        config = json.load(file)
    required = {"full", "partial", "alternate_uom"}
    if set(config.get("scenarios", {})) != required:
        raise ValueError(f"Sales scenarios must be exactly: {sorted(required)}")
    for name, scenario in config["scenarios"].items():
        delivered = sum(float(qty) for qty in scenario["delivery_quantities"])
        if delivered != float(scenario["qty"]):
            raise ValueError(f"{name} delivery quantities do not equal ordered quantity")
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


def item_matches(row: dict[str, Any], scenario: dict[str, Any], qty: float) -> bool:
    return (
        row.get("item_code") == scenario["item_code"]
        and float(row.get("qty", 0)) == float(qty)
        and row.get("uom") == scenario["uom"]
        and float(row.get("conversion_factor", 0))
        == float(scenario["conversion_factor"])
        and float(row.get("rate", 0)) == float(scenario["rate"])
    )


def ensure_submitted(api: ERPNextAPI, document: dict[str, Any]) -> dict[str, Any]:
    if document.get("docstatus") == 1:
        return document
    return api.submit(document)


def ensure_quotation(
    api: ERPNextAPI, config: dict[str, Any], scenario: dict[str, Any]
) -> dict[str, Any]:
    filters = [
        ["Quotation", "company", "=", config["company"]],
        ["Quotation", "party_name", "=", scenario["customer"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and item_matches(rows[0], scenario, scenario["qty"])

    document = find_doc(api, "Quotation", filters, matches)
    if document is None:
        today = date.today()
        document = api.insert(
            "Quotation",
            {
                "quotation_to": "Customer",
                "party_name": scenario["customer"],
                "company": config["company"],
                "transaction_date": today.isoformat(),
                "valid_till": (today + timedelta(days=30)).isoformat(),
                "selling_price_list": "Standard Selling",
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "qty": scenario["qty"],
                        "uom": scenario["uom"],
                        "conversion_factor": scenario["conversion_factor"],
                        "rate": scenario["rate"],
                        "warehouse": config["warehouse"],
                    }
                ],
            },
        )
        print(f"CREATED Quotation: {document['name']}")
    else:
        print(f"EXISTS  Quotation: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Quotation was not submitted: {submitted['name']}")
    return submitted


def ensure_sales_order(
    api: ERPNextAPI,
    config: dict[str, Any],
    scenario: dict[str, Any],
    quotation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters = [
        ["Sales Order", "company", "=", config["company"]],
        ["Sales Order", "customer", "=", scenario["customer"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        if len(rows) != 1 or not item_matches(rows[0], scenario, scenario["qty"]):
            return False
        return quotation is None or rows[0].get("prevdoc_docname") == quotation["name"]

    document = find_doc(api, "Sales Order", filters, matches)
    if document is None:
        today = date.today().isoformat()
        if quotation is not None:
            document_data = api.call(
                "erpnext.selling.doctype.quotation.quotation.make_sales_order",
                {"source_name": quotation["name"]},
            )
            if not document_data or len(document_data.get("items", [])) != 1:
                raise RuntimeError("ERPNext did not map exactly one Sales Order item")
            document_data.pop("name", None)
            document_data["transaction_date"] = today
            document_data["delivery_date"] = today
            document_data["items"][0]["delivery_date"] = today
        else:
            document_data = {
                "customer": scenario["customer"],
                "company": config["company"],
                "transaction_date": today,
                "delivery_date": today,
                "selling_price_list": "Standard Selling",
                "set_warehouse": config["warehouse"],
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "qty": scenario["qty"],
                        "uom": scenario["uom"],
                        "conversion_factor": scenario["conversion_factor"],
                        "rate": scenario["rate"],
                        "warehouse": config["warehouse"],
                        "delivery_date": today,
                    }
                ],
            }
        document = api.insert("Sales Order", document_data)
        print(f"CREATED Sales Order: {document['name']}")
    else:
        print(f"EXISTS  Sales Order: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Sales Order was not submitted: {submitted['name']}")
    return submitted


def ensure_delivery_note(
    api: ERPNextAPI,
    config: dict[str, Any],
    scenario: dict[str, Any],
    sales_order: dict[str, Any],
    qty: float,
) -> dict[str, Any]:
    filters = [
        ["Delivery Note", "company", "=", config["company"]],
        ["Delivery Note", "customer", "=", scenario["customer"]],
        ["Delivery Note", "is_return", "=", 0],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            item_matches(rows[0], scenario, qty)
            and rows[0].get("against_sales_order") == sales_order["name"]
        )

    document = find_doc(api, "Delivery Note", filters, matches)
    if document is None:
        mapped = api.call(
            "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
            {"source_name": sales_order["name"]},
        )
        if not mapped or len(mapped.get("items", [])) != 1:
            raise RuntimeError("ERPNext did not map exactly one Delivery Note item")
        mapped.pop("name", None)
        mapped["posting_date"] = date.today().isoformat()
        row = mapped["items"][0]
        row["qty"] = qty
        row["stock_qty"] = float(qty) * float(row["conversion_factor"])
        document = api.insert("Delivery Note", mapped)
        print(f"CREATED Delivery Note: {document['name']}")
    else:
        print(f"EXISTS  Delivery Note: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Delivery Note was not submitted: {submitted['name']}")
    return submitted


def ensure_sales_invoice(
    api: ERPNextAPI,
    config: dict[str, Any],
    scenario: dict[str, Any],
    sales_order: dict[str, Any],
) -> dict[str, Any]:
    filters = [
        ["Sales Invoice", "company", "=", config["company"]],
        ["Sales Invoice", "customer", "=", scenario["customer"]],
        ["Sales Invoice", "is_return", "=", 0],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            item_matches(rows[0], scenario, scenario["qty"])
            and rows[0].get("sales_order") == sales_order["name"]
        )

    document = find_doc(api, "Sales Invoice", filters, matches)
    if document is None:
        mapped = api.call(
            "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
            {"source_name": sales_order["name"]},
        )
        if not mapped or len(mapped.get("items", [])) != 1:
            raise RuntimeError("ERPNext did not map exactly one Sales Invoice item")
        mapped.pop("name", None)
        mapped["posting_date"] = date.today().isoformat()
        mapped["due_date"] = date.today().isoformat()
        document = api.insert("Sales Invoice", mapped)
        print(f"CREATED Sales Invoice: {document['name']}")
    else:
        print(f"EXISTS  Sales Invoice: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Sales Invoice was not submitted: {submitted['name']}")
    return submitted


def ensure_payment(
    api: ERPNextAPI,
    config: dict[str, Any],
    invoice: dict[str, Any],
    amount: float,
) -> dict[str, Any]:
    filters = [
        ["Payment Entry", "company", "=", config["company"]],
        ["Payment Entry", "party_type", "=", "Customer"],
        ["Payment Entry", "party", "=", invoice["customer"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        return any(
            row.get("reference_doctype") == "Sales Invoice"
            and row.get("reference_name") == invoice["name"]
            and float(row.get("allocated_amount", 0)) == float(amount)
            for row in document.get("references", [])
        )

    document = find_doc(api, "Payment Entry", filters, matches)
    if document is None:
        mapped = api.call(
            "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
            {
                "dt": "Sales Invoice",
                "dn": invoice["name"],
                "party_amount": amount,
                "bank_account": config["cash_account"],
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
    if submitted.get("docstatus") != 1:
        raise RuntimeError(f"Payment Entry was not submitted: {submitted['name']}")
    return submitted


def ensure_delivery_return(
    api: ERPNextAPI,
    config: dict[str, Any],
    scenario: dict[str, Any],
    delivery_note: dict[str, Any],
) -> dict[str, Any]:
    filters = [
        ["Delivery Note", "company", "=", config["company"]],
        ["Delivery Note", "customer", "=", scenario["customer"]],
        ["Delivery Note", "is_return", "=", 1],
        ["Delivery Note", "return_against", "=", delivery_note["name"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            rows[0].get("item_code") == scenario["item_code"]
            and rows[0].get("uom") == scenario["uom"]
            and float(rows[0].get("qty", 0))
            == -abs(float(scenario["return_qty"]))
            and float(rows[0].get("conversion_factor", 0))
            == float(scenario["conversion_factor"])
        )

    document = find_doc(api, "Delivery Note", filters, matches)
    if document is None:
        mapped = api.call(
            "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return",
            {"source_name": delivery_note["name"]},
        )
        if not mapped or len(mapped.get("items", [])) != 1:
            raise RuntimeError("ERPNext did not map exactly one Sales Return item")
        mapped.pop("name", None)
        mapped["posting_date"] = date.today().isoformat()
        document = api.insert("Delivery Note", mapped)
        print(f"CREATED Sales Return Delivery Note: {document['name']}")
    else:
        print(f"EXISTS  Sales Return Delivery Note: {document['name']}")
    submitted = ensure_submitted(api, document)
    row = submitted.get("items", [None])[0]
    expected_qty = -abs(float(scenario["return_qty"]))
    expected_stock_qty = expected_qty * float(scenario["conversion_factor"])
    if (
        submitted.get("docstatus") != 1
        or not row
        or float(row.get("qty", 0)) != expected_qty
        or float(row.get("stock_qty", 0)) != expected_stock_qty
    ):
        raise RuntimeError("Sales Return Delivery Note quantities are incorrect")
    return submitted


def ensure_credit_note(
    api: ERPNextAPI,
    config: dict[str, Any],
    scenario: dict[str, Any],
    invoice: dict[str, Any],
) -> dict[str, Any]:
    filters = [
        ["Sales Invoice", "company", "=", config["company"]],
        ["Sales Invoice", "customer", "=", scenario["customer"]],
        ["Sales Invoice", "is_return", "=", 1],
        ["Sales Invoice", "return_against", "=", invoice["name"]],
    ]

    def matches(document: dict[str, Any]) -> bool:
        rows = document.get("items", [])
        return len(rows) == 1 and (
            rows[0].get("item_code") == scenario["item_code"]
            and rows[0].get("uom") == scenario["uom"]
            and float(rows[0].get("qty", 0)) == -abs(float(scenario["return_qty"]))
            and float(rows[0].get("conversion_factor", 0))
            == float(scenario["conversion_factor"])
            and float(rows[0].get("rate", 0)) == float(scenario["rate"])
        )

    document = find_doc(api, "Sales Invoice", filters, matches)
    if document is None:
        mapped = api.call(
            "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
            {"source_name": invoice["name"]},
        )
        if not mapped or len(mapped.get("items", [])) != 1:
            raise RuntimeError("ERPNext did not map exactly one Credit Note item")
        mapped.pop("name", None)
        mapped["posting_date"] = date.today().isoformat()
        document = api.insert("Sales Invoice", mapped)
        print(f"CREATED Sales Invoice Credit Note: {document['name']}")
    else:
        print(f"EXISTS  Sales Invoice Credit Note: {document['name']}")
    submitted = ensure_submitted(api, document)
    if submitted.get("docstatus") != 1 or float(submitted.get("grand_total", 0)) >= 0:
        raise RuntimeError("Sales Invoice Credit Note was not submitted as a return")
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


def gl_entries(api: ERPNextAPI, voucher_no: str) -> list[dict[str, Any]]:
    return api.list_docs(
        "GL Entry",
        [
            "name",
            "account",
            "party_type",
            "party",
            "debit",
            "credit",
            "voucher_type",
            "voucher_no",
            "against_voucher_type",
            "against_voucher",
        ],
        [
            ["GL Entry", "voucher_no", "=", voucher_no],
            ["GL Entry", "is_cancelled", "=", 0],
        ],
        100,
    )


def party_gl_amount(
    entries: list[dict[str, Any]], customer: str, field: str
) -> float:
    return sum(
        float(row.get(field, 0))
        for row in entries
        if row.get("party_type") == "Customer" and row.get("party") == customer
    )


def validate(api: ERPNextAPI, config: dict[str, Any]) -> None:
    scenarios = config["scenarios"]
    baseline = {
        scenario["item_code"]: stock_balance(
            api, scenario["item_code"], config["warehouse"]
        )
        for scenario in scenarios.values()
    }

    quotation = ensure_quotation(api, config, scenarios["full"])
    orders = {
        "full": ensure_sales_order(api, config, scenarios["full"], quotation),
        "partial": ensure_sales_order(api, config, scenarios["partial"]),
        "alternate_uom": ensure_sales_order(api, config, scenarios["alternate_uom"]),
    }
    deliveries = {
        name: [
            ensure_delivery_note(api, config, scenarios[name], orders[name], qty)
            for qty in scenarios[name]["delivery_quantities"]
        ]
        for name in scenarios
    }
    invoices = {
        name: ensure_sales_invoice(api, config, scenarios[name], orders[name])
        for name in scenarios
    }
    payments = {
        name: ensure_payment(
            api, config, invoices[name], float(scenarios[name]["payment"])
        )
        for name in ("full", "partial")
    }
    delivery_return = ensure_delivery_return(
        api,
        config,
        scenarios["alternate_uom"],
        deliveries["alternate_uom"][0],
    )
    credit_note = ensure_credit_note(
        api, config, scenarios["alternate_uom"], invoices["alternate_uom"]
    )

    final_orders = {
        name: api.get_doc("Sales Order", order["name"])
        for name, order in orders.items()
    }
    final_invoices = {
        name: api.get_doc("Sales Invoice", invoice["name"])
        for name, invoice in invoices.items()
    }
    final_stock = {
        item_code: stock_balance(api, item_code, config["warehouse"])
        for item_code in config["expected_final_stock"]
    }
    expected_stock = {
        item_code: float(qty)
        for item_code, qty in config["expected_final_stock"].items()
    }
    if final_stock != expected_stock:
        raise RuntimeError(f"Final stock does not match expected values: {final_stock}")

    for name in ("full", "partial"):
        order = final_orders[name]
        if not order or float(order.get("per_delivered", 0)) != 100:
            raise RuntimeError(f"{name} Sales Order is not fully delivered")
    alternate_order = final_orders["alternate_uom"]
    if not alternate_order or float(alternate_order.get("per_delivered", 0)) != 0:
        raise RuntimeError(
            "Returned alternate-UOM Sales Order does not show zero net delivery"
        )
    full_invoice = final_invoices["full"]
    partial_invoice = final_invoices["partial"]
    if not full_invoice or float(full_invoice["outstanding_amount"]) != 0:
        raise RuntimeError("Full-payment Sales Invoice still has an outstanding amount")
    expected_partial_outstanding = float(partial_invoice["grand_total"]) - float(
        scenarios["partial"]["payment"]
    )
    if not partial_invoice or float(
        partial_invoice["outstanding_amount"]
    ) != expected_partial_outstanding:
        raise RuntimeError("Partial-payment Sales Invoice outstanding amount is incorrect")

    invoice_gl = {
        name: gl_entries(api, invoice["name"])
        for name, invoice in invoices.items()
    }
    payment_gl = {
        name: gl_entries(api, payment["name"])
        for name, payment in payments.items()
    }
    credit_gl = gl_entries(api, credit_note["name"])
    for name in scenarios:
        expected = float(invoices[name]["grand_total"])
        actual = party_gl_amount(invoice_gl[name], scenarios[name]["customer"], "debit")
        if actual != expected:
            raise RuntimeError(
                f"{name} invoice receivable GL debit is incorrect: {actual}"
            )
    for name in payments:
        expected = float(scenarios[name]["payment"])
        actual = party_gl_amount(
            payment_gl[name], scenarios[name]["customer"], "credit"
        )
        if actual != expected:
            raise RuntimeError(
                f"{name} payment receivable GL credit is incorrect: {actual}"
            )
    expected_credit = abs(float(credit_note["grand_total"]))
    actual_credit = party_gl_amount(
        credit_gl, scenarios["alternate_uom"]["customer"], "credit"
    )
    if actual_credit != expected_credit:
        raise RuntimeError(f"Credit Note receivable GL credit is incorrect: {actual_credit}")

    alternate_delivery_row = deliveries["alternate_uom"][0]["items"][0]
    if float(alternate_delivery_row.get("stock_qty", 0)) != 50:
        raise RuntimeError("Alternate-UOM Delivery Note did not convert 1 Box to 50 Piece")

    evidence = {
        "baseline_stock": baseline,
        "quotation": quotation["name"],
        "sales_orders": {
            name: {
                "name": order["name"],
                "status": final_orders[name]["status"],
                "per_delivered": final_orders[name]["per_delivered"],
                "per_billed": final_orders[name]["per_billed"],
            }
            for name, order in orders.items()
        },
        "delivery_notes": {
            name: [document["name"] for document in documents]
            for name, documents in deliveries.items()
        },
        "sales_invoices": {
            name: {
                "name": final_invoices[name]["name"],
                "grand_total": final_invoices[name]["grand_total"],
                "outstanding_amount": final_invoices[name]["outstanding_amount"],
            }
            for name in final_invoices
        },
        "payments": {name: payment["name"] for name, payment in payments.items()},
        "sales_return_delivery": {
            "name": delivery_return["name"],
            "return_against": delivery_return["return_against"],
            "qty": delivery_return["items"][0]["qty"],
            "stock_qty": delivery_return["items"][0]["stock_qty"],
        },
        "credit_note": {
            "name": credit_note["name"],
            "return_against": credit_note["return_against"],
            "grand_total": credit_note["grand_total"],
            "outstanding_amount": credit_note["outstanding_amount"],
        },
        "receivable_gl": {
            name: party_gl_amount(invoice_gl[name], scenarios[name]["customer"], "debit")
            for name in invoice_gl
        },
        "payment_gl": {
            name: party_gl_amount(payment_gl[name], scenarios[name]["customer"], "credit")
            for name in payment_gl
        },
        "credit_note_gl": actual_credit,
        "alternate_delivery_stock_qty": alternate_delivery_row["stock_qty"],
        "final_stock": final_stock,
    }
    print("EVIDENCE " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    print("OK: Phase 0 sales and accounts-receivable validation passed")


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
