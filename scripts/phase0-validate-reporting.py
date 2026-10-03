#!/usr/bin/env python3
"""Execute read-only native report checks for the Phase 0 evidence dataset."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from phase0_api import ERPNextAPI


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "phase0" / "reporting-validation.json"


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    required = {
        "company",
        "from_date",
        "to_date",
        "report_date",
        "stock_balance",
        "stock_ledger",
        "purchase_analytics",
        "sales_analytics",
        "accounts_receivable",
        "accounts_payable",
        "general_ledger",
        "print_output",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"Reporting configuration is missing: {sorted(missing)}")
    if config["from_date"] > config["to_date"]:
        raise ValueError("Reporting from_date must not be after to_date")
    return config


def report_filters(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    company = config["company"]
    date_filters = {
        "company": company,
        "from_date": config["from_date"],
        "to_date": config["to_date"],
    }
    analytics_common = {
        **date_filters,
        "value_quantity": "Quantity",
        "range": "Monthly",
    }
    ageing = {
        "company": company,
        "report_date": config["report_date"],
        "ageing_based_on": "Due Date",
        "range1": 30,
        "range2": 60,
        "range3": 90,
        "range4": 120,
    }
    return [
        (config["stock_balance"]["report_name"], date_filters),
        (config["stock_ledger"]["report_name"], date_filters),
        (
            config["purchase_analytics"]["report_name"],
            {
                **analytics_common,
                "tree_type": "Supplier",
                "doc_type": "Purchase Order",
            },
        ),
        (
            config["purchase_analytics"]["report_name"],
            {
                **analytics_common,
                "tree_type": "Item",
                "doc_type": "Purchase Order",
            },
        ),
        (
            config["sales_analytics"]["report_name"],
            {
                **analytics_common,
                "tree_type": "Customer",
                "doc_type": "Sales Order",
                "curves": "select",
            },
        ),
        (
            config["sales_analytics"]["report_name"],
            {
                **analytics_common,
                "tree_type": "Item",
                "doc_type": "Sales Order",
                "curves": "select",
            },
        ),
        (config["accounts_receivable"]["report_name"], ageing),
        (config["accounts_payable"]["report_name"], ageing),
        (
            config["general_ledger"]["report_name"],
            {**date_filters, "group_by": "Group by Voucher (Consolidated)"},
        ),
    ]


def validate_report_interfaces(
    api: ERPNextAPI, config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    required_columns = {
        "Stock Balance": {"item_code", "warehouse", "bal_qty"},
        "Stock Ledger": {
            "item_code",
            "warehouse",
            "qty_after_transaction",
            "voucher_type",
            "voucher_no",
        },
        "Purchase Analytics": {"entity", "total"},
        "Sales Analytics": {"entity", "total"},
        "Accounts Receivable": {
            "party",
            "voucher_no",
            "invoiced",
            "paid",
            "outstanding",
        },
        "Accounts Payable": {
            "party",
            "voucher_no",
            "invoiced",
            "paid",
            "outstanding",
        },
        "General Ledger": {
            "posting_date",
            "account",
            "debit",
            "credit",
            "voucher_type",
            "voucher_no",
        },
    }
    evidence: dict[str, dict[str, Any]] = {}
    occurrence: dict[str, int] = {}
    for report_name, filters in report_filters(config):
        report = api.get_doc("Report", report_name)
        if not report or report.get("is_standard") != "Yes":
            raise RuntimeError(f"Report is not a standard ERPNext report: {report_name}")
        result = api.run_report(report_name, filters)
        columns = {
            column.get("fieldname")
            for column in result.get("columns", [])
            if isinstance(column, dict)
        }
        missing = required_columns[report_name] - columns
        if missing:
            raise RuntimeError(
                f"Report {report_name} is missing columns: {sorted(missing)}"
            )
        occurrence[report_name] = occurrence.get(report_name, 0) + 1
        key = f"{report_name}#{occurrence[report_name]}"
        evidence[key] = {
            "report_type": report.get("report_type"),
            "rows": len(result["result"]),
            "columns": sorted(columns),
            "filters": filters,
        }
        print(f"REPORT  {key}: rows={len(result['result'])}")
    return evidence


def dict_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in result["result"] if isinstance(row, dict)]


def assert_number(actual: Any, expected: Any, label: str) -> None:
    if abs(float(actual) - float(expected)) > 0.000001:
        raise RuntimeError(f"{label}: expected {expected}, got {actual}")


def validate_stock_reports(
    api: ERPNextAPI, config: dict[str, Any]
) -> dict[str, Any]:
    filters = {
        "company": config["company"],
        "from_date": config["from_date"],
        "to_date": config["to_date"],
    }
    balance_result = api.run_report(
        config["stock_balance"]["report_name"], filters
    )
    balance_rows = {
        (row["item_code"], row["warehouse"]): row
        for row in dict_rows(balance_result)
        if row.get("item_code") and row.get("warehouse")
    }
    verified_balances: dict[str, float] = {}
    for expected in config["stock_balance"]["expected_balances"]:
        key = (expected["item_code"], expected["warehouse"])
        row = balance_rows.get(key)
        if not row:
            raise RuntimeError(f"Stock Balance is missing {key}")
        assert_number(row.get("bal_qty"), expected["qty"], f"Stock Balance {key}")
        verified_balances[f"{key[0]} @ {key[1]}"] = float(row["bal_qty"])

    ledger_result = api.run_report(
        config["stock_ledger"]["report_name"], filters
    )
    report_rows = dict_rows(ledger_result)
    verified_vouchers: dict[str, int] = {}
    for expected in config["stock_ledger"]["expected_vouchers"]:
        voucher_no = expected["voucher_no"]
        voucher_type = expected["voucher_type"]
        selected = [
            row
            for row in report_rows
            if row.get("voucher_no") == voucher_no
            and row.get("voucher_type") == voucher_type
        ]
        if not selected:
            raise RuntimeError(
                f"Stock Ledger report is missing {voucher_type} {voucher_no}"
            )
        ledger_rows = api.list_docs(
            "Stock Ledger Entry",
            [
                "name",
                "item_code",
                "warehouse",
                "qty_after_transaction",
                "voucher_type",
                "voucher_no",
            ],
            [
                ["Stock Ledger Entry", "voucher_no", "=", voucher_no],
                ["Stock Ledger Entry", "is_cancelled", "=", 0],
            ],
            500,
        )
        report_signature = {
            (
                row["item_code"],
                row["warehouse"],
                float(row["qty_after_transaction"]),
                row["voucher_type"],
                row["voucher_no"],
            )
            for row in selected
        }
        ledger_signature = {
            (
                row["item_code"],
                row["warehouse"],
                float(row["qty_after_transaction"]),
                row["voucher_type"],
                row["voucher_no"],
            )
            for row in ledger_rows
        }
        if report_signature != ledger_signature:
            raise RuntimeError(
                f"Stock Ledger report/resource mismatch for {voucher_no}: "
                f"report={report_signature}, resource={ledger_signature}"
            )
        verified_vouchers[voucher_no] = len(selected)

    evidence = {
        "balances": verified_balances,
        "voucher_row_counts": verified_vouchers,
    }
    print("STOCK   " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return evidence


def analytics_filters(
    config: dict[str, Any], tree_type: str, doc_type: str
) -> dict[str, Any]:
    filters = {
        "company": config["company"],
        "from_date": config["from_date"],
        "to_date": config["to_date"],
        "tree_type": tree_type,
        "doc_type": doc_type,
        "value_quantity": "Quantity",
        "range": "Monthly",
    }
    if doc_type == "Sales Order":
        filters["curves"] = "select"
    return filters


def validate_analytics_rows(
    api: ERPNextAPI,
    report_name: str,
    filters: dict[str, Any],
    expected: dict[str, Any],
    label: str,
) -> dict[str, float]:
    result = api.run_report(report_name, filters)
    actual = {
        row["entity"]: float(row["total"])
        for row in dict_rows(result)
        if row.get("entity")
    }
    expected_numbers = {key: float(value) for key, value in expected.items()}
    if actual != expected_numbers:
        raise RuntimeError(f"{label} mismatch: expected {expected_numbers}, got {actual}")
    return actual


def validate_purchase_sales_reports(
    api: ERPNextAPI, config: dict[str, Any]
) -> dict[str, dict[str, float]]:
    purchase = config["purchase_analytics"]
    sales = config["sales_analytics"]
    evidence = {
        "purchase_by_supplier": validate_analytics_rows(
            api,
            purchase["report_name"],
            analytics_filters(config, "Supplier", "Purchase Order"),
            purchase["by_supplier"],
            "Purchase Analytics by supplier",
        ),
        "purchase_by_item": validate_analytics_rows(
            api,
            purchase["report_name"],
            analytics_filters(config, "Item", "Purchase Order"),
            purchase["by_item"],
            "Purchase Analytics by item",
        ),
        "sales_by_customer": validate_analytics_rows(
            api,
            sales["report_name"],
            analytics_filters(config, "Customer", "Sales Order"),
            sales["by_customer"],
            "Sales Analytics by customer",
        ),
        "sales_by_item": validate_analytics_rows(
            api,
            sales["report_name"],
            analytics_filters(config, "Item", "Sales Order"),
            sales["by_item"],
            "Sales Analytics by item",
        ),
    }
    print("TRADE   " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return evidence


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
        config = load_config(args.scenarios)
        api = ERPNextAPI(args.base_url)
        api.login(args.username, args.password)
        evidence = {
            "interfaces": validate_report_interfaces(api, config),
            "stock": validate_stock_reports(api, config),
            "trade": validate_purchase_sales_reports(api, config),
        }
        print("EVIDENCE " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
        print("OK: Phase 0 native stock, purchase, and sales reports are reproducible")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
