"""Replay synthetic item masters through native REST on the isolated migration site."""
import argparse
import csv
import json
import os
from pathlib import Path
from phase0_api import ERPNextAPI, validate_disposable_url

FIELDS = ["item_code", "item_name", "item_group", "stock_uom"]

def plan(api, path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("主数据列不符合模板")
        rows = list(reader)
    if not rows:
        raise ValueError("主数据文件为空")
    seen, actions = set(), []
    for index, row in enumerate(rows, 2):
        if None in row or any(not row.get(field) for field in FIELDS):
            raise ValueError(f"第 {index} 行缺字段或列数异常")
        code = row["item_code"]
        if not code.startswith("M1-DEMO-") or code in seen:
            raise ValueError(f"第 {index} 行不是合成编码或存在重复")
        seen.add(code)
        for doctype, field in [("Item Group","item_group"),("UOM","stock_uom")]:
            if not api.get_doc(doctype, row[field]):
                raise ValueError(f"第 {index} 行关联资料不存在")
        expected = dict(row, is_stock_item=1)
        current = api.get_doc("Item", code)
        if current and any(current.get(field) != value for field, value in expected.items()):
            raise ValueError(f"第 {index} 行目标已有冲突，需核对映射")
        actions.append((code, expected, current is None))
    return actions

def migrate(api, path, apply=False):
    actions = plan(api, path)
    created = 0
    for code, expected, missing in actions:
        if not apply or not missing:
            continue
        # A timeout has unknown outcome. Fail and let the next preflight read
        # the stable item code before retrying, avoiding duplicate inserts.
        api.insert("Item", expected)
        current = api.get_doc("Item", code)
        if not current or any(current.get(k) != v for k,v in expected.items()):
            raise ValueError("创建后回读不一致")
        created += 1
    return dict(rows=len(actions), pending=sum(row[2] for row in actions),
                created=created, unchanged=sum(not row[2] for row in actions), applied=apply)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    url = validate_disposable_url(os.environ.get("PHASE0_BASE_URL","http://localhost:18081"))
    if url != "http://localhost:18081":
        raise ValueError("本演练限定独立站点 localhost:18081")
    api = ERPNextAPI(url)
    api.login("Administrator", os.environ.get("PHASE0_PASSWORD","admin"))
    if not api.get_doc("Company","R1合成发布验证公司"):
        raise ValueError("缺少隔离合成公司")
    print(json.dumps(migrate(api,args.csv,args.apply),ensure_ascii=False))

if __name__ == "__main__":
    main()
