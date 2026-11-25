"""1A Read-only pricing advisory: transparent source resolution, history window & minimum-sale check."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import frappe

SOURCE_KEYS = ("pricing_rule", "party_price", "tier_price", "history_price", "item_default")
DEFAULT_PRIORITY_ORDER = ("pricing_rule", "party_price", "tier_price", "history_price", "item_default")
DEFAULT_HISTORY_WINDOW_DAYS = 180
MAX_HISTORY_WINDOW_DAYS = 730


def format_rate(value) -> str:
    try:
        dec = Decimal(str(value)).quantize(Decimal("0.000001")).normalize()
    except (InvalidOperation, TypeError, ValueError):
        return "0.00"
    if dec == dec.to_integral():
        return f"{dec.quantize(Decimal('1'))}.00"
    text = format(dec, "f").rstrip("0")
    if "." in text and len(text.split(".")[1]) < 2:
        text += "0" * (2 - len(text.split(".")[1]))
    return text


def normalize_priority_order(priority_order) -> list[str]:
    if priority_order is None:
        return list(DEFAULT_PRIORITY_ORDER)
    if not isinstance(priority_order, list) or not priority_order:
        raise ValueError("priorityOrder 必须是非空数组。")
    seen = []
    for key in priority_order:
        if not isinstance(key, str) or key not in SOURCE_KEYS:
            raise ValueError(f"不支持的价格来源：{key}")
        if key not in seen:
            seen.append(key)
    return seen


def select_price_candidate(candidates_by_source: dict[str, dict | None], priority_order: list[str]) -> tuple[dict, list[dict]]:
    ordered: list[dict] = []
    for key in priority_order:
        cand = candidates_by_source.get(key)
        if cand is not None:
            ordered.append(cand)
    if ordered:
        return ordered[0], ordered
    return (
        {
            "source": "none",
            "sourceLabel": "无匹配价格",
            "rate": None,
            "referenceDoc": None,
        },
        [],
    )


def check_minimum_sale(rate, minimum_sale, conversion_factor=1) -> dict:
    """Compare effective stock-UOM rate against Item.custom_trade_minimum_sale (advisory warning)."""
    try:
        min_dec = Decimal(str(minimum_sale or 0))
    except (InvalidOperation, TypeError, ValueError):
        min_dec = Decimal("0")

    if min_dec <= 0:
        return {
            "belowMinimumSale": False,
            "minimumSaleRate": None,
            "stockUomRate": None,
            "warning": None,
        }

    if rate is None:
        return {
            "belowMinimumSale": False,
            "minimumSaleRate": format_rate(min_dec),
            "stockUomRate": None,
            "warning": None,
        }

    try:
        rate_dec = Decimal(str(rate))
        cf_dec = Decimal(str(conversion_factor or 1))
        if cf_dec <= 0:
            cf_dec = Decimal("1")
        stock_rate = rate_dec / cf_dec
    except (InvalidOperation, TypeError, ValueError):
        return {
            "belowMinimumSale": False,
            "minimumSaleRate": format_rate(min_dec),
            "stockUomRate": None,
            "warning": None,
        }

    below = stock_rate < min_dec
    warning = (
        f"建议价（按库存单位折算 {format_rate(stock_rate)}）低于最低售价参考 {format_rate(min_dec)}，请核对或经授权改价。"
        if below
        else None
    )
    return {
        "belowMinimumSale": below,
        "minimumSaleRate": format_rate(min_dec),
        "stockUomRate": format_rate(stock_rate),
        "warning": warning,
    }


def _find_item_price(item_code: str, price_list: str | None, uom: str, posting_date: str, is_buying: bool, party_field: str, party: str | None):
    if not price_list or not frappe.has_permission("Item Price", "read"):
        return None
    filters = [
        ["item_code", "=", item_code],
        ["price_list", "=", price_list],
        ["buying" if is_buying else "selling", "=", 1],
    ]
    if party:
        filters.append([party_field, "=", party])
    else:
        filters.append([party_field, "is", "not set"])

    rows = frappe.get_list(
        "Item Price",
        filters=filters,
        fields=["name", "price_list_rate", "uom", "valid_from", "valid_upto", "modified"],
        order_by="modified desc",
        limit_page_length=50,
    )
    valid_rows = []
    for row in rows:
        vf = str(row.get("valid_from") or "")
        vu = str(row.get("valid_upto") or "")
        if vf and vf > posting_date:
            continue
        if vu and vu < posting_date:
            continue
        valid_rows.append(row)

    # Prefer exact UOM match first, then UOM-agnostic price
    for row in valid_rows:
        if row.get("uom") == uom:
            return row
    for row in valid_rows:
        if not row.get("uom"):
            return row
    return None


def _find_history_price(is_buying: bool, company: str, party: str | None, item_code: str, uom: str, posting_date: str, window_days: int):
    if not party:
        return None
    target_date = date.fromisoformat(posting_date)
    start_date = (target_date - timedelta(days=window_days)).isoformat()
    candidates_doctypes = (
        (("Purchase Invoice", "posting_date", True), ("Purchase Order", "transaction_date", False))
        if is_buying
        else (("Sales Invoice", "posting_date", True), ("Sales Order", "transaction_date", False))
    )
    party_field = "supplier" if is_buying else "customer"

    best = None
    for doctype, date_field, has_return_flag in candidates_doctypes:
        if not frappe.has_permission(doctype, "read"):
            continue
        filters = [
            ["company", "=", company],
            [party_field, "=", party],
            ["docstatus", "=", 1],
            [date_field, ">=", start_date],
            [date_field, "<=", posting_date],
        ]
        if has_return_flag:
            filters.append(["is_return", "=", 0])
        headers = frappe.get_list(
            doctype,
            filters=filters,
            fields=["name", date_field],
            order_by=f"{date_field} desc, modified desc",
            limit_page_length=25,
        )
        for header in headers:
            doc = frappe.get_doc(doctype, header["name"])
            if not doc.has_permission("read"):
                continue
            for row in (doc.get("items") or []):
                if row.item_code == item_code and (row.uom == uom or not uom):
                    doc_date = str(header[date_field])
                    if best is None or doc_date > best["date"]:
                        best = {
                            "source": "history_price",
                            "sourceLabel": f"历史成交价（{doc.name} · {doc_date}）",
                            "rate": format_rate(row.rate),
                            "referenceDoc": doc.name,
                            "date": doc_date,
                        }
                    break
            if best and best["date"] == posting_date:
                break
    if best:
        best.pop("date", None)
    return best


def resolve_price_advisory(
    *,
    kind: str,
    company_id: str,
    partner_id: str | None,
    product_id: str,
    posting_date: str,
    quantity: str | float | int = 1,
    uom: str | None = None,
    price_list: str | None = None,
    warehouse_id: str | None = None,
    priority_order: list[str] | None = None,
    history_window_days: int = DEFAULT_HISTORY_WINDOW_DAYS,
    proposed_rate=None,
) -> dict:
    from erpnext.stock.get_item_details import get_item_details

    if kind in ("purchase_receipt", "purchase", "Purchase Order", "Purchase Receipt", "Purchase Invoice"):
        is_buying = True
        doctype = "Purchase Order"
        party_doctype = "Supplier"
        party_field = "supplier"
    elif kind in ("sales_delivery", "sales", "Sales Order", "Delivery Note", "Sales Invoice", "Quotation"):
        is_buying = False
        doctype = "Sales Order"
        party_doctype = "Customer"
        party_field = "customer"
    else:
        raise ValueError("单据方向仅支持采购或销售。")

    if not isinstance(history_window_days, int) or not 1 <= history_window_days <= MAX_HISTORY_WINDOW_DAYS:
        raise ValueError(f"historyWindowDays 须为 1 至 {MAX_HISTORY_WINDOW_DAYS} 的整数。")
    date.fromisoformat(posting_date)
    order = normalize_priority_order(priority_order)

    # Enforce native read permissions on Item, Company, and Party.
    item = frappe.get_doc("Item", product_id)
    item.check_permission("read")
    frappe.get_doc("Company", company_id).check_permission("read")

    resolved_price_list = price_list
    if partner_id:
        party_doc = frappe.get_doc(party_doctype, partner_id)
        party_doc.check_permission("read")
        if not resolved_price_list:
            resolved_price_list = party_doc.get("default_price_list")

    if not resolved_price_list:
        default_field = "buying_price_list" if is_buying else "selling_price_list"
        settings_dt = "Buying Settings" if is_buying else "Selling Settings"
        resolved_price_list = frappe.db.get_single_value(settings_dt, default_field)

    resolved_uom = uom or item.stock_uom
    conversion_factor = Decimal("1")
    for uom_row in (item.get("uoms") or []):
        if uom_row.uom == resolved_uom and uom_row.conversion_factor:
            conversion_factor = Decimal(str(uom_row.conversion_factor))
            break

    # 1. Native Pricing Rule evaluation
    pricing_rule_candidate = None
    if resolved_price_list:
        ctx = {
            "doctype": doctype,
            "company": company_id,
            "item_code": product_id,
            party_field: partner_id,
            "transaction_date": posting_date,
            "price_list": resolved_price_list,
            "currency": "CNY",
            "price_list_currency": "CNY",
            "conversion_rate": 1,
            "plc_conversion_rate": 1,
            "qty": float(Decimal(str(quantity))),
            "uom": resolved_uom,
            "ignore_party": not bool(partner_id),
        }
        if warehouse_id:
            ctx["warehouse"] = warehouse_id
        details = get_item_details(ctx)
        applied_rules_raw = details.get("pricing_rules") or ""
        applied_rules = []
        if isinstance(applied_rules_raw, str) and applied_rules_raw.strip():
            try:
                parsed_rules = json.loads(applied_rules_raw)
                if isinstance(parsed_rules, list):
                    applied_rules = [str(r) for r in parsed_rules if r]
            except ValueError:
                applied_rules = [applied_rules_raw.strip()]
        if applied_rules:
            rule_name = applied_rules[0]
            rule_title = frappe.db.get_value("Pricing Rule", rule_name, "title") or rule_name
            rule_rate = details.get("price_list_rate") if details.get("price_list_rate") is not None else details.get("rate")
            if rule_rate is not None:
                pricing_rule_candidate = {
                    "source": "pricing_rule",
                    "sourceLabel": f"价格规则（{rule_title}）",
                    "rate": format_rate(rule_rate),
                    "referenceDoc": rule_name,
                }

    # 2. Party-specific Item Price
    party_price_candidate = None
    if partner_id:
        p_row = _find_item_price(product_id, resolved_price_list, resolved_uom, posting_date, is_buying, party_field, partner_id)
        if p_row:
            party_price_candidate = {
                "source": "party_price",
                "sourceLabel": f"往来专价（{resolved_price_list}）",
                "rate": format_rate(p_row["price_list_rate"]),
                "referenceDoc": p_row["name"],
            }

    # 3. General Tier / Price List
    tier_price_candidate = None
    t_row = _find_item_price(product_id, resolved_price_list, resolved_uom, posting_date, is_buying, party_field, None)
    if t_row:
        tier_price_candidate = {
            "source": "tier_price",
            "sourceLabel": f"档位价（{resolved_price_list}）",
            "rate": format_rate(t_row["price_list_rate"]),
            "referenceDoc": t_row["name"],
        }

    # 4. Recent Historical Transaction Price (submitted, non-return only)
    history_candidate = _find_history_price(
        is_buying, company_id, partner_id, product_id, resolved_uom, posting_date, history_window_days
    )

    # 5. Item Default Rate
    item_default_candidate = None
    default_base = item.get("last_purchase_rate") if is_buying else item.get("standard_rate")
    if default_base and Decimal(str(default_base)) > 0:
        item_default_candidate = {
            "source": "item_default",
            "sourceLabel": "商品默认价",
            "rate": format_rate(Decimal(str(default_base)) * conversion_factor),
            "referenceDoc": item.name,
        }

    candidates_map = {
        "pricing_rule": pricing_rule_candidate,
        "party_price": party_price_candidate,
        "tier_price": tier_price_candidate,
        "history_price": history_candidate,
        "item_default": item_default_candidate,
    }
    selected, ordered_candidates = select_price_candidate(candidates_map, order)

    effective_rate = proposed_rate if proposed_rate is not None else selected.get("rate")
    minimum_sale = (
        check_minimum_sale(effective_rate, item.get("custom_trade_minimum_sale"), conversion_factor)
        if not is_buying
        else {"belowMinimumSale": False, "minimumSaleRate": None, "stockUomRate": None, "warning": None}
    )

    return {
        "productId": product_id,
        "uom": resolved_uom,
        "conversionFactor": str(conversion_factor.normalize()),
        "currency": "CNY",
        "priceList": resolved_price_list or "",
        "selected": selected,
        "candidates": ordered_candidates,
        "priorityOrder": order,
        "historyWindowDays": history_window_days,
        "minimumSale": minimum_sale,
    }


@frappe.whitelist(methods=["POST"])
@frappe.read_only()
def get_price_advisory(payload: dict | str):
    data = frappe.parse_json(payload)
    if not isinstance(data, dict):
        frappe.throw("请提供有效的取价查询参数。")
    return resolve_price_advisory(
        kind=data.get("kind") or "",
        company_id=data.get("companyId") or "",
        partner_id=data.get("partnerId"),
        product_id=data.get("productId") or "",
        posting_date=data.get("postingDate") or date.today().isoformat(),
        quantity=data.get("quantity") or 1,
        uom=data.get("uom"),
        price_list=data.get("priceList"),
        warehouse_id=data.get("warehouseId"),
        priority_order=data.get("priorityOrder"),
        history_window_days=data.get("historyWindowDays", DEFAULT_HISTORY_WINDOW_DAYS),
        proposed_rate=data.get("proposedRate"),
    )
