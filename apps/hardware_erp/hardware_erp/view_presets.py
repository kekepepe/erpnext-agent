"""Data-driven job-view presets (DEC-020): one configuration drives frontend and backend."""

from __future__ import annotations

import json
from datetime import datetime, timezone

PRESET_TABLE = "hardware_erp_view_preset"

ALL_HEADER_FIELDS = ("companyId", "partnerId", "postingDate")
ALL_LINE_FIELDS = ("productId", "warehouseId", "quantity", "spec", "uom")
ALL_FIELDS = ALL_HEADER_FIELDS + ALL_LINE_FIELDS
EDITABLE_CANDIDATES = ("companyId", "partnerId", "postingDate", "productId", "warehouseId", "quantity")
ALL_ACTIONS = ("saveDraft", "addRow", "removeRow", "newDraft")
ALLOWED_KINDS = ("purchase_receipt", "sales_delivery")

# Default R1 presets seeded idempotently on install/migrate.
# Administrators can adjust or add roles via data without code changes.
DEFAULT_PRESETS = [
    {
        "role": "R1库存经办",
        "kind": "purchase_receipt",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": list(EDITABLE_CANDIDATES),
        "requiredFields": ["companyId", "partnerId", "postingDate", "productId", "warehouseId", "quantity"],
        "actions": list(ALL_ACTIONS),
        "lockReasons": {},
    },
    {
        "role": "R1库存经办",
        "kind": "sales_delivery",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": list(EDITABLE_CANDIDATES),
        "requiredFields": ["companyId", "partnerId", "postingDate", "productId", "warehouseId", "quantity"],
        "actions": list(ALL_ACTIONS),
        "lockReasons": {},
    },
    {
        "role": "R1库存复核",
        "kind": "purchase_receipt",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1库存复核）仅可复核查看采购入库草稿，不可录入或修改。",
        },
    },
    {
        "role": "R1库存复核",
        "kind": "sales_delivery",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1库存复核）仅可复核查看销售出库草稿，不可录入或修改。",
        },
    },
    {
        "role": "R1采购经理",
        "kind": "purchase_receipt",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1采购经理）仅可查看采购入库草稿，不可修改录单内容。",
        },
    },
    {
        "role": "R1销售经理",
        "kind": "sales_delivery",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1销售经理）仅可查看销售出库草稿，不可修改录单内容。",
        },
    },
    {
        "role": "R1财务经办",
        "kind": "purchase_receipt",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1财务经办）仅可核对采购入库草稿，不可修改库存单据。",
        },
    },
    {
        "role": "R1财务经办",
        "kind": "sales_delivery",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1财务经办）仅可核对销售出库草稿，不可修改库存单据。",
        },
    },
    {
        "role": "R1财务复核",
        "kind": "purchase_receipt",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1财务复核）仅可复核采购入库草稿，不可修改录单内容。",
        },
    },
    {
        "role": "R1财务复核",
        "kind": "sales_delivery",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1财务复核）仅可复核销售出库草稿，不可修改录单内容。",
        },
    },
    {
        "role": "R1业务负责人",
        "kind": "purchase_receipt",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1业务负责人）仅可审批查看，不可直接修改草稿内容。",
        },
    },
    {
        "role": "R1业务负责人",
        "kind": "sales_delivery",
        "visibleFields": list(ALL_FIELDS),
        "editableFields": [],
        "requiredFields": [],
        "actions": [],
        "lockReasons": {
            "saveDraft": "此岗位（R1业务负责人）仅可审批查看，不可直接修改草稿内容。",
        },
    },
]


def validate_preset_config(payload: dict) -> dict:
    """Validate and normalize a single role x kind preset payload. Pure function."""
    if not isinstance(payload, dict):
        raise ValueError("岗位视图预设应为 JSON 对象。")

    role = payload.get("role")
    if not isinstance(role, str) or not role.strip() or len(role.strip()) > 140:
        raise ValueError("请提供有效的岗位角色名称。")
    role = role.strip()

    kind = payload.get("kind")
    if kind not in ALLOWED_KINDS:
        raise ValueError("单据类型仅支持 purchase_receipt 或 sales_delivery。")

    def clean_list(key: str, allowed: tuple[str, ...]) -> list[str]:
        val = payload.get(key)
        if not isinstance(val, list) or any(not isinstance(item, str) or item not in allowed for item in val):
            raise ValueError(f"{key} 包含不支持的配置项。")
        return [item for item in allowed if item in val]

    visible = clean_list("visibleFields", ALL_FIELDS)
    editable = clean_list("editableFields", EDITABLE_CANDIDATES)
    required = clean_list("requiredFields", EDITABLE_CANDIDATES)
    actions = clean_list("actions", ALL_ACTIONS)

    # Editable fields must be visible.
    editable = [f for f in editable if f in visible]

    raw_reasons = payload.get("lockReasons") or {}
    if not isinstance(raw_reasons, dict):
        raise ValueError("lockReasons 应为键值对象。")
    valid_reason_keys = set(ALL_FIELDS) | set(ALL_ACTIONS)
    lock_reasons: dict[str, str] = {}
    for k, v in raw_reasons.items():
        if not isinstance(k, str) or k not in valid_reason_keys:
            raise ValueError(f"lockReasons 包含无效键：{k}")
        if not isinstance(v, str) or len(v) > 200:
            raise ValueError(f"lockReasons.{k} 应为 200 字以内的文本。")
        if v.strip():
            lock_reasons[k] = v.strip()

    return {
        "role": role,
        "kind": kind,
        "visibleFields": visible,
        "editableFields": editable,
        "requiredFields": required,
        "actions": actions,
        "lockReasons": lock_reasons,
    }


