/* Native display hooks only. Never assign doc values or translate user comments. */
$(document).ready(() => {
    if (frappe.boot.lang !== "zh") return;
    const originalItem = frappe.form.link_formatters.Item;
    frappe.form.link_formatters.Item = (value, doc, df) => {
        const result = originalItem(value, doc, df);
        if (!doc.item_name || __(doc.item_name) === doc.item_name) return result;
        // Preserve the native branch, code and link target; translate its title only.
        if (result === value + ": " + doc.item_name) return value + ": " + __(doc.item_name);
        if (result === doc.item_name) return __(doc.item_name);
        return result;
    };

    const localizeInfo = frm => {
        const states = new Set((frm.meta.fields.find(df => df.fieldname === "status")?.options || "").split("\n"));
        // Info records are system status logs. Free-text comments, emails and
        // arbitrary Info prose are excluded, even if the dictionary knows them.
        for (const log of frm.get_docinfo().info_logs || []) {
            if (!states.has(log.content) || !log.content || __(log.content) === log.content) continue;
            frm.timeline?.wrapper?.find(".timeline-item").each((_, item) => {
                if (item.dataset.timestamp !== log.creation) return;
                item.querySelectorAll(".timeline-content").forEach(content => {
                    for (const node of content.childNodes) {
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() === log.content) {
                            node.textContent = " " + __(log.content);
                        }
                    }
                });
            });
        }
    };
    const localizeMoney = async frm => {
        if (frm.doc.currency !== "CNY") return;
        const name = frm.doc.name;
        const field = frm.fields_dict.in_words;
        if (!field || !frm.doc.in_words) return;
        // Match native buying/selling amount selection, including zero rounded totals.
        const amount = Math.abs(Number(!frm.doc.disable_rounded_total && frm.doc.rounded_total != null
            ? frm.doc.rounded_total : frm.doc.grand_total));
        if (!Number.isFinite(amount)) return;
        const response = await frappe.call({method: "erpnext_zh.display.money_words", args: {amount, currency: "CNY"}});
        const current = Math.abs(Number(!frm.doc.disable_rounded_total && frm.doc.rounded_total != null
            ? frm.doc.rounded_total : frm.doc.grand_total));
        if (frm.doc.name === name && frm.doc.currency === "CNY" && current === amount && field.disp_area) {
            // Native controls can render again after refresh hooks resolve.
            // Keep this in their formatter; scope cached text to this exact
            // document/amount so navigation cannot reuse another order's words.
            field.df.formatter = (value, df, options, doc) => {
                const source = doc || frm.doc;
                const total = Math.abs(Number(!source.disable_rounded_total && source.rounded_total != null
                    ? source.rounded_total : source.grand_total));
                return frappe.utils.escape_html(source.name === name && source.currency === "CNY" && total === amount
                    ? response.message : String(value || ""));
            };
            field.refresh();
        }
    };
    for (const dt of ["Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Sales Order", "Delivery Note", "Sales Invoice"]) {
        frappe.ui.form.on(dt, {
            refresh: frm => localizeMoney(frm),
            timeline_refresh: frm => localizeInfo(frm),
        });
    }
});
