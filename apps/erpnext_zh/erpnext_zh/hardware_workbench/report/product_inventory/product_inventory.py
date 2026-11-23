"""Stock Balance presentation for the product inventory worksheet."""

from collections import defaultdict
import json
from pathlib import Path
import re

import frappe
from frappe.desk.query_report import generate_report_result, get_report_doc
from frappe.utils import cint, flt, getdate, today

TIERS = json.loads((Path(__file__).parents[3] / "price_tiers.json").read_text())


def records(doctype, **kwargs):
    return frappe.get_list(doctype, page_length=0, **kwargs)


def columns(tiers, currency):
    def field(name, label, fieldtype="Data", options=None, width=125):
        entry = dict(fieldname=name, label=label, fieldtype=fieldtype, width=width)
        if options:
            entry["options"] = options
        return entry

    def money(name, label):
        return field(name, label, "Currency", currency)

    result = [field("row_number", "行号", "Int", width=62)]
    result.append(field("image", "图片", width=85))
    result.extend(field(f"group_{i}", f"{name}级分类") for i, name in enumerate("一二三四", 1))
    result.extend([
        field("item_code", "商品编号", "Link", "Item"),
        field("item_name", "商品名称", width=190),
        field("specification", "规格"), field("model", "型号"), field("brand", "品牌"),
        money("retail_price", "零售价"), money("reference_cost", "参考成本价"),
        field("book_qty", "账面库存", "Float"), field("stock_uom", "基本单位", width=95),
        money("unit_cost", "成本均价"), money("auxiliary_unit_cost", "辅助单位成本均价"),
        money("stock_value", "库存金额"),
    ])
    result.extend(money(f"tier_{tier['number']}", tier["label"]) for tier in tiers if tier["number"])
    result.extend([
        money("estimated_sales", "参考销售总价"), field("margin_percent", "参考毛利率(%)", "Percent"),
    ])
    return result


def group_path(group, groups):
    path = []
    seen = set()
    while group and group != "All Item Groups" and group not in seen:
        seen.add(group)
        path.append(group)
        group = groups.get(group)
    path.reverse()
    # Show deeper groups within the fourth column rather than losing the leaf.
    return path[:3] + [" / ".join(path[3:])] if len(path) > 4 else path


def selling_lists(currency):
    if not frappe.has_permission("Price List", "read") or not frappe.has_permission("Item Price", "read"):
        return set()
    return {row.name for row in records("Price List", fields=["name"], filters={
        "enabled": 1, "selling": 1, "currency": currency,
    })}


def report_tiers(allowed_lists):
    tiers = list(TIERS)
    numbers = {tier["number"] for tier in tiers}
    for name in sorted(allowed_lists):
        match = re.fullmatch(r"预设售价([1-9][0-9]*)档?", name)
        if match and (number := int(match[1])) not in numbers:
            numbers.add(number)
            tiers.append(dict(number=number, name=name, label=f"预设售价{number}"))
    return sorted(tiers, key=lambda tier: tier["number"])


def prices_from_lists(codes, stock_units, allowed_lists, as_of):
    prices = {}
    if not codes or not allowed_lists:
        return prices
    data = records("Item Price", fields=[
        "name", "item_code", "price_list", "price_list_rate", "valid_from", "valid_upto", "uom",
        "customer", "supplier", "batch_no",
    ], filters={"item_code": ["in", codes], "price_list": ["in", sorted(allowed_lists)]},
        order_by="valid_from desc, uom desc, name asc")
    for price in data:
        if (price.customer or price.supplier or price.batch_no
                or (price.uom and price.uom != stock_units[price.item_code])
                or (price.valid_from and getdate(price.valid_from) > as_of)
                or (price.valid_upto and getdate(price.valid_upto) < as_of)):
            continue
        prices.setdefault((price.item_code, price.price_list), price.price_list_rate)
    return prices


