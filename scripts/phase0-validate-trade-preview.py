#!/usr/bin/env python3
"""Compare the native preview with existing or newly created R1 quote drafts."""

import argparse
import json
import os
from pathlib import Path

from phase0_api import ERPNextAPI, validate_disposable_url

ENDPOINT = "hardware_erp.trade_preview.preview"
BASELINE = Path(__file__).resolve().parents[1] / "phase0/release-baseline.json"


def validate(api, config, create):
    def taxes(mode):
        if mode is None:
            return []
        template = api.get_doc("Sales Taxes and Charges Template", f"R1合成销售{mode} - R1D")
        return [{
            key: row[key] for key in (
                "charge_type", "account_head", "rate", "included_in_print_rate", "description",
            )
        } for row in template["taxes"]]

    company = config["company"]["company_name"]
    for mode, quantities_and_rates, discount, expected_total in (
        (None, [(3, 12.19)], 0, 36.57),
        ("未税", [(2, 81)], 0, 170.10),
        ("含税", [(2, 105)], 0, 210),
        ("未税", [(3, 14.33), (2, 8.29)], 7, 58.17),
    ):
        marker = f"R1-W4-金额预览 {mode or '无税'} {discount}%"
        draft = {
            "doctype": "Quotation", "company": company, "quotation_to": "Customer",
            "party_name": config["customer"], "terms": marker, "currency": "CNY",
            "conversion_rate": 1, "price_list_currency": "CNY", "plc_conversion_rate": 1,
            "selling_price_list": config["selling_price_list"], "ignore_pricing_rule": 1,
            "items": [{
                "item_code": config["item"]["item_code"], "qty": qty, "uom": "Piece",
                "conversion_factor": 1, "rate": rate,
            } for qty, rate in quantities_and_rates],
            "taxes": taxes(mode), "apply_discount_on": "Net Total",
            "additional_discount_percentage": discount,
        }
        result = api.call(ENDPOINT, {"draft": draft})
        assert result == api.call(ENDPOINT, {"draft": json.dumps(draft, ensure_ascii=False)})
        names = api.list_docs("Quotation", ["name"], [["company", "=", company], ["terms", "=", marker]], 2)
        assert len(names) < 2, f"Duplicate fixture: {marker}"
        if names:
            saved = api.get_doc("Quotation", names[0]["name"])
        elif create:
            saved = api.insert("Quotation", draft)
        else:
            raise ValueError(f"Missing draft: {marker}")
        assert saved["docstatus"] == 0 and len(result["rows"]) == len(saved["items"])
        assert result["grand_total"] == saved["grand_total"] == expected_total
        assert result["net_total"] == saved["net_total"]
        assert result["tax_total"] == saved["total_taxes_and_charges"]
        for preview, row in zip(result["rows"], saved["items"]):
            assert preview["net_rate"] == row["net_rate"]
            assert preview["net_amount"] == row["net_amount"]
            for key in ("gross_amount", "gross_rate", "tax_percent"):
                assert preview[key] == row["custom_trade_" + key]
        print(f"PASS {marker}: {result['net_total']} + {result['tax_total']} = {expected_total}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-drafts", action="store_true")
    args = parser.parse_args()
    base = validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://127.0.0.1:8080"))
    guest = ERPNextAPI(base)
    try:
        guest.call(ENDPOINT, {"draft": {"doctype": "Quotation"}})
    except RuntimeError as error:
        assert "HTTP 403" in str(error)
    else:
        raise AssertionError("Guest preview was accepted.")
    print("PASS guest denied")
    api = ERPNextAPI(base)
    api.login(os.environ.get("PHASE0_USERNAME", "Administrator"), os.environ.get("PHASE0_PASSWORD", "admin"))
    validate(api, json.loads(BASELINE.read_text()), args.create_drafts)


if __name__ == "__main__":
    main()
