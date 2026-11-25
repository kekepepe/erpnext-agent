"""Same-origin Business API v1 adapter for W6 Purchase Receipt and Delivery Note drafts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import frappe

from hardware_erp.approval import MAKERS, P0_COMPANY
from hardware_erp.business_api_setup import AUDIT_TABLE, IDEMPOTENCY_TABLE


KINDS = {
    "purchase_receipt": {
        "doctype": "Purchase Receipt",
        "partner_doctype": "Supplier",
        "partner_field": "supplier",
        "partner_name_field": "supplier_name",
        "item_flag": "is_purchase_item",
    },
    "sales_delivery": {
        "doctype": "Delivery Note",
        "partner_doctype": "Customer",
        "partner_field": "customer",
        "partner_name_field": "customer_name",
        "item_flag": "is_sales_item",
    },
}
DOCTYPE_TO_KIND = {spec["doctype"]: kind for kind, spec in KINDS.items()}
QUANTITY_RE = re.compile(r"^(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,6})?$")
IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
MAX_BODY_BYTES = 65536


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, issues: list[dict] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.error = {"code": code, "message": message, "issues": issues or []}


def canonical_digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def format_quantity(value) -> str:
    try:
        dec = Decimal(str(value)).normalize()
    except (InvalidOperation, TypeError, ValueError):
        return "0"
    if dec == dec.to_integral():
        return str(dec.quantize(Decimal("1")))
    text = format(dec, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def parse_route(route: str | None) -> tuple[str, str | None] | None:
    cleaned = (route or "").strip("/")
    if cleaned == "entry-options":
        return ("entry_options", None)
    if cleaned == "drafts":
        return ("drafts", None)
    if cleaned.startswith("drafts/"):
        draft_id = cleaned[len("drafts/"):]
        if draft_id and "/" not in draft_id and len(draft_id) <= 140:
            return ("draft", draft_id)
    return None


def validate_payload_shape(body, updating: bool) -> None:
    if not isinstance(body, dict):
        raise ApiError(400, "INVALID_REQUEST", "草稿应为 JSON 对象。")
    kind = body.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ApiError(400, "INVALID_KIND", "请选择采购入库或销售出库。")

    issues: list[dict] = []

    def issue(path: str, message: str) -> None:
        issues.append({"path": path, "message": message})

    allowed_fields = {"kind", "companyId", "partnerId", "postingDate", "lines"}
    if updating:
        allowed_fields.add("revision")
    for extra in sorted(body.keys() - allowed_fields):
        issue(extra, "此字段不在录单范围内。")

    if not isinstance(body.get("companyId"), str) or not body.get("companyId"):
        issue("companyId", "请选择有效选项。")
    if not isinstance(body.get("partnerId"), str) or not body.get("partnerId"):
        issue("partnerId", "请选择有效选项。")

    posting_date = body.get("postingDate")
    try:
        if not isinstance(posting_date, str) or date.fromisoformat(posting_date).isoformat() != posting_date:
            raise ValueError
    except ValueError:
        issue("postingDate", "请输入有效的单据日期。")

    revision = body.get("revision")
    if updating and (type(revision) is not int or revision < 1):
        issue("revision", "缺少有效的草稿版本。")

    lines = body.get("lines")
    if not isinstance(lines, list) or not 1 <= len(lines) <= 100:
        issue("lines", "请输入 1 至 100 行商品。")
    else:
        for index, line in enumerate(lines):
            path = f"lines.{index}"
            if not isinstance(line, dict):
                issue(path, "商品行格式无效。")
                continue
            for extra in sorted(line.keys() - {"productId", "warehouseId", "quantity"}):
                issue(f"{path}.{extra}", "此字段不在录单范围内。")
            if not isinstance(line.get("productId"), str) or not line.get("productId"):
                issue(f"{path}.productId", "请选择有效选项。")
            if not isinstance(line.get("warehouseId"), str) or not line.get("warehouseId"):
                issue(f"{path}.warehouseId", "请选择有效选项。")
            quantity = line.get("quantity")
            if (
                not isinstance(quantity, str)
                or not QUANTITY_RE.fullmatch(quantity)
                or not quantity.replace(".", "").strip("0")
            ):
                issue(f"{path}.quantity", "数量须大于零，整数最多九位，小数最多六位。")

    if issues:
        raise ApiError(422, "VALIDATION_ERROR", "请修正录单内容。", issues)


def serialize_draft(doc, kind: str) -> dict:
    spec = KINDS[kind]
    return {
        "id": doc.name,
        "kind": kind,
        "companyId": doc.company,
        "partnerId": doc.get(spec["partner_field"]),
        "postingDate": str(doc.posting_date),
        "lines": [
            {
                "productId": row.item_code,
                "warehouseId": row.warehouse,
                "quantity": format_quantity(row.qty),
            }
            for row in (doc.get("items") or [])
        ],
        "revision": max(int(doc.get("custom_w6_revision") or 0), 1),
        "status": "draft",
    }


def _json_response(status: int, payload: dict):
    from werkzeug.wrappers import Response

    body = json.dumps(payload, ensure_ascii=False)
    return Response(
        body,
        status=status,
        mimetype="application/json",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _record_audit(operator: str, operation: str, doctype: str, doc_id: str, status: int, code: str, commit: bool = False) -> None:
    import frappe

    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        frappe.db.sql(
            f"""
            INSERT INTO `{AUDIT_TABLE}`
                (`operator`, `created_at`, `operation`, `doctype`, `doc_id`, `http_status`, `result_code`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (operator or "Guest", now, operation, doctype or "", doc_id or "", int(status), code[:64]),
        )
        if commit:
            frappe.db.commit()
    except Exception:
        pass