def conversions(codes, stock_units, requested_uom):
    rates = {}
    if not codes:
        return rates
    for row in records("UOM Conversion Detail", fields=["parent", "uom", "conversion_factor", "idx"],
                       filters={"parent": ["in", codes], "parenttype": "Item", "parentfield": "uoms"},
                       parent_doctype="Item", order_by="idx asc"):
        if (row.uom != stock_units[row.parent] and flt(row.conversion_factor) > 0
                and (not requested_uom or row.uom == requested_uom)):
            rates.setdefault(row.parent, flt(row.conversion_factor))
    return rates


def execute(filters=None):
    filters = frappe._dict(filters or {})
    report = get_report_doc("Stock Balance")
    if not filters.company:
        return [], []
    if not frappe.has_permission("Company", "read", doc=filters.company):
        frappe.throw("无权查看该公司的商品库存。", frappe.PermissionError)
    for doctype in ("Warehouse", "Item", "Item Group"):
        frappe.has_permission(doctype, "read", throw=True)

    as_of = getdate(filters.to_date or today())
    currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    allowed_lists = selling_lists(currency)
    tiers = report_tiers(allowed_lists)
    result_columns = columns(tiers, currency)

    warehouse_filters = {"company": filters.company, "is_group": 0}
    if filters.warehouse:
        warehouse_filters["name"] = filters.warehouse
    warehouses = {row.name for row in records("Warehouse", fields=["name"], filters=warehouse_filters)}
    if not warehouses:
        return result_columns, []

    item_filter = {"is_stock_item": 1}
    if not cint(filters.include_disabled):
        item_filter["disabled"] = 0
    if filters.item_group:
        root_group = frappe.get_doc("Item Group", filters.item_group)
        root_group.check_permission("read")
        descendants = records("Item Group", fields=["name"], filters={
            "lft": [">=", root_group.lft], "rgt": ["<=", root_group.rgt],
        })
        item_filter["item_group"] = ["in", [group.name for group in descendants]]
    search = [["Item", key, "like", f"%{filters.keyword}%"] for key in (
        "item_code", "item_name", "custom_trade_specification", "custom_trade_model",
    )] if filters.keyword else None
    items = records("Item", filters=item_filter, or_filters=search, fields=[
        "name", "item_name", "item_group", "image", "brand", "stock_uom", "valuation_method",
        "custom_trade_specification", "custom_trade_model", "custom_trade_reference_cost",
    ], order_by="item_group asc, name asc")
    if filters.valuation_method:
        company_method = frappe.get_cached_value("Company", filters.company, "valuation_method")
        items = [item for item in items if (
            item.valuation_method or company_method
        ) == filters.valuation_method]
    codes = [row.name for row in items]
    if not codes:
        return result_columns, []

    balance = generate_report_result(report, frappe._dict(
        company=filters.company, from_date=str(as_of), to_date=str(as_of),
        warehouse=sorted(warehouses), item=codes,
    ))["result"]
    totals = defaultdict(lambda: [0.0, 0.0])
    code_set = set(codes)
    for row in balance:
        if isinstance(row, dict) and row.get("warehouse") in warehouses and row.get("item_code") in code_set:
            qty_value = totals[row["item_code"]]
            qty_value[0] += flt(row.get("bal_qty"))
            qty_value[1] += flt(row.get("bal_val"))

    groups = {row.name: row.parent_item_group for row in records(
        "Item Group", fields=["name", "parent_item_group"],
    )}
    items = [item for item in items if (
        (cint(filters.include_zero) and not filters.warehouse)
        or (item.name in totals and (cint(filters.include_zero) or any(totals[item.name])))
    )]
    stock_units = {item.name: item.stock_uom for item in items}
    used_lists = {tier["name"] for tier in tiers}
    estimate_tier = filters.estimate_tier or TIERS[1]["name"]
    used_lists.add(estimate_tier)
    pricing = prices_from_lists(list(stock_units), stock_units, allowed_lists & used_lists, as_of)
    auxiliary_rates = conversions(list(stock_units), stock_units, filters.auxiliary_uom)
    result = []
    for i, item in enumerate(items, 1):
        qty, value = totals[item.name]
        unit_cost = value / qty if qty else None
        rate = pricing.get((item.name, estimate_tier))
        sales = flt(qty * rate, 2) if rate is not None else None
        row = dict(
            row_number=i, image=item.get("image") if cint(filters.include_image) else None,
            item_code=item.name, item_name=frappe._(item.item_name), brand=item.get("brand"),
            specification=item.get("custom_trade_specification"), model=item.get("custom_trade_model"),
            reference_cost=item.get("custom_trade_reference_cost"), stock_uom=frappe._(item.stock_uom),
            book_qty=qty, stock_value=flt(value, 2), unit_cost=unit_cost,
            auxiliary_unit_cost=unit_cost * auxiliary_rates[item.name]
            if unit_cost is not None and item.name in auxiliary_rates else None,
            retail_price=pricing.get((item.name, TIERS[0]["name"])), estimated_sales=sales,
            margin_percent=100 * (sales - value) / sales if qty > 0 and sales and sales > 0 else None,
        )
        row.update({f"group_{level}": frappe._(group)
                    for level, group in enumerate(group_path(item.item_group, groups), 1)})
        row.update({f"tier_{tier['number']}": pricing.get((item.name, tier["name"]))
                    for tier in tiers if tier["number"]})
        result.append(row)
    return result_columns, result


