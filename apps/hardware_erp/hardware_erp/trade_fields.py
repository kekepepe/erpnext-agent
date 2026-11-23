"""Additional trade fields on native documents. The ERPNext controllers own prices and totals."""

TRADE_DOCUMENTS = (
    "Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice",
    "Sales Order", "Delivery Note", "Sales Invoice",
)

PRODUCT_DETAILS = (
    ("custom_trade_short_name", "简称"),
    ("custom_trade_specification", "规格"),
    ("custom_trade_model", "型号"),
    ("custom_trade_name_en", "英文商品名称"),
)
PRODUCT_REQUIREMENT = "custom_trade_requirement_en"
LINE_REQUIREMENT = "custom_trade_line_requirement_en"
PRICE_INPUT = "custom_trade_price_input"


def install():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    def field(name, label, after, fieldtype="Data", **options):
        return dict(fieldname=name, label=label, insert_after=after, fieldtype=fieldtype, **options)

    item_fields = []
    line_fields = []
    after = "item_name"
    for name, label in PRODUCT_DETAILS:
        item_fields.append(field(name, label, after))
        line_fields.append(field(name, label, after, read_only=1))
        after = name

    item_fields.extend([
        field(PRODUCT_REQUIREMENT, "英文商品要求", after, "Small Text"),
        field("custom_trade_reference_cost", "参考成本价（本位币）", "standard_rate", "Currency", non_negative=1),
        field("custom_trade_minimum_sale", "最低售价参考（本位币）", "custom_trade_reference_cost", "Currency", non_negative=1),
        field(PRICE_INPUT, "档位价格", "pricing_tab", "HTML", no_copy=1),
    ])
    line_fields.extend([
        field("custom_trade_line_mark", "标记", after),
        field(LINE_REQUIREMENT, "英文订单要求", "description", "Small Text"),
        field("custom_trade_gross_rate", "含税单价", "net_rate", "Currency", read_only=1, options="currency"),
        field("custom_trade_gross_amount", "含税金额", "net_amount", "Currency", read_only=1, options="currency"),
        field("custom_trade_tax_percent", "税费率（折算 %）", "custom_trade_gross_amount", "Percent", read_only=1,
              description="保存后按 ERPNext 逐行税费计算。比例为计入单据总额的税费除以折后不含税金额。"),
    ])
    create_custom_fields({
        "Item": item_fields,
        **{doctype + " Item": [dict(entry) for entry in line_fields] for doctype in TRADE_DOCUMENTS},
        **{doctype: [
            field("custom_trade_summary", "摘要", "terms", "Small Text"),
            field("custom_trade_line_review", "商品核对与金额明细", "items", "HTML"),
        ] for doctype in TRADE_DOCUMENTS},
    })


def configure_forms():
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    # Use the full native Item form as its normal create entrypoint so users see pricing.
    make_property_setter("Item", None, "quick_entry", 0, "Check", for_doctype=True)
    make_property_setter("Item", "pricing_tab", "depends_on", "", "Data")
    make_property_setter("Item", "pricing_tab", "label", "档位价格", "Data")
    make_property_setter("Customer", "default_price_list", "allow_in_quick_entry", 1, "Check")
    make_property_setter("Customer", "default_price_list", "label", "默认报价档位", "Data")


def after_install():
    install()
    configure_forms()


def populate_product_details(doc, method=None):
    import frappe

    fields = [name for name, _ in PRODUCT_DETAILS]
    old_doc = doc.get_doc_before_save()
    old_items = {row.name: row for row in old_doc.items} if old_doc else {}
    products = {}

    for row in doc.items:
        if not row.item_code:
            continue
        old_row = old_items.get(row.name)
        if old_row and old_row.item_code == row.item_code:
            continue
        if row.item_code not in products:
            products[row.item_code] = frappe.get_cached_doc("Item", row.item_code)
        item = products[row.item_code]
        for name in fields:
            # Mapping between native documents can carry the original snapshot.
            if old_row or not row.get(name):
                row.set(name, item.get(name))
        if row.get(LINE_REQUIREMENT) is None:
            row.set(LINE_REQUIREMENT, item.get(PRODUCT_REQUIREMENT))


def calculate_line_amounts(doc, method=None):
    from collections import defaultdict

    from frappe.utils import flt

    tax_by_row = defaultdict(float)
    for detail in doc.get("_item_wise_tax_details") or []:
        if detail.tax.get("category") != "Valuation":
            tax_by_row[detail.item.idx] += flt(detail.amount)

    conversion_rate = flt(doc.conversion_rate) or 1
    for row in doc.items:
        net = flt(row.net_amount)
        tax = tax_by_row[row.idx] / conversion_rate
        gross = net + tax
        row.custom_trade_gross_rate = flt(gross / row.qty, row.precision("rate")) if row.qty else None
        row.custom_trade_gross_amount = flt(gross, row.precision("net_amount"))
        row.custom_trade_tax_percent = flt(100 * tax / net, 4) if net else None


def create_initial_prices(doc, method=None):
    """Insert native Item Prices in the same transaction as the new Item."""
    from decimal import Decimal, InvalidOperation

    import frappe
    from frappe import _

    request = doc.get("trade_initial_prices")
    if request is None:
        return
    if not isinstance(request, dict):
        frappe.throw(_("请按价目表填写档位价格。"))

    for price_list, rate in request.items():
        if not isinstance(price_list, str) or not isinstance(rate, (str, int, float)):
            frappe.throw(_("档位价格格式无效。"))
        try:
            amount = Decimal(str(rate))
        except InvalidOperation:
            frappe.throw(_("档位价格必须是有效的非负金额。"))
        if not amount.is_finite() or amount < 0 or amount > Decimal("999999999999"):
            frappe.throw(_("档位价格必须是有效的非负金额。"))

        tier = frappe.get_doc("Price List", price_list)
        tier.check_permission("read")
        if not tier.enabled or not ((tier.selling and doc.is_sales_item) or (tier.buying and doc.is_purchase_item)):
            frappe.throw(_("该价目表未启用，或与商品的采购和销售设置不匹配。"))

        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": doc.name,
            "price_list": tier.name,
            "uom": doc.stock_uom,
            "price_list_rate": float(amount),
        }).insert()