def _require_auth(is_write: bool) -> str:
    import frappe

    user = getattr(frappe.session, "user", None)
    if not user or user == "Guest":
        raise ApiError(401, "UNAUTHORIZED", "请先登录。")
    if frappe.db.get_value("User", user, "user_type") != "System User":
        raise ApiError(403, "FORBIDDEN", "仅系统用户可使用录单接口。")
    if is_write and not frappe.conf.get("ignore_csrf"):
        saved_token = getattr(getattr(frappe.session, "data", None), "csrf_token", None)
        sent_token = frappe.get_request_header("X-Frappe-CSRF-Token")
        if saved_token and sent_token != saved_token:
            raise ApiError(403, "CSRF_REQUIRED", "缺少或无效的会话安全令牌。")
    return user


def _user_restricted_values(user: str, allow_doctype: str) -> set[str] | None:
    import frappe.permissions

    user_perms = frappe.permissions.get_user_permissions(user) or {}
    entries = user_perms.get(allow_doctype) or []
    if not entries:
        return None
    return {entry["doc"] for entry in entries if entry.get("doc")}


def _can_create_draft(doctype: str, companies: list[dict]) -> bool:
    import frappe

    if not frappe.has_permission(doctype, "create"):
        return False
    roles = set(frappe.get_roles())
    if MAKERS[doctype] in roles:
        return True
    return any(company["id"] == P0_COMPANY for company in companies)


def _handle_entry_options(kind: str | None) -> tuple[int, dict, str, str]:
    import frappe

    if not isinstance(kind, str) or kind not in KINDS:
        raise ApiError(400, "INVALID_KIND", "请选择采购入库或销售出库。")
    spec = KINDS[kind]
    doctype = spec["doctype"]
    if not frappe.has_permission(doctype, "read"):
        raise ApiError(403, "FORBIDDEN", "当前身份无权访问此类单据。")

    raw_companies = frappe.get_list(
        "Company",
        fields=["name", "company_name"],
        order_by="name asc",
        limit_page_length=100,
    )
    companies = [{"id": row["name"], "label": row.get("company_name") or row["name"]} for row in raw_companies]
    company_ids = {row["id"] for row in companies}

    raw_partners = frappe.get_list(
        spec["partner_doctype"],
        filters={"disabled": 0},
        fields=["name", spec["partner_name_field"]],
        order_by="name asc",
        limit_page_length=500,
    )
    partners = [
        {"id": row["name"], "label": row.get(spec["partner_name_field"]) or row["name"]}
        for row in raw_partners
    ]

    raw_warehouses = frappe.get_list(
        "Warehouse",
        filters={"is_group": 0, "disabled": 0},
        fields=["name", "warehouse_name", "company"],
        order_by="name asc",
        limit_page_length=500,
    )
    warehouses = [
        {"id": row["name"], "label": row.get("warehouse_name") or row["name"]}
        for row in raw_warehouses
        if not company_ids or row.get("company") in company_ids
    ]

    raw_products = frappe.get_list(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1, spec["item_flag"]: 1},
        fields=[
            "name",
            "item_name",
            "custom_trade_name_en",
            "custom_trade_specification",
            "custom_trade_model",
            "stock_uom",
        ],
        order_by="name asc",
        limit_page_length=5000,
    )
    products = [
        {
            "id": row["name"],
            "label": row.get("item_name") or row["name"],
            "englishName": row.get("custom_trade_name_en") or "",
            "specification": row.get("custom_trade_specification") or "",
            "model": row.get("custom_trade_model") or "",
            "uom": row.get("stock_uom") or "",
        }
        for row in raw_products
    ]

    data = {
        "companies": companies,
        "partners": partners,
        "warehouses": warehouses,
        "products": products,
        "defaults": {
            "companyId": companies[0]["id"] if companies else "",
            "postingDate": date.today().isoformat(),
        },
        "capabilities": {
            "saveDraft": _can_create_draft(doctype, companies),
        },
    }
    return 200, {"data": data}, doctype, ""