def resolve_effective_preset(presets: list[dict], user_roles: set[str], can_save_native: bool) -> dict:
    """Merge matched role presets into one effective viewPreset for frontend & backend.

    Rules:
    - If one or more presets match the user's roles, union their visibleFields,
      editableFields, and actions (least-restrictive among granted roles).
    - requiredFields are intersected across editable-capable presets or unioned if single.
    - lockReasons are kept for any field/action that remains hidden or non-editable/disallowed.
    - If no preset matches the user's roles (e.g. Administrator or custom role),
      fall back to native capabilities (all fields visible; editable iff can_save_native).
    - Effective saveDraft is always bounded by can_save_native (native permissions remain authoritative).
    """
    matched = [p for p in presets if p.get("role") in user_roles]
    if not matched:
        editable = list(EDITABLE_CANDIDATES) if can_save_native else []
        actions = list(ALL_ACTIONS) if can_save_native else []
        reasons = {} if can_save_native else {"saveDraft": "当前身份仅可查看，无权保存草稿。"}
        return {
            "matchedRoles": [],
            "visibleFields": list(ALL_FIELDS),
            "editableFields": editable,
            "requiredFields": list(EDITABLE_CANDIDATES) if can_save_native else [],
            "actions": actions,
            "lockReasons": reasons,
        }

    visible_set: set[str] = set()
    editable_set: set[str] = set()
    required_set: set[str] = set()
    action_set: set[str] = set()
    collected_reasons: dict[str, str] = {}

    for preset in matched:
        visible_set.update(preset.get("visibleFields") or [])
        editable_set.update(preset.get("editableFields") or [])
        required_set.update(preset.get("requiredFields") or [])
        action_set.update(preset.get("actions") or [])
        for k, msg in (preset.get("lockReasons") or {}).items():
            if k not in collected_reasons and msg:
                collected_reasons[k] = msg

    # Enforce native authority: never grant saveDraft if native permissions deny it.
    if not can_save_native:
        action_set.discard("saveDraft")

    # Editable must be a subset of visible.
    editable_set &= visible_set

    visible = [f for f in ALL_FIELDS if f in visible_set]
    editable = [f for f in EDITABLE_CANDIDATES if f in editable_set]
    required = [f for f in EDITABLE_CANDIDATES if f in required_set and f in editable_set]
    actions = [a for a in ALL_ACTIONS if a in action_set]

    # Only keep lockReasons for items that are actually restricted.
    lock_reasons: dict[str, str] = {}
    for field in ALL_FIELDS:
        if field not in visible_set:
            lock_reasons[field] = collected_reasons.get(field, "当前岗位无权查看此字段。")
        elif field in EDITABLE_CANDIDATES and field not in editable_set:
            lock_reasons[field] = collected_reasons.get(field, "当前岗位不可编辑此字段。")
    for action in ALL_ACTIONS:
        if action not in action_set:
            if action in collected_reasons:
                lock_reasons[action] = collected_reasons[action]
            elif action == "saveDraft":
                lock_reasons[action] = "当前岗位无权保存草稿。"

    return {
        "matchedRoles": sorted({p["role"] for p in matched}),
        "visibleFields": visible,
        "editableFields": editable,
        "requiredFields": required,
        "actions": actions,
        "lockReasons": lock_reasons,
    }


