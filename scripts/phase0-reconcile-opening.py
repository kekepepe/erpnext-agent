"""Compare normalized opening snapshots offline. Do not print private keys or balances."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUMNS = ["kind", "company", "key", "warehouse", "unit", "quantity", "debit", "credit", "amount"]

def snapshot(path):
    rows = {}
    gl_totals = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError("列名或顺序错误")
        for number, row in enumerate(reader, 2):
            if None in row or None in row.values():
                raise ValueError(f"第 {number} 行列数错误")
            kind, company, key, warehouse, unit = [row[k].strip() for k in COLUMNS[:5]]
            if kind not in {"stock","ar","ap","gl"} or not company or not key:
                raise ValueError(f"第 {number} 行类型或业务键无效")
            if (kind == "stock") != bool(warehouse and unit) or (kind != "stock" and (warehouse or unit)):
                raise ValueError(f"第 {number} 行仓库或库存单位无效")
            identity = kind, company, key, warehouse, unit
            if identity in rows:
                raise ValueError(f"第 {number} 行业务键重复")
            required = {"stock": {"quantity","amount"}, "ar":{"amount"}, "ap":{"amount"}, "gl":{"debit","credit"}}[kind]
            values = {}
            for field in COLUMNS[5:]:
                raw = row[field].strip()
                if bool(raw) != (field in required):
                    raise ValueError(f"第 {number} 行 {field} 填写错误")
                if raw:
                    try:
                        value = Decimal(raw)
                    except InvalidOperation:
                        raise ValueError(f"第 {number} 行数值无效") from None
                    if not value.is_finite() or (field != "quantity" and value.as_tuple().exponent < -2):
                        raise ValueError(f"第 {number} 行数值或金额精度错误")
                    values[field] = value
            rows[identity] = values
            if kind == "gl":
                if min(values.values()) < 0:
                    raise ValueError(f"第 {number} 行借贷金额为负")
                gl_totals[company] = gl_totals.get(company, Decimal(0)) + values["debit"] - values["credit"]
    if not rows or any(gl_totals.values()):
        raise ValueError("快照为空或公司期初试算不平")
    return rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    before, after = snapshot(args.source), snapshot(args.target)
    missing, added = before.keys() - after.keys(), after.keys() - before.keys()
    changed = sum(before[k] != after[k] for k in before.keys() & after.keys())
    print(f"源行 {len(before)}，目标行 {len(after)}，缺失 {len(missing)}，新增 {len(added)}，差异 {changed}")
    return int(bool(missing or added or changed))

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
