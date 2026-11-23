/* Compose with native list hooks; never change business fields or approval transitions. */
(() => {
  for (const dt of ["Purchase Order", "Purchase Receipt", "Purchase Invoice", "Sales Order", "Delivery Note", "Sales Invoice", "Stock Entry", "Stock Reconciliation", "Payment Entry",
    "Quotation", "Item", "Item Group", "Customer", "Supplier", "Warehouse", "UOM", "Item Price", "Price List"]) {
    const settings = frappe.listview_settings[dt] ||= {};
    if (settings.hw_extended) continue;
    settings.hw_extended = true;
    const previousLoad = settings.onload;
    settings.onload = function(list) {
      if (previousLoad) previousLoad.call(this, list);
      const nativeIndicator = list.get_indicator_html.bind(list);
      list.get_indicator_html = function(doc, showWorkflow) {
        const html = nativeIndicator(doc, showWorkflow);
        // Only the generated workflow indicator for an actually cancelled document.
        // No free-text/user field replacement; a rejected draft is not a cancellation.
        if (frappe.boot.lang === "zh" && doc.docstatus === 2 && doc.workflow_state === "Rejected") {
          const span = document.createElement("span"); span.innerHTML = html;
          const indicator = span.querySelector('[data-filter="workflow_state,=,Rejected"]');
          if (indicator) indicator.textContent = "已撤销";
          return span.innerHTML;
        }
        return html;
      };
    };
    const previousAction = settings.primary_action;
    settings.primary_action = function() {
      const list = cur_list;
      const returning = Number(list.filter_area.filter_list.get_filter_value("is_return")) === 1;
      if (returning && ["Purchase Receipt", "Purchase Invoice", "Delivery Note", "Sales Invoice"].includes(dt)) {
        frappe.msgprint("请打开已提交的原单，在“创建”菜单中办理退货或贷项。原单关联与可退数量由系统校验。");
        frappe.route_options = {is_return: 0, docstatus: 1};
        return frappe.set_route("List", dt, "List");
      }
      return previousAction ? previousAction.call(this) : list.make_new_doc();
    };
    const previousRefresh = settings.refresh;
    settings.refresh = function(list) {
      if (previousRefresh) previousRefresh.call(this, list);
      if (Number(list.filter_area.filter_list.get_filter_value("is_return")) === 1 && list.can_create) {
        list.page.set_primary_action("从原单办理退货", () => settings.primary_action(), "add");
      }
      window.hardware_workbench?.sync_list(list);
    };
  }
})();