def check_write_against_preset(preset: dict, payload: dict, existing_draft: dict | None = None) -> tuple[str, str] | None:
    """Return (code, message) if the write violates the effective job-view preset, else None."""
    actions = set(preset.get("actions") or [])
    lock_reasons = preset.get("lockReasons") or {}
    if "saveDraft" not in actions:
        return ("PRESET_ACTION_DENIED", lock_reasons.get("saveDraft") or "当前岗位无权保存草稿。")

    editable = set(preset.get("editableFields") or [])

    if existing_draft is not None:
        # On update, reject mutations to any header field not in editableFields.
        for field in ALL_HEADER_FIELDS:
            if field not in editable and payload.get(field) != existing_draft.get(field):
                return ("PRESET_FIELD_LOCKED", lock_reasons.get(field) or f"当前岗位不可修改字段 {field}。")

        # On update, if any line field is locked, reject changes to that field across existing rows.
        old_lines = existing_draft.get("lines") or []
        new_lines = payload.get("lines") or []
        if len(new_lines) > len(old_lines) and "addRow" not in actions:
            return ("PRESET_ACTION_DENIED", lock_reasons.get("addRow") or "当前岗位不可新增商品行。")
        if len(new_lines) < len(old_lines) and "removeRow" not in actions:
            return ("PRESET_ACTION_DENIED", lock_reasons.get("removeRow") or "当前岗位不可删除商品行。")

        for idx, (old_line, new_line) in enumerate(zip(old_lines, new_lines)):
            for field in ("productId", "warehouseId", "quantity"):
                if field not in editable and new_line.get(field) != old_line.get(field):
                    return ("PRESET_FIELD_LOCKED", lock_reasons.get(field) or f"当前岗位不可修改第 {idx + 1} 行的 {field}。")

    return None


def filter_draft_by_preset(draft: dict, preset: dict) -> dict:
    """Strip hidden fields from a serialized draft response so API cannot leak them."""
    visible = set(preset.get("visibleFields") or ALL_FIELDS)
    filtered = {
        "id": draft["id"],
        "kind": draft["kind"],
        "revision": draft["revision"],
        "status": draft["status"],
    }
    for field in ALL_HEADER_FIELDS:
        if field in visible:
            filtered[field] = draft.get(field)

    lines = []
    for line in draft.get("lines") or []:
        row = {}
        for field in ("productId", "warehouseId", "quantity"):
            if field in visible:
                row[field] = line.get(field)
        if line.get("sourceOrderId"):
            row["sourceOrderId"] = line["sourceOrderId"]
        if line.get("sourceOrderItemId"):
            row["sourceOrderItemId"] = line["sourceOrderItemId"]
        lines.append(row)
    filtered["lines"] = lines
    return filtered


def ensure_preset_table() -> None:
    import frappe

    frappe.db.sql_ddl(
        f"""
        CREATE TABLE IF NOT EXISTS `{PRESET_TABLE}` (
            `role` VARCHAR(140) NOT NULL,
            `kind` VARCHAR(32) NOT NULL,
            `config_json` LONGTEXT NOT NULL,
            `updated_by` VARCHAR(140) NOT NULL,
            `updated_at` DATETIME(6) NOT NULL,
            PRIMARY KEY (`role`, `kind`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def seed_default_presets() -> None:
    import frappe

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for preset in DEFAULT_PRESETS:
        normalized = validate_preset_config(preset)
        frappe.db.sql(
            f"""
            INSERT IGNORE INTO `{PRESET_TABLE}` (`role`, `kind`, `config_json`, `updated_by`, `updated_at`)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                normalized["role"],
                normalized["kind"],
                json.dumps(normalized, ensure_ascii=False),
                "Administrator",
                now,
            ),
        )


def list_presets(kind: str | None = None) -> list[dict]:
    import frappe

    if kind:
        rows = frappe.db.sql(
            f"SELECT `config_json` FROM `{PRESET_TABLE}` WHERE `kind` = %s ORDER BY `role` ASC",
            (kind,),
            as_dict=True,
        )
    else:
        rows = frappe.db.sql(
            f"SELECT `config_json` FROM `{PRESET_TABLE}` ORDER BY `kind` ASC, `role` ASC",
            as_dict=True,
        )
    return [json.loads(row["config_json"]) for row in rows]


def upsert_preset(payload: dict, operator: str) -> dict:
    import frappe

    normalized = validate_preset_config(payload)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql(
        f"""
        INSERT INTO `{PRESET_TABLE}` (`role`, `kind`, `config_json`, `updated_by`, `updated_at`)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `config_json` = VALUES(`config_json`),
            `updated_by` = VALUES(`updated_by`),
            `updated_at` = VALUES(`updated_at`)
        """,
        (
            normalized["role"],
            normalized["kind"],
            json.dumps(normalized, ensure_ascii=False),
            operator,
            now,
        ),
    )
    return normalized