def _locate_draft(draft_id: str, for_update: bool = False):
    import frappe

    for kind, spec in KINDS.items():
        doctype = spec["doctype"]
        if frappe.db.exists(doctype, draft_id):
            doc = frappe.get_doc(doctype, draft_id, for_update=for_update)
            if not doc.has_permission("read"):
                raise ApiError(404, "DRAFT_NOT_FOUND", "找不到草稿或无权访问。")
            return doc, kind
    raise ApiError(404, "DRAFT_NOT_FOUND", "找不到草稿或无权访问。")


def _handle_get_draft(draft_id: str) -> tuple[int, dict, str, str]:
    doc, kind = _locate_draft(draft_id, for_update=False)
    if int(doc.docstatus) != 0 or int(doc.get("is_return") or 0) != 0:
        raise ApiError(404, "DRAFT_NOT_FOUND", "找不到草稿或无权访问。")
    return 200, {"data": serialize_draft(doc, kind)}, doc.doctype, doc.name


def _read_json_body() -> dict:
    import frappe

    content_type = (frappe.request.mimetype or "").lower()
    if content_type != "application/json":
        raise ApiError(415, "JSON_REQUIRED", "请发送 JSON 格式的草稿。")
    raw = frappe.request.get_data() or b""
    if len(raw) > MAX_BODY_BYTES:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "单次录单内容过大。")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise ApiError(400, "INVALID_REQUEST", "草稿 JSON 格式无效。") from None
    if not isinstance(parsed, dict):
        raise ApiError(400, "INVALID_REQUEST", "草稿应为 JSON 对象。")
    return parsed


def _lookup_idempotency(operator: str, operation: str, target_id: str, key: str):
    import frappe

    rows = frappe.db.sql(
        f"""
        SELECT `request_digest`, `response_status`, `response_json`
        FROM `{IDEMPOTENCY_TABLE}`
        WHERE `operator` = %s AND `operation` = %s AND `target_id` = %s AND `idempotency_key` = %s
        LIMIT 1
        """,
        (operator, operation, target_id, key),
        as_dict=True,
    )
    return rows[0] if rows else None


