#!/usr/bin/env python3
"""Create retail and five native CNY selling price lists on the existing local test site."""

import argparse
import json
import os
from pathlib import Path

from phase0_api import ERPNextAPI

CONFIG = Path(__file__).resolve().parents[1] / "apps/erpnext_zh/erpnext_zh/price_tiers.json"
TIERS = tuple(tier["name"] for tier in json.loads(CONFIG.read_text()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Create missing lists; default is read-only")
    args = parser.parse_args()
    api = ERPNextAPI("http://localhost:8080")
    api.login(os.environ.get("PHASE0_USERNAME", "Administrator"), os.environ.get("PHASE0_PASSWORD", "admin"))

    missing = []
    for name in TIERS:
        current = api.get_doc("Price List", name)
        if current is None:
            missing.append(name)
        elif not (current["currency"] == "CNY" and current["selling"] and current["enabled"] and not current["buying"]):
            raise SystemExit(f"配置存在冲突，请核对价目表 {name}")

    if missing and not args.apply:
        raise SystemExit("缺少价目表 " + "、".join(missing))
    for name in missing:
        api.insert("Price List", {"price_list_name": name, "currency": "CNY", "selling": 1, "buying": 0, "enabled": 1})
    print("已核对零售价及五档人民币预设售价。本次新增 " + str(len(missing)) + " 档。")


if __name__ == "__main__":
    main()
