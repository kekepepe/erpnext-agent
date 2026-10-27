"""Pure presentation API: no document lookup or write and no guest access."""
import frappe

from erpnext_zh.printing import chinese_money


@frappe.whitelist()
def money_words(amount, currency):
    if currency != "CNY":
        frappe.throw("Only CNY presentation is supported")
    return chinese_money(amount)
