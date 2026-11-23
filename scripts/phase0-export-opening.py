"""Export one local synthetic company's as-of balances from four native reports."""
import argparse
import csv
from datetime import date
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from phase0_api import ERPNextAPI, validate_disposable_url

REPORTS = ("Stock Balance", "Accounts Receivable", "Accounts Payable", "Trial Balance")
COLUMNS = "kind company key warehouse unit quantity debit credit amount".split()


def number(value, money=True):
    n = Decimal(str(value))
    if not n.is_finite() or (money and n != n.quantize(Decimal(".01"))):
        raise ValueError("原生金额精度或数值异常")
    return n


def normalize(reports, company, cutoff, keep_accounts):
    rows = {}
    for name in REPORTS:
        result = reports[name]
        for index, r in enumerate(result["result"]):
            if isinstance(r, list) and result.get("add_total_row") and index + 1 == len(result["result"]):
                continue  # Frappe appends its presentation total as a positional list.
            if not isinstance(r, dict):
                raise ValueError("无法识别原生报表行：" + name)
            if name == "Trial Balance":
                if not r or (r.get("warn_if_negative") and "is_group_account" not in r):
                    continue  # native separator / report total
                if r["currency"] != "CNY" or r["to_date"] != cutoff:
                    raise ValueError("试算表币种或实际截止日不符")
                if r["is_group_account"]:
                    continue
                key = ("gl", company, r["account"], "", "")
                values = dict(debit=number(r["closing_debit"]), credit=number(r["closing_credit"]))
            elif name == "Stock Balance":
                if r["company"] != company:
                    raise ValueError("库存公司不符")
                key = ("stock", company, r["item_code"], r["warehouse"], r["stock_uom"])
                values = dict(quantity=number(r["bal_qty"], False), amount=number(r["bal_val"]))
            else:
                if r["currency"] != "CNY" or r["posting_date"] > cutoff or not r["voucher_no"]:
                    raise ValueError("账龄表币种、截止日或凭证不符")
                key = ("ar" if name == "Accounts Receivable" else "ap", company, r["party"], "", "")
                rows.setdefault(key, {"amount": Decimal(0)})["amount"] += number(r["outstanding"])
                continue
            if key in rows:
                raise ValueError("库存或试算表重复明细")
            rows[key] = values
    if not keep_accounts <= {k[2] for k in rows if k[0] == "gl"}:
        raise ValueError("试算表缺少映射的叶科目")
    rows = {k:v for k,v in rows.items() if any(v.values()) or (k[0] == "gl" and k[2] in keep_accounts)}
    if sum(v["debit"] - v["credit"] for k,v in rows.items() if k[0] == "gl"):
        raise ValueError("原生目标试算不平")
    return rows


def collect(api, config):
    company, cutoff = config["company"], date.fromisoformat(config["cutoff"]).isoformat()
    if config["currency"] != "CNY" or api.get_doc("Company", company)["default_currency"] != "CNY":
        raise ValueError("公司本位币须为人民币")
    zone = api.get_doc("System Settings", "System Settings")["time_zone"]
    if zone != "Asia/Shanghai":
        raise ValueError("演练站点时区不匹配")
    years = api.list_docs("Fiscal Year", ["name"], [["disabled", "=", 0], ["year_start_date", "<=", cutoff],
                          ["year_end_date", ">=", cutoff]], 0)
    eligible = []
    for row in years:
        y = api.get_doc("Fiscal Year", row["name"])
        if not y["companies"] or company in {c["company"] for c in y["companies"]}:
            eligible.append(y)
    if len(eligible) != 1:
        raise ValueError("截止日无法唯一确定公司财年")
    # v16 trial balance can include future is_opening entries in its opening bucket.
    if api.list_docs("GL Entry", ["name"], [["company","=",company], ["is_cancelled","=",0],
                     ["is_opening","=","Yes"], ["posting_date",">",cutoff]], 1):
        raise ValueError("存在截止日之后的期初分录，不能以原生试算表证明此截止日")
    dates = dict(company=company, from_date=eligible[0]["year_start_date"], to_date=cutoff)
    ageing = dict(company=company, report_date=cutoff, ageing_based_on="Due Date", range1=30, range2=60, range3=90, range4=120)
    trial = dict(dates, fiscal_year=eligible[0]["name"], show_zero_values=1, show_net_values=1,
                 show_unclosed_fy_pl_balances=1, with_period_closing_entry_for_opening=1,
                 with_period_closing_entry_for_current_period=1, include_default_book_entries=1)
    filters = dict(zip(REPORTS, (dates, ageing, ageing, trial)))
    reports = {name:api.run_report(name, f) for name,f in filters.items()}
    rows = normalize(reports, company, cutoff, set(config["gl"].values()))
    return rows, dict(company=company, cutoff=cutoff, currency="CNY", time_zone=zone, filters=filters), reports


def export(api, config, directory):
    rows, meta, reports = collect(api, config)
    # Publish only complete bundles. Never overwrite previous evidence.
    if directory.exists():
        raise ValueError("证据目录已存在")
    with TemporaryDirectory(dir=directory.parent) as tmp:
        stage = Path(tmp) / "bundle"
        stage.mkdir(mode=0o700)
        with (stage / "target.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, COLUMNS)
            writer.writeheader()
            for key, values in sorted(rows.items()):
                writer.writerow(dict(zip(COLUMNS, key), **{k:format(v, "f") for k,v in values.items()}))
        (stage / "reports.json").write_text(json.dumps(reports, ensure_ascii=False), encoding="utf-8")
        meta["sha256"] = {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in stage.iterdir()}
        (stage / "manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        stage.rename(directory)
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mapping", type=Path)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    api = ERPNextAPI(validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://localhost:18081")))
    api.login("Administrator", os.environ.get("PHASE0_PASSWORD", "admin"))
    print("原生报表 4 份；余额行", export(api, json.loads(args.mapping.read_text()), args.directory))
