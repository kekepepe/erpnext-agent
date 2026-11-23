frappe.query_reports["Product Inventory"] = {
  filters: [
    {fieldname: "company", label: "公司", fieldtype: "Link", options: "Company",
      default: frappe.defaults.get_user_default("Company"), reqd: 1},
    {fieldname: "to_date", label: "库存截止日", fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1},
    {fieldname: "item_group", label: "商品分类", fieldtype: "Link", options: "Item Group"},
    {fieldname: "warehouse", label: "仓库", fieldtype: "Link", options: "Warehouse",
      get_query: () => ({filters: {company: frappe.query_report.get_filter_value("company"), is_group: 0}})},
    {fieldname: "keyword", label: "商品编号 / 名称 / 规格 / 型号", fieldtype: "Data"},
    {fieldname: "include_zero", label: "显示零库存商品", fieldtype: "Check", default: 1},
    {fieldname: "include_disabled", label: "包含停用商品", fieldtype: "Check", default: 0},
    {fieldname: "include_image", label: "显示图片链接", fieldtype: "Check", default: 1},
    {fieldname: "valuation_method", label: "成本算法", fieldtype: "Select",
      options: [{value: "", label: "全部"}, {value: "Moving Average", label: "移动平均"}, {value: "FIFO", label: "先进先出"}]},
    {fieldname: "auxiliary_uom", label: "辅助计量单位", fieldtype: "Link", options: "UOM"},
    {fieldname: "estimate_tier", label: "预估计价档位", fieldtype: "Link", options: "Price List",
      default: "预设售价一档", get_query: () => ({filters: {enabled: 1, selling: 1}})},
  ],

  onload(report) {
    report.page.set_title("库存状况表－商品库存");
    if (frappe.model.can_export("Stock Ledger Entry")) {
      report.page.add_inner_button("下载商品库存 Excel", () => {
        const filters = report.get_filter_values();
        if (!filters.company) {
          frappe.msgprint("请先选择公司。");
          return;
        }
        const query = new URLSearchParams({filters: JSON.stringify(filters)});
        window.open("/api/method/erpnext_zh.hardware_workbench.report.product_inventory.product_inventory.download_inventory?" +
          query, "_blank", "noopener");
      });
    }
  },

  get_datatable_options(options) {
    return {...options, serialNoColumn: false};
  },

  formatter(value, row, column, data, default_formatter) {
    if (column.fieldname === "image" && typeof value === "string" && /^\/(?:private\/)?files\//.test(value)) {
      const link = document.createElement("a");
      link.href = value;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = "查看图片";
      return link.outerHTML;
    }
    return default_formatter(value, row, column, data);
  },
};
