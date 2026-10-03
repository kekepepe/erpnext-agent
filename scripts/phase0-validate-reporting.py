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
            {
                **date_filters,
                "categorize_by": "Categorize by Voucher (Consolidated)",
            },
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


def ageing_filters(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "company": config["company"],
        "report_date": config["report_date"],
        "ageing_based_on": "Due Date",
        "range1": 30,
        "range2": 60,
        "range3": 90,
        "range4": 120,
    }


def validate_ageing_row(
    api: ERPNextAPI, config: dict[str, Any], section: str
) -> dict[str, Any]:
    expected = config[section]
    result = api.run_report(expected["report_name"], ageing_filters(config))
    matches = [
        row
        for row in dict_rows(result)
        if row.get("voucher_no") == expected["voucher_no"]
        and row.get("party") == expected["party"]
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"{expected['report_name']} expected one target row, got {len(matches)}"
        )
    row = matches[0]
    for field in ["invoiced", "paid", "outstanding"]:
        assert_number(
            row.get(field), expected[field], f"{expected['report_name']} {field}"
        )
    source_doctype = (
        "Sales Invoice" if section == "accounts_receivable" else "Purchase Invoice"
    )
    source = api.get_doc(source_doctype, expected["voucher_no"])
    if not source or int(source.get("docstatus", 0)) != 1:
        raise RuntimeError(f"Missing submitted source {source_doctype}")
    assert_number(
        source.get("outstanding_amount"),
        expected["outstanding"],
        f"{source_doctype} outstanding",
    )
    return {
        "voucher_no": row["voucher_no"],
        "party": row["party"],
        "invoiced": float(row["invoiced"]),
        "paid": float(row["paid"]),
        "outstanding": float(row["outstanding"]),
    }


def validate_general_ledger(
    api: ERPNextAPI, config: dict[str, Any]
) -> dict[str, Any]:
    expected = config["general_ledger"]
    filters = {
        "company": config["company"],
        "from_date": config["from_date"],
        "to_date": config["to_date"],
        "categorize_by": "Categorize by Voucher (Consolidated)",
    }
    report_rows = dict_rows(api.run_report(expected["report_name"], filters))
    verified: dict[str, dict[str, float]] = {}
    for voucher_no in expected["required_vouchers"]:
        selected = [row for row in report_rows if row.get("voucher_no") == voucher_no]
        if not selected:
            raise RuntimeError(f"General Ledger is missing voucher {voucher_no}")
        debit = sum(float(row.get("debit", 0)) for row in selected)
        credit = sum(float(row.get("credit", 0)) for row in selected)
        assert_number(debit, credit, f"General Ledger balance {voucher_no}")
        if debit <= 0:
            raise RuntimeError(f"General Ledger voucher has no value: {voucher_no}")
        voucher_type = selected[0].get("voucher_type")
        if not voucher_type:
            raise RuntimeError(f"General Ledger voucher type missing: {voucher_no}")
        source = api.get_doc(voucher_type, voucher_no)
        if not source or int(source.get("docstatus", 0)) != 1:
            raise RuntimeError(f"Missing submitted source {voucher_type} {voucher_no}")
        resource_rows = api.list_docs(
            "GL Entry",
            ["name", "debit", "credit", "voucher_type", "voucher_no", "is_cancelled"],
            [
                ["GL Entry", "voucher_no", "=", voucher_no],
                ["GL Entry", "is_cancelled", "=", 0],
            ],
            100,
        )
        if not resource_rows:
            raise RuntimeError(f"No active GL Entry rows for {voucher_no}")
        assert_number(
            sum(float(row.get("debit", 0)) for row in resource_rows),
            debit,
            f"GL resource/report debit {voucher_no}",
        )
        assert_number(
            sum(float(row.get("credit", 0)) for row in resource_rows),
            credit,
            f"GL resource/report credit {voucher_no}",
        )
        verified[voucher_no] = {"debit": debit, "credit": credit}

    cancelled = expected["cancelled_payment"]
    default_cancelled_rows = [
        row for row in report_rows if row.get("voucher_no") == cancelled
    ]
    if default_cancelled_rows:
        raise RuntimeError("Cancelled Payment Entry appeared in default General Ledger")
    cancelled_filters = {
        **filters,
        "voucher_no": cancelled,
        "show_cancelled_entries": 1,
    }
    cancelled_rows = [
        row
        for row in dict_rows(api.run_report(expected["report_name"], cancelled_filters))
        if row.get("voucher_no") == cancelled
    ]
    if len(cancelled_rows) != 2:
        raise RuntimeError(
            f"Expected two consolidated cancelled GL rows, got {len(cancelled_rows)}"
        )
    cancel_debit = sum(float(row.get("debit", 0)) for row in cancelled_rows)
    cancel_credit = sum(float(row.get("credit", 0)) for row in cancelled_rows)
    assert_number(cancel_debit, cancel_credit, "Cancelled General Ledger net")
    resource_cancelled = api.list_docs(
        "GL Entry",
        ["name", "debit", "credit", "account", "voucher_no", "is_cancelled"],
        [["GL Entry", "voucher_no", "=", cancelled]],
        100,
    )
    if len(resource_cancelled) != 4 or any(
        int(row.get("is_cancelled", 0)) != 1 for row in resource_cancelled
    ):
        raise RuntimeError("Cancelled Payment Entry GL audit rows are incomplete")
    assert_number(
        sum(float(row.get("debit", 0)) for row in resource_cancelled),
        sum(float(row.get("credit", 0)) for row in resource_cancelled),
        "Cancelled GL resource net",
    )
    return {
        "active_vouchers": verified,
        "cancelled_payment": {
            "voucher_no": cancelled,
            "default_report_rows": 0,
            "cancelled_report_rows": len(cancelled_rows),
            "resource_rows": len(resource_cancelled),
            "debit": cancel_debit,
            "credit": cancel_credit,
        },
    }


def validate_accounting_reports(
    api: ERPNextAPI, config: dict[str, Any]
) -> dict[str, Any]:
    evidence = {
        "accounts_receivable": validate_ageing_row(
            api, config, "accounts_receivable"
        ),
        "accounts_payable": validate_ageing_row(api, config, "accounts_payable"),
        "general_ledger": validate_general_ledger(api, config),
    }
    print("ACCOUNTS " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
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
            "accounting": validate_accounting_reports(api, config),
        }
        print("EVIDENCE " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
        print("OK: Phase 0 native operational and accounting reports are reproducible")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