def _insert_idempotency(operator: str, operation: str, target_id: str, key: str, digest: str, status: int, body: dict) -> None:
    import frappe

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql(
        f"""
        INSERT INTO `{IDEMPOTENCY_TABLE}`
            (`operator`, `operation`, `target_id`, `idempotency_key`, `request_digest`, `response_status`, `response_json`, `created_at`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (operator, operation, target_id, key, digest, int(status), json.dumps(body, ensure_ascii=False), now),
    )


def _validate_references(body: dict, spec: dict) -> None:
    import frappe

    issues: list[dict] = []

    def issue(path: str, message: str) -> None:
        issues.append({"path": path, "message": message})

    companies = {
        row["name"]
        for row in frappe.get_list("Company", filters={"name": body["companyId"]}, fields=["name"], limit_page_length=1)
    }
    if body["companyId"] not in companies:
        issue("companyId", "请选择有效选项。")

    partners = {
        row["name"]
        for row in frappe.get_list(
            spec["partner_doctype"],
            filters={"name": body["partnerId"], "disabled": 0},
            fields=["name"],
            limit_page_length=1,
        )
    }
    if body["partnerId"] not in partners:
        issue("partnerId", "请选择有效选项。")

    requested_items = list({line["productId"] for line in body["lines"]})
    valid_items = {
        row["name"]
        for row in frappe.get_list(
            "Item",
            filters={
                "name": ["in", requested_items],
                "disabled": 0,
                "is_stock_item": 1,
                spec["item_flag"]: 1,
            },
            fields=["name"],
            limit_page_length=len(requested_items) + 1,
        )
    }

    requested_warehouses = list({line["warehouseId"] for line in body["lines"]})
    valid_warehouses = {
        row["name"]
        for row in frappe.get_list(
            "Warehouse",
            filters={
                "name": ["in", requested_warehouses],
                "is_group": 0,
                "disabled": 0,
                "company": body["companyId"],
            },
            fields=["name"],
            limit_page_length=len(requested_warehouses) + 1,
        )
    }

    for index, line in enumerate(body["lines"]):
        if line["productId"] not in valid_items:
            issue(f"lines.{index}.productId", "请选择有效选项。")
        if line["warehouseId"] not in valid_warehouses:
            issue(f"lines.{index}.warehouseId", "请选择有效选项。")

    if issues:
        raise ApiError(422, "VALIDATION_ERROR", "请修正录单内容。", issues)


def _idempotency_lock_name(operator: str, operation: str, target_id: str, key: str) -> str:
    raw = f"{operator}|{operation}|{target_id}|{key}".encode("utf-8")
    return "w6_idem_" + hashlib.sha256(raw).hexdigest()[:40]


def _handle_save_draft(operator: str, draft_id: str | None) -> tuple[int, dict, str, str]:
    import frappe

    key = frappe.get_request_header("Idempotency-Key") or ""
    if not IDEMPOTENCY_KEY_RE.fullmatch(key):
        raise ApiError(400, "INVALID_IDEMPOTENCY_KEY", "缺少有效的保存标识。")

    body = _read_json_body()
    operation = "update_draft" if draft_id else "create_draft"
    target_id = draft_id or ""
    digest = canonical_digest(body)

    lock_name = _idempotency_lock_name(operator, operation, target_id, key)
    acquired = frappe.db.sql("SELECT GET_LOCK(%s, 10)", (lock_name,))[0][0]
    if acquired != 1:
        raise ApiError(409, "CONCURRENT_SAVE", "同一保存请求正在处理中，请稍后重试。")

    try:
        # Refresh InnoDB REPEATABLE READ snapshot after acquiring the advisory lock
        # so any just-committed sibling request is immediately visible.
        frappe.db.rollback()

        # Check idempotency before revision or validation to guarantee safe replay.
        existing = _lookup_idempotency(operator, operation, target_id, key)
        if existing:
            if existing["request_digest"] != digest:
                raise ApiError(409, "IDEMPOTENCY_CONFLICT", "保存标识已用于其他内容。")
            saved_body = json.loads(existing["response_json"])
            saved_data = saved_body.get("data") or {}
            saved_doctype = KINDS.get(saved_data.get("kind"), {}).get("doctype", "")
            return int(existing["response_status"]), saved_body, saved_doctype, saved_data.get("id", target_id)

        validate_payload_shape(body, updating=draft_id is not None)
        kind = body["kind"]
        spec = KINDS[kind]
        doctype = spec["doctype"]

        doc = None
        current_revision = 0
        if draft_id is None:
            if not frappe.has_permission(doctype, "create"):
                raise ApiError(403, "FORBIDDEN", "当前身份无权新建此类草稿。")
            if body["companyId"] != P0_COMPANY and MAKERS[doctype] not in set(frappe.get_roles()):
                raise ApiError(403, "FORBIDDEN", "当前身份不能创建此类业务单据。")
        else:
            doc, found_kind = _locate_draft(draft_id, for_update=True)
            if int(doc.docstatus) != 0 or int(doc.get("is_return") or 0) != 0:
                raise ApiError(409, "DRAFT_NOT_EDITABLE", "当前单据状态不可通过录单接口修改。")
            if found_kind != kind:
                raise ApiError(409, "KIND_CONFLICT", "已保存草稿的单据类型不能更改。")
            if not doc.has_permission("write"):
                raise ApiError(403, "FORBIDDEN", "当前身份无权修改此草稿。")
            current_revision = max(int(doc.get("custom_w6_revision") or 0), 1)

        # Check user-scoped Company / Warehouse restrictions without leaking existence.
        allowed_companies = _user_restricted_values(operator, "Company")
        if allowed_companies is not None and body["companyId"] not in allowed_companies:
            raise ApiError(403, "FORBIDDEN", "所选公司超出当前岗位权限范围。")

        allowed_warehouses = _user_restricted_values(operator, "Warehouse")
        if allowed_warehouses is not None:
            for line in body["lines"]:
                if line["warehouseId"] not in allowed_warehouses:
                    raise ApiError(403, "FORBIDDEN", "所选仓库超出当前岗位权限范围。")

        _validate_references(body, spec)

        if draft_id is not None and body["revision"] != current_revision:
            raise ApiError(409, "STALE_REVISION", "草稿已更新，请核对最新版本后重试。")

        new_revision = 1 if draft_id is None else current_revision + 1
        if draft_id is None:
            doc = frappe.get_doc({
                "doctype": doctype,
                "company": body["companyId"],
                spec["partner_field"]: body["partnerId"],
                "posting_date": body["postingDate"],
                "set_posting_time": 1,
                "is_return": 0,
                "custom_w6_revision": new_revision,
                "items": [
                    {
                        "item_code": line["productId"],
                        "warehouse": line["warehouseId"],
                        "qty": float(Decimal(line["quantity"])),
                    }
                    for line in body["lines"]
                ],
            })
            doc.insert()
            status = 201
        else:
            doc.company = body["companyId"]
            doc.set(spec["partner_field"], body["partnerId"])
            doc.posting_date = body["postingDate"]
            doc.set_posting_time = 1
            doc.is_return = 0
            doc.custom_w6_revision = new_revision
            doc.set("items", [])
            for line in body["lines"]:
                doc.append("items", {
                    "item_code": line["productId"],
                    "warehouse": line["warehouseId"],
                    "qty": float(Decimal(line["quantity"])),
                })
            doc.save()
            status = 200

        if int(doc.docstatus) != 0:
            raise ApiError(409, "DRAFT_NOT_EDITABLE", "录单接口仅允许保存草稿。")

        response_body = {"data": serialize_draft(doc, kind)}
        _insert_idempotency(operator, operation, target_id, key, digest, status, response_body)
        _record_audit(operator, operation, doctype, doc.name, status, "OK", commit=False)
        frappe.db.commit()
        return status, response_body, doctype, doc.name
    finally:
        try:
            frappe.db.sql("SELECT RELEASE_LOCK(%s)", (lock_name,))
        except Exception:
            pass


@frappe.whitelist(allow_guest=True, methods=["GET", "POST", "PUT"])
def dispatch(**kwargs):
    import frappe
    from hardware_erp.approval import ApprovalBoundaryError

    method = frappe.request.method.upper()
    raw_route = frappe.get_request_header("X-Business-API-Route") or frappe.form_dict.get("_route") or ""
    parsed = parse_route(raw_route)
    operation = f"{method} /{raw_route.strip('/')}"
    operator = getattr(frappe.session, "user", "Guest")
    doctype = ""
    doc_id = ""

    try:
        operator = _require_auth(is_write=method in ("POST", "PUT"))
        if parsed is None:
            raise ApiError(404, "NOT_FOUND", "找不到此功能。")
        action, draft_id = parsed

        if method == "GET" and action == "entry_options":
            operation = "entry_options"
            status, payload, doctype, doc_id = _handle_entry_options(frappe.request.args.get("kind"))
            return _json_response(status, payload)

        if method == "GET" and action == "draft" and draft_id:
            operation = "get_draft"
            status, payload, doctype, doc_id = _handle_get_draft(draft_id)
            return _json_response(status, payload)

        if method == "POST" and action == "drafts":
            operation = "create_draft"
            status, payload, doctype, doc_id = _handle_save_draft(operator, None)
            return _json_response(status, payload)

        if method == "PUT" and action == "draft" and draft_id:
            operation = "update_draft"
            doc_id = draft_id
            status, payload, doctype, doc_id = _handle_save_draft(operator, draft_id)
            return _json_response(status, payload)

        raise ApiError(404, "NOT_FOUND", "找不到此功能。")

    except ApiError as error:
        if method in ("POST", "PUT"):
            frappe.db.rollback()
            _record_audit(operator, operation, doctype, doc_id, error.status, error.code, commit=True)
        return _json_response(error.status, {"error": error.error})

    except (frappe.PermissionError, ApprovalBoundaryError) as error:
        if method in ("POST", "PUT"):
            frappe.db.rollback()
            _record_audit(operator, operation, doctype, doc_id, 403, "FORBIDDEN", commit=True)
        return _json_response(
            403,
            {"error": {"code": "FORBIDDEN", "message": str(error) or "当前身份无权执行此操作。", "issues": []}},
        )

    except frappe.ValidationError as error:
        if method in ("POST", "PUT"):
            frappe.db.rollback()
            _record_audit(operator, operation, doctype, doc_id, 422, "VALIDATION_ERROR", commit=True)
        return _json_response(
            422,
            {"error": {"code": "VALIDATION_ERROR", "message": str(error) or "单据校验未通过。", "issues": []}},
        )
