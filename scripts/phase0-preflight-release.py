#!/usr/bin/env python3
"""Fail-closed release preflight for the approved R1 approval boundary.

The default mode rejects disposable P0 discovery fixtures. C0 may explicitly
allow them while exercising the clean synthetic site. All checks use native
authenticated APIs; no database access or writes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

from phase0_api import ERPNextAPI, validate_disposable_url

ROOT = Path(__file__).resolve().parents[1]
ACCESS = json.loads((ROOT / "phase0/release-access.json").read_text())


def load(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def preflight(api: ERPNextAPI, allow_synthetic_fixtures: bool = False) -> dict:
    installed_doc = api.get_doc("Installed Applications", "Installed Applications")
    installed = [
        row.get("app_name")
        for row in (installed_doc or {}).get("installed_applications", [])
        if row.get("app_name")
    ]
    if not isinstance(installed, list) or "hardware_erp" not in installed:
        raise ValueError("hardware_erp is not installed; business writes must remain closed")
    if "erpnext" not in installed or "erpnext_zh" not in installed:
        raise ValueError("required ERPNext or approved presentation app is not installed")

    access = load("p010_access", "scripts/phase0-configure-access.py")
    result = access.configure(api, ACCESS, False)
    if result["roles"] != 9 or result["workflows"] != 9 or result["changed"]:
        raise ValueError("approval role/workflow configuration is incomplete or drifted")

    for doctype in access.TYPES:
        wanted = access.workflow_spec(doctype, ACCESS)
        current = api.get_doc("Workflow", wanted["workflow_name"])
        if not current or not current.get("is_active"):
            raise ValueError("inactive approval workflow: " + doctype)

    p0_company = api.get_doc("Company", "Phase Zero Hardware Trading Demo")
    if p0_company and not allow_synthetic_fixtures:
        raise ValueError("P0 discovery fixture exists; production preflight must reject it")

    return {
        "installed_apps": sorted(app for app in installed if app in {"frappe", "erpnext", "erpnext_zh", "hardware_erp"}),
        "roles": result["roles"],
        "workflows": result["workflows"],
        "audit_retention": result["audit_retention"],
        "p0_fixture_policy": "ALLOWED_FOR_C0" if p0_company else "ABSENT",
        "result": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-synthetic-fixtures", action="store_true")
    args = parser.parse_args()
    url = validate_disposable_url(os.environ.get("PHASE0_BASE_URL", "http://localhost:8080"))
    api = ERPNextAPI(url)
    api.login(
        os.environ.get("PHASE0_USERNAME", "Administrator"),
        os.environ.get("PHASE0_PASSWORD", "admin"),
    )
    print(json.dumps(preflight(api, args.allow_synthetic_fixtures), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