@frappe.whitelist(methods=["GET"])
@frappe.read_only()
def download_inventory(filters: str):
    """Download the source worksheet's two-level header with current report filters."""
    from io import BytesIO

    from frappe.desk.utils import provide_binary_file
    from xlsxwriter import Workbook

    report = get_report_doc("Product Inventory")
    frappe.has_permission(report.ref_doctype, "export", throw=True)
    filters = frappe._dict(frappe.parse_json(filters) or {})
    report_columns, result = execute(filters)
    if not report_columns:
        frappe.throw("请先选择公司。")

    output = BytesIO()
    with Workbook(output, {"strings_to_formulas": False, "strings_to_urls": False}) as book:
        sheet = book.add_worksheet("商品库存")
        title = book.add_format({"bold": True, "font_size": 16})
        header = book.add_format({
            "bold": True, "align": "center", "valign": "vcenter",
            "text_wrap": True, "border": 1, "bg_color": "#E8EFF7",
        })
        sheet.merge_range(0, 0, 0, len(report_columns) - 1, "库存状况表－商品库存", title)
        sheet.write_row(1, 0, [
            "公司", filters.company, "库存截止日", str(filters.to_date or today()),
            "仓库", filters.warehouse or "全部有权限的仓库",
            "商品分类", filters.item_group, "快速查询", filters.keyword,
        ])
        sheet.write_row(2, 0, [
            "辅助单位", filters.auxiliary_uom or "首个可用辅助单位",
            "预估计价档位", filters.estimate_tier or TIERS[1]["name"],
        ])
        stock_start = next(i for i, col in enumerate(report_columns) if col["fieldname"] == "book_qty")
        estimate_start = next(i for i, col in enumerate(report_columns) if col["fieldname"] == "tier_1")
        sheet.merge_range(4, stock_start, 4, estimate_start - 1, "财务库存数据", header)
        sheet.merge_range(4, estimate_start, 4, len(report_columns) - 1, "预估收益", header)
        money_format = book.add_format({"num_format": "0.00"})
        for col_index, column in enumerate(report_columns):
            sheet.set_column(col_index, col_index, column["width"] / 7,
                             money_format if column["fieldtype"] == "Currency" else None)
            if col_index < stock_start:
                sheet.merge_range(4, col_index, 5, col_index, column["label"], header)
            else:
                sheet.write(5, col_index, column["label"], header)
        for row_index, row in enumerate(result, 6):
            sheet.write_row(row_index, 0, [row.get(column["fieldname"]) for column in report_columns])
        sheet.freeze_panes(6, 0)
    provide_binary_file(f"库存状况表-商品库存-{filters.to_date or today()}", "xlsx", output.getvalue())
