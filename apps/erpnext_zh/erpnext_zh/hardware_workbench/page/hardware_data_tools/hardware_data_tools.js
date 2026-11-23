frappe.pages["hardware-data-tools"].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({parent: wrapper, title: "资料工具", single_column: true});
  page.set_primary_action("刷新", () => hardware_data_tools.render(page, true));
};
frappe.pages["hardware-data-tools"].on_page_show = function(wrapper) {
  if (wrapper.page) hardware_data_tools.render(wrapper.page);
};
