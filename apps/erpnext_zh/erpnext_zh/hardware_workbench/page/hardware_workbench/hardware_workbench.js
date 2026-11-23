frappe.pages["hardware-workbench"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({parent: wrapper, title: "工作台", single_column: true});
    page.set_primary_action("刷新", () => hardware_workbench.render(page));
    hardware_workbench.render(page);
};
frappe.pages["hardware-workbench"].on_page_show = function(wrapper) {
    if (wrapper.page) hardware_workbench.render(wrapper.page);
};
