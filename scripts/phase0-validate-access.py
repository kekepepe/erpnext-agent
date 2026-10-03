#!/usr/bin/env python3
"""Validate Phase 0 language, role permissions, workflow, and audit behaviour."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from phase0_api import ERPNextAPI


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "phase0" / "access-validation.json"
MARKERS = {
    "Purchase Order": "P0.6 Purchase Approval",
    "Sales Order": "P0.6 Sales Approval",
    "Payment Entry": "P0.6-PAYMENT-APPROVAL",
}


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("site_language") != "zh":
        raise ValueError("P0.6 site language must be Simplified Chinese code zh")
    return config


def login(base_url: str, email: str, password: str) -> ERPNextAPI:
    api = ERPNextAPI(base_url)
    api.login(email, password)
    logged_in = api.call("frappe.auth.get_logged_user", {})
    if logged_in != email:
        raise RuntimeError(f"Unexpected logged-in user: {logged_in}")
    return api


def resolved_session_language(api: ERPNextAPI) -> str:
    desk_html = api.get_text("/app")
    match = re.search(r'<html[^>]+lang="([^"]+)"', desk_html)
    if not match:
        raise RuntimeError("ERPNext Desk HTML did not expose a resolved language")
    return match.group(1)


def ensure_language(admin: ERPNextAPI, config: dict[str, Any]) -> None:
    settings = admin.get_doc("System Settings", "System Settings")
    if not settings:
        raise RuntimeError("System Settings was not found")
    if settings.get("language") != config["site_language"]:
        settings = admin.update(
            "System Settings",
            "System Settings",
            {"language": config["site_language"]},
        )
        print("UPDATED System Settings language: zh")
    else:
        print("EXISTS  System Settings language: zh")
    if settings.get("language") != "zh":
        raise RuntimeError("System Settings language did not persist as zh")


def ensure_user(
    admin: ERPNextAPI,
    user: dict[str, Any],
    password: str,
) -> dict[str, Any]:
    email = user["email"]
    payload = {
        "email": email,
        "first_name": user["first_name"],
        "enabled": 1,
        "user_type": "System User",
        "send_welcome_email": 0,
        "language": user["language"],
        "new_password": password,
        "roles": [{"role": role} for role in user["roles"]],
    }
    existing = admin.get_doc("User", email)
    if existing:
        document = admin.update("User", email, payload)
        print(f"EXISTS  User: {email}")
    else:
        document = admin.insert("User", payload)
        print(f"CREATED User: {email}")
    roles = {row["role"] for row in document.get("roles", [])}
    expected_roles = set(user["roles"])
    if document.get("language") != user["language"]:
        raise RuntimeError(f"User language mismatch for {email}")
    if not expected_roles.issubset(roles):
        raise RuntimeError(f"User roles mismatch for {email}: {roles}")
    return document


def expect_access(api: ERPNextAPI, doctype: str, allowed: bool) -> None:
    try:
        api.list_docs(doctype, ["name"], [], limit=1)
    except RuntimeError as error:
        if allowed:
            raise RuntimeError(f"Expected access to {doctype}: {error}") from error
        if "HTTP 403" not in str(error) and "PermissionError" not in str(error):
            raise
        print(f"DENIED  {doctype}")
        return
    if not allowed:
        raise RuntimeError(f"Unexpected access to restricted DocType {doctype}")
    print(f"ALLOWED {doctype}")


def ensure_workflow(admin: ERPNextAPI, workflow: dict[str, Any]) -> dict[str, Any]:
    name = workflow["workflow_name"]
    payload = {
        "workflow_name": name,
        "document_type": workflow["document_type"],
        "is_active": 1,
        "send_email_alert": 0,
        "workflow_state_field": "workflow_state",
        "states": [
            {
                "state": "Pending",
                "doc_status": "0",
                "allow_edit": workflow["creator_role"],
            },
            {
                "state": "Approved",
                "doc_status": "1",
                "allow_edit": workflow["approver_role"],
            },
            {
                "state": "Rejected",
                "doc_status": "2",
                "allow_edit": workflow["approver_role"],
            },
        ],
        "transitions": [
            {
                "state": "Pending",
                "action": "Approve",
                "next_state": "Approved",
                "allowed": workflow["approver_role"],
                "allow_self_approval": 0,
            },
            {
                "state": "Approved",
                "action": "Reject",
                "next_state": "Rejected",
                "allowed": workflow["approver_role"],
                "allow_self_approval": 0,
            },
        ],
    }
    existing = admin.get_doc("Workflow", name)
    if existing:
        document = admin.update("Workflow", name, payload)
        print(f"EXISTS  Workflow: {name}")
    else:
        document = admin.insert("Workflow", payload)
        print(f"CREATED Workflow: {name}")
    if not document.get("is_active"):
        raise RuntimeError(f"Workflow {name} is not active")
    return document


def find_marked_document(
    admin: ERPNextAPI,
    doctype: str,
    marker: str,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    fixture = config["transaction_fixtures"]
    if doctype == "Purchase Order":
        filters = [[doctype, "supplier", "=", fixture["supplier"]]]
        expected_owner = config["users"]["purchase"]["email"]
        expected_item = fixture["purchase_item"]
    elif doctype == "Sales Order":
        filters = [[doctype, "customer", "=", fixture["customer"]]]
        expected_owner = config["users"]["sales"]["email"]
        expected_item = fixture["sales_item"]
    else:
        filters = [[doctype, "party", "=", fixture["customer"]]]
        expected_owner = config["users"]["finance"]["email"]
        expected_item = None
    candidates = admin.list_docs(doctype, ["name"], filters, limit=500)
    matches = []
    for candidate in candidates:
        document = admin.get_doc(doctype, candidate["name"])
        if not document or document.get("owner") != expected_owner:
            continue
        if doctype == "Payment Entry":
            if (
                float(document.get("paid_amount", 0)) == 1
                and document.get("reference_no") == marker
            ):
                matches.append(document)
            continue
        items = document.get("items", [])
        if (
            len(items) == 1
            and items[0].get("item_code") == expected_item
            and float(items[0].get("qty", 0)) == float(fixture["quantity"])
        ):
            matches.append(document)
    if not matches:
        return None
    incomplete = [row for row in matches if int(row.get("docstatus", 0)) != 2]
    selected = incomplete[0] if incomplete else sorted(
        matches, key=lambda row: row["name"]
    )[-1]
    if len(matches) > 1:
        print(
            f"NOTICE  {doctype}: reusing {selected['name']} from "
            f"{len(matches)} matching validation documents"
        )
    return selected


def fixture_payload(doctype: str, config: dict[str, Any]) -> dict[str, Any]:
    fixture = config["transaction_fixtures"]
    today = date.today().isoformat()
    future = (date.today() + timedelta(days=7)).isoformat()
    if doctype == "Purchase Order":
        return {
            "supplier": fixture["supplier"],
            "company": fixture["company"],
            "transaction_date": today,
            "schedule_date": future,
            "supplier_order_info": MARKERS[doctype],
            "items": [
                {
                    "item_code": fixture["purchase_item"],
                    "qty": fixture["quantity"],
                    "rate": fixture["purchase_rate"],
                    "warehouse": fixture["warehouse"],
                    "schedule_date": future,
                }
            ],
        }
    if doctype == "Sales Order":
        return {
            "customer": fixture["customer"],
            "company": fixture["company"],
            "transaction_date": today,
            "delivery_date": future,
            "order_type": "Sales",
            "po_no": MARKERS[doctype],
            "items": [
                {
                    "item_code": fixture["sales_item"],
                    "qty": fixture["quantity"],
                    "rate": fixture["sales_rate"],
                    "warehouse": fixture["warehouse"],
                    "delivery_date": future,
                }
            ],
        }
    if doctype == "Payment Entry":
        return {
            "payment_type": "Receive",
            "posting_date": today,
            "company": fixture["company"],
            "party_type": "Customer",
            "party": fixture["customer"],
            "paid_from": "Debtors - PZH",
            "paid_to": "Cash - PZH",
            "paid_amount": 1,
            "received_amount": 1,
            "source_exchange_rate": 1,
            "target_exchange_rate": 1,
            "reference_no": MARKERS[doctype],
            "reference_date": today,
        }
    raise ValueError(f"Unsupported fixture DocType: {doctype}")


def expect_workflow_denial(api: ERPNextAPI, document: dict[str, Any]) -> None:
    try:
        api.call(
            "frappe.model.workflow.apply_workflow",
            {"doc": document, "action": "Approve"},
        )
    except RuntimeError as error:
        if "HTTP 403" not in str(error) and "WorkflowTransitionError" not in str(error):
            raise
        print(f"DENIED  Self approval: {document['doctype']} {document['name']}")
        return
    raise RuntimeError(f"Creator unexpectedly approved {document['doctype']}")


def exercise_workflow(
    admin: ERPNextAPI,
    creator: ERPNextAPI,
    approver: ERPNextAPI,
    doctype: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    existing = find_marked_document(admin, doctype, MARKERS[doctype], config)
    if existing:
        print(f"EXISTS  {doctype}: {existing['name']}")
        if int(existing.get("docstatus", 0)) == 2:
            return existing
        document = existing
    else:
        document = creator.insert(doctype, fixture_payload(doctype, config))
        print(f"CREATED {doctype}: {document['name']}")
    if int(document.get("docstatus", 0)) == 0 and document.get(
        "workflow_state"
    ) != "Pending":
        raise RuntimeError(f"{doctype} did not enter Pending workflow state")
    if int(document.get("docstatus", 0)) == 0:
        expect_workflow_denial(creator, document)
        approved = approver.call(
            "frappe.model.workflow.apply_workflow",
            {"doc": document, "action": "Approve"},
        )
        if int(approved.get("docstatus", 0)) != 1:
            raise RuntimeError(f"{doctype} approval did not submit the document")
        if approved.get("workflow_state") != "Approved":
            raise RuntimeError(f"{doctype} did not enter Approved workflow state")
        print(f"APPROVED {doctype}: {approved['name']}")
    else:
        approved = document
    rejected = approver.call(
        "frappe.model.workflow.apply_workflow",
        {"doc": approved, "action": "Reject"},
    )
    if int(rejected.get("docstatus", 0)) != 2:
        raise RuntimeError(f"{doctype} rejection did not cancel the document")
    if rejected.get("workflow_state") != "Rejected":
        raise RuntimeError(f"{doctype} did not enter Rejected workflow state")
    print(f"CANCELLED {doctype}: {rejected['name']}")
    return rejected


def validate_audit(
    admin: ERPNextAPI,
    documents: list[dict[str, Any]],
    creator_emails: set[str],
    approver_email: str,
) -> dict[str, int]:
    evidence: dict[str, int] = {}
    for document in documents:
        current = admin.get_doc(document["doctype"], document["name"])
        if not current:
            raise RuntimeError(f"Missing workflow document {document['name']}")
        if current.get("owner") not in creator_emails:
            raise RuntimeError(f"Unexpected owner for {document['name']}")
        if current.get("modified_by") != approver_email:
            raise RuntimeError(f"Unexpected modifier for {document['name']}")
        versions = admin.list_docs(
            "Version",
            ["name", "owner", "modified_by", "ref_doctype", "docname"],
            [
                ["Version", "ref_doctype", "=", document["doctype"]],
                ["Version", "docname", "=", document["name"]],
            ],
            limit=100,
        )
        if not versions:
            raise RuntimeError(f"No Version audit history for {document['name']}")
        evidence[document["name"]] = len(versions)
    return evidence


def validate(
    base_url: str,
    admin: ERPNextAPI,
    config: dict[str, Any],
    role_password: str,
) -> None:
    ensure_language(admin, config)
    users = {
        name: ensure_user(admin, user, role_password)
        for name, user in config["users"].items()
    }
    sessions = {
        name: login(base_url, user["email"], role_password)
        for name, user in config["users"].items()
    }
    resolved_languages = {
        name: resolved_session_language(session)
        for name, session in sessions.items()
    }
    for name, user in config["users"].items():
        if resolved_languages[name] != user["language"]:
            raise RuntimeError(
                f"Resolved session language mismatch for {user['email']}: "
                f"{resolved_languages[name]}"
            )
    for name, checks in config["permission_checks"].items():
        for doctype in checks["allowed"]:
            expect_access(sessions[name], doctype, True)
        for doctype in checks["denied"]:
            expect_access(sessions[name], doctype, False)

    workflows = [ensure_workflow(admin, row) for row in config["workflows"]]
    creator_by_doctype = {
        "Purchase Order": sessions["purchase"],
        "Sales Order": sessions["sales"],
        "Payment Entry": sessions["finance"],
    }
    documents = [
        exercise_workflow(
            admin,
            creator_by_doctype[workflow["document_type"]],
            sessions["approver"],
            workflow["document_type"],
            config,
        )
        for workflow in config["workflows"]
    ]
    audit = validate_audit(
        admin,
        documents,
        {user["email"] for name, user in config["users"].items() if name != "approver"},
        config["users"]["approver"]["email"],
    )
    evidence = {
        "site_language": "zh",
        "user_languages": {
            name: user["language"] for name, user in users.items()
        },
        "resolved_session_languages": resolved_languages,
        "workflows": [workflow["name"] for workflow in workflows],
        "workflow_documents": {
            document["doctype"]: {
                "name": document["name"],
                "docstatus": document["docstatus"],
                "workflow_state": document.get("workflow_state"),
                "owner": document.get("owner"),
                "modified_by": document.get("modified_by"),
            }
            for document in documents
        },
        "version_counts": audit,
    }
    print("EVIDENCE " + json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    print("OK: Phase 0 language, permissions, approval, and audit validation passed")


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
    parser.add_argument(
        "--role-password",
        default=os.environ.get("PHASE0_ROLE_PASSWORD", "p0-local-only"),
    )
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.scenarios)
        admin = login(args.base_url, args.username, args.password)
        validate(args.base_url, admin, config, args.role_password)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
