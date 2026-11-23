/* Permission-aware shortcuts to native ERPNext import, export and print tools. */
(() => {
  const groupLabel = "资料操作";
  const listPages = new WeakSet();

  function openImport(doctype) {
    frappe.new_doc("Data Import", {
      reference_doctype: doctype,
      import_type: "Insert New Records",
      submit_after_import: 0,
    });
  }

  function openExporter(doctype, filters, template = false) {
    frappe.require("data_import_tools.bundle.js", () => {
      frappe.model.with_doctype(doctype, () => {
        const exporter = new frappe.data_import.DataExporter(doctype, "Insert New Records", "Excel");
        if (!template) {
          exporter.dialog.set_value("export_records", filters.length ? "by_filter" : "all");
          exporter.filter_group.add_filters_to_filter_group(filters);
        }
      });
    });
  }

  function exportList(list) {
    const selected = list.get_checked_items(true);
    const filters = selected.length
      ? [[list.doctype, "name", "in", selected]]
      : list.get_filters_for_args();
    openExporter(list.doctype, filters);
  }

  function bulkPrint(list) {
    const rows = list.get_checked_items();
    if (!rows.length) {
      frappe.msgprint("请先在列表勾选要打印或下载的单据。");
      return;
    }
    new frappe.ui.BulkOperations({doctype: list.doctype}).print(rows);
  }

  function listActions(list, item) {
    if (!item || listPages.has(list.page)) return;
    listPages.add(list.page);
    if (item.can_import) {
      list.page.add_inner_button("导入文件", () => openImport(list.doctype), groupLabel);
      list.page.add_inner_button("下载导入模板", () => openExporter(list.doctype, [], true), groupLabel);
    }
    if (item.can_export) {
      list.page.add_inner_button("导出数据", () => exportList(list), groupLabel);
    }
    if (item.can_print) {
      list.page.add_inner_button("批量下载 PDF / 打印", () => bulkPrint(list), groupLabel);
    }
  }

  function formActions(frm, item) {
    if (!item || frm.is_new()) return;
    if (item.can_export) {
      frm.add_custom_button("导出本单数据", () => openExporter(
        frm.doctype, [[frm.doctype, "name", "=", frm.doc.name]]
      ), groupLabel);
    }
    if (item.can_print && frappe.model.can_print_doc(frm)) {
      frm.add_custom_button("打印本单", () => frm.print_doc(), groupLabel);
      frm.add_custom_button("下载本单 PDF", () => {
        if (frm.is_dirty()) {
          frappe.msgprint("请先保存单据，再下载 PDF。");
          return;
        }
        const query = new URLSearchParams({
          doctype: frm.doctype,
          name: frm.doc.name,
          format: frm.meta.default_print_format || "Standard",
          language: frappe.boot.lang,
        });
        window.open("/api/method/frappe.utils.print_format.download_pdf?" + query, "_blank", "noopener");
      }, groupLabel);
    }
  }

  function button(parent, label, action) {
    const control = document.createElement("button");
    control.type = "button";
    control.className = "btn btn-default btn-sm";
    control.textContent = label;
    control.onclick = action;
    parent.append(control);
  }

  async function render(page, force = false) {
    const host = page.main.get(0);
    host.classList.add("hw-page", "hw-data-tools");
    host.textContent = "正在读取可用资料工具…";
    try {
      const data = await hardware_workbench.context(force);
      const groups = data.groups.filter(group => group.id !== "settings");
      host.replaceChildren();
      const intro = document.createElement("p");
      intro.className = "text-muted";
      intro.textContent = "按业务类型打开单据、导入文件、下载模板或导出数据。打印和批量 PDF 可在列表勾选单据后办理。";
      host.append(intro);
      for (const group of groups) {
        const section = document.createElement("section");
        const heading = document.createElement("h3");
        heading.textContent = group.label;
        section.append(heading);
        for (const item of group.items) {
          const row = document.createElement("div");
          row.className = "hw-data-row";
          const title = document.createElement("span");
          title.textContent = item.label;
          row.append(title);
          const buttons = document.createElement("div");
          buttons.className = "hw-data-buttons";
          button(buttons, item.report ? "打开报表" : "打开列表", () => hardware_workbench.go(item));
          if (item.report) {
            if (item.can_export || item.can_print) {
              const note = document.createElement("span");
              note.className = "text-muted";
              note.textContent = [item.can_export && "导出 Excel / CSV", item.can_print && "下载 PDF / 打印"].filter(Boolean).join(" · ");
              buttons.append(note);
            }
          } else {
            if (item.can_import) {
              button(buttons, "导入文件", () => openImport(item.doctype));
              button(buttons, "下载模板", () => openExporter(item.doctype, [], true));
            }
            if (item.can_export) {
              button(buttons, "导出数据", () => openExporter(item.doctype, Object.entries(item.filters || {})
                .map(([field, value]) => [item.doctype, field, "=", value])));
            }
            if (item.can_print) {
              button(buttons, "下载 PDF / 打印", () => hardware_workbench.go(item));
            }
          }
          row.append(buttons);
          section.append(row);
        }
        host.append(section);
      }
      if (!groups.length) host.append("当前账号没有可查看的业务资料。");
    } catch {
      host.textContent = "资料工具加载失败，请刷新后重试。";
    }
  }

  window.hardware_data_tools = {render, listActions, formActions};
})();
