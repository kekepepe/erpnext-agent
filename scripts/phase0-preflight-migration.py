"""Check an approved opening snapshot and its ERP mappings, with optional native readback."""
import argparse
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from phase0_api import ERPNextAPI, validate_disposable_url

spec = importlib.util.spec_from_file_location("opening", Path(__file__).with_name("phase0-reconcile-opening.py"))
opening = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opening)

TYPES = {"stock": "Item", "ar": "Customer", "ap": "Supplier", "gl": "Account",
         "warehouses": "Warehouse", "units": "UOM"}


def prepare(config, source):
    date.fromisoformat(config["cutoff"])
    if config["currency"] != "CNY" or hashlib.sha256(source.read_bytes()).hexdigest() != config["source_sha256"]:
        raise ValueError("币种或来源文件校验值不符")
    for group in TYPES:
        targets = list(config[group].values())
        if any(not isinstance(value, str) or not value.strip() for value in targets):
            raise ValueError("目标映射为空")
        if len(targets) != len(set(targets)):
            raise ValueError("多个来源指向相同目标，须先审阅合并")
    if len(config["warehouses"]) != 2 or not config["company"].strip():
        raise ValueError("首版公司或两仓映射缺失")
    if set(config["controls"]) != {"stock", "ar", "ap"} or len(set(config["controls"].values())) != 3:
        raise ValueError("需要独立的库存、应收、应付控制科目")
    balances = opening.snapshot(source)
    mapped = {}
    for (kind, company, key, warehouse, unit), values in balances.items():
        if company != config["source_company"]:
            raise ValueError("来源公司不匹配")
        try:
            mapped_key = (kind, config["company"], config[kind][key],
                          config["warehouses"][warehouse] if warehouse else "",
                          config["units"][unit] if unit else "")
        except KeyError:
            raise ValueError("来源行缺少业务键、仓库或单位映射") from None
        mapped[mapped_key] = values
    for kind, account in config["controls"].items():
        details = sum(v["amount"] for k, v in balances.items() if k[0] == kind)
        ledger = balances.get(("gl", config["source_company"], account, "", ""))
        if ledger is None:
            raise ValueError("试算缺少控制科目行（零余额须显式列示）")
        net = ledger["debit"] - ledger["credit"]
        if details != (-net if kind == "ap" else net):
            raise ValueError("明细与期初控制科目不一致")
    return mapped


def check_native(api, config, mapped):
    company = api.get_doc("Company", config["company"])
    if not company or company["default_currency"] != config["currency"]:
        raise ValueError("ERP 公司或本位币不匹配")
    stock_units = {}
    account_types = {}
    for group, doctype in TYPES.items():
        for target in config[group].values():
            doc = api.get_doc(doctype, target)
            if not doc or doc.get("disabled"):
                raise ValueError("目标缺失或停用：" + doctype)
            if group in {"gl", "warehouses"} and (doc["company"] != config["company"] or doc["is_group"]):
                raise ValueError("目标公司不符或引用了分组节点：" + doctype)
            if group == "stock":
                if not doc["is_stock_item"]:
                    raise ValueError("期初库存引用非库存商品")
                stock_units[target] = doc["stock_uom"]
            if group == "gl":
                account_types[target] = doc.get("account_type")
    for kind, expected in {"stock":"Stock", "ar":"Receivable", "ap":"Payable"}.items():
        if account_types[config["gl"][config["controls"][kind]]] != expected:
            raise ValueError("原生控制科目类型不匹配")
    if any(stock_units[key] != unit for kind, _, key, _, unit in mapped if kind == "stock"):
        raise ValueError("来源库存单位与目标商品不一致")


def verify_target(config, mapped, target):
    manifest = json.loads((target.parent / "manifest.json").read_text(encoding="utf-8"))
    if target.name != "target.csv" or any(manifest.get(k) != config[k] for k in ("cutoff", "company", "currency")) or manifest.get("time_zone") != "Asia/Shanghai":
        raise ValueError("目标快照截止日、公司、币种或时区不符")
    for name in ("target.csv", "reports.json"):
        if hashlib.sha256((target.parent / name).read_bytes()).hexdigest() != manifest["sha256"][name]:
            raise ValueError("目标快照或报表摘要不符")
    if opening.snapshot(target) != mapped:
        raise ValueError("目标快照逐项对账存在差异")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mapping", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--target", type=Path, help="同一截止日的ERP标准化快照")
    parser.add_argument("--check-native", action="store_true", help="通过原生API核对演练站点的映射")
    args = parser.parse_args()
    config = json.loads(args.mapping.read_text(encoding="utf-8"))
    mapped = prepare(config, args.source)
    if args.target:
        verify_target(config, mapped, args.target)
    if args.check_native:
        api = ERPNextAPI(validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080")))
        api.login(os.environ.get("PHASE0_USERNAME","Administrator"), os.environ.get("PHASE0_PASSWORD","admin"))
        check_native(api, config, mapped)
    print(json.dumps({"rows":len(mapped),"control_accounts":3,"cutoff":config["cutoff"],
                      "native_readback":args.check_native,"target_compared":bool(args.target),"result":"PASS"}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(str(error))
