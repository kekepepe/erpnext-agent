from decimal import Decimal, ROUND_HALF_UP

DIGITS = "零壹贰叁肆伍陆柒捌玖"


def business_title(doc):
    """Reviewed document semantics; never change the native type or numbering."""
    doctype = doc.get("doctype")
    if doctype == "Payment Entry":
        return {"Receive": "收款单", "Pay": "付款单", "Internal Transfer": "资金转账单"}.get(doc.get("payment_type"), "收付款凭证")
    if doctype == "Stock Entry":
        return {"Material Transfer": "库存调拨单", "Material Receipt": "其他入库单", "Material Issue": "其他出库单"}.get(doc.get("purpose"), "库存变动单")
    if doc.get("is_return") in (1, "1", True):
        returns = {"Purchase Receipt": "采购退货单", "Delivery Note": "销售退货单", "Purchase Invoice": "采购退货账务单", "Sales Invoice": "销售贷项通知单"}
        if doctype in returns:
            return returns[doctype]
    return {"Quotation": "报价单", "Purchase Order": "采购订单", "Purchase Receipt": "采购入库单", "Purchase Invoice": "采购发票", "Sales Order": "销售订单", "Delivery Note": "销售出库单", "Sales Invoice": "销售发票", "Stock Reconciliation": "库存盘点调整单"}.get(doctype, doctype or "业务单据")


def integer_words(value):
    if value == 0:
        return "零"
    groups = []
    for unit in ("", "万", "亿", "兆"):
        part = value % 10000
        value //= 10000
        words, zero = "", False
        for place, suffix in ((1000, "仟"), (100, "佰"), (10, "拾"), (1, "")):
            digit, part = divmod(part, place)
            if digit:
                if zero and words:
                    words += "零"
                words += DIGITS[digit] + suffix
                zero = False
            elif words:
                zero = True
        groups.append((words, unit))
        if not value:
            break
    if value:
        raise ValueError("Amount exceeds supported Chinese currency range")
    result = ""
    for index in range(len(groups)-1, -1, -1):
        words, unit = groups[index]
        if not words:
            if result and not result.endswith("零"):
                result += "零"
            continue
        # A lower non-zero group under 1000 needs an intervening zero.
        if result and not result.endswith("零") and not any(c in words for c in "仟"):
            result += "零"
        result += words + unit
    return result.rstrip("零")


def chinese_money(amount):
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "负" if value < 0 else ""
    cents = int(abs(value) * 100)
    yuan, cents = divmod(cents, 100)
    jiao, fen = divmod(cents, 10)
    result = sign + integer_words(yuan) + "元"
    if not cents:
        return result + "整"
    if jiao:
        result += DIGITS[jiao] + "角"
    elif fen:
        result += "零"
    if fen:
        result += DIGITS[fen] + "分"
    return result
