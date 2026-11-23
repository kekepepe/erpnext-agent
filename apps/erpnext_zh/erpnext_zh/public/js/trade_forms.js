/* Native document fields and price lists; the server calculates the saved totals. */
$(document).ready(() => {
  const details = [
    "custom_trade_short_name", "custom_trade_specification",
    "custom_trade_model", "custom_trade_name_en",
  ];
  const requirement = "custom_trade_line_requirement_en";
  const priceInput = "custom_trade_price_input";
  const documents = [
    "Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice",
    "Sales Order", "Delivery Note", "Sales Invoice",
  ];

  async function renderInitialPrices(frm) {
    const field = frm.fields_dict[priceInput];
    if (!field) return;
    const show = frm.is_new() && frappe.model.can_create("Item Price") &&
      (frm.doc.is_sales_item || frm.doc.is_purchase_item);
    frm.toggle_display(priceInput, Boolean(show));
    if (!show) return;

    const item = frm.doc;
    const selling = item.is_sales_item;
    const buying = item.is_purchase_item;
    field.$wrapper.empty();
    const lists = await frappe.db.get_list("Price List", {
      fields: ["name", "currency", "selling", "buying"],
      filters: { enabled: 1 },
      or_filters: [
        ...(selling ? [["selling", "=", 1]] : []),
        ...(buying ? [["buying", "=", 1]] : []),
      ],
      order_by: "name asc",
      limit: 0,
    });
    if (item !== frm.doc || !frm.is_new() ||
        selling !== frm.doc.is_sales_item || buying !== frm.doc.is_purchase_item) return;

    const workbench = await window.hardware_workbench.context();
    if (item !== frm.doc || !frm.is_new() ||
        selling !== frm.doc.is_sales_item || buying !== frm.doc.is_purchase_item) return;
    const tiers = new Map(workbench.price_tiers.map(tier => [tier.name, tier]));
    lists.sort((a, b) => (tiers.get(a.name)?.number ?? Infinity) -
      (tiers.get(b.name)?.number ?? Infinity));
    const inputs = frm.tradePriceDrafts ||= new WeakMap();
    const draft = inputs.get(item) || Object.create(null);
    inputs.set(item, draft);
    frm.tradeActivePriceLists = lists.map(list => list.name);
    $("<p>", {class: "text-muted"}).text(
      "填写后随商品保存，按库存单位计价。留空的档位不生成价格记录。已保存商品可在本页维护价格。"
    ).appendTo(field.$wrapper);

    const container = $("<div>", {class: "trade-price-inputs"}).appendTo(field.$wrapper);
    for (const list of lists) {
      const label = $("<label>").text(`${tiers.get(list.name)?.label || __(list.name)}（${list.currency}）`).appendTo(container);
      $("<input>", {class: "form-control", type: "number", min: 0, step: "any"})
        .val(draft[list.name] ?? "")
        .on("input", function () { draft[list.name] = this.value; })
        .appendTo(label);
    }
  }

  frappe.ui.form.on("Item", {
    refresh(frm) {
      for (const [name, label] of Object.entries({
        item_code: "商品编号", item_name: "商品名称", item_group: "商品分类",
        stock_uom: "库存计量单位", is_stock_item: "库存商品", uoms: "多单位换算",
        brand: "品牌", valuation_method: "库存成本算法",
      })) {
        frm.set_df_property(name, "label", label);
      }
      return renderInitialPrices(frm);
    },
    is_sales_item: renderInitialPrices,
    is_purchase_item: renderInitialPrices,
    before_save(frm) {
      if (!frm.is_new()) return;
      const draft = frm.tradePriceDrafts?.get(frm.doc) || {};
      const active = frm.tradeActivePriceLists || [];
      frm.doc.trade_initial_prices = Object.fromEntries(
        active.filter(name => draft[name] !== undefined && draft[name] !== "")
          .map(name => [name, draft[name]])
      );
    },
  });

  frappe.ui.form.on("Customer", {
    refresh(frm) {
      frm.set_df_property("default_price_list", "description", "报价和销售开单时默认采用该价目表。");
    },
  });

  const previews = new WeakMap();

  function queueTradePreview(frm) {
    const doc = frm.doc;
    const state = previews.get(frm) || {};
    clearTimeout(state.timer);
    const request = {};
    state.request = request;
    previews.set(frm, state);
    renderTradeRows(frm);

    if (!frm.fields_dict.custom_trade_line_review || !doc.items?.some(row => row.item_code) ||
        (!frm.is_new() && !frm.is_dirty()) || doc.docstatus !== 0) return;

    state.timer = setTimeout(async () => {
      if (frm.doc !== doc || (!frm.is_new() && !frm.is_dirty())) return;
      const draft = {
        ...doc,
        name: frm.is_new() ? null : doc.name,
        items: doc.items.filter(row => row.item_code),
      };
      let result = null;
      try {
        const response = await frappe.call({
          method: "hardware_erp.trade_preview.preview",
          args: {draft},
          silent: true,
        });
        result = response.message;
      } catch {
        // Keep the rest of the native form usable when a draft is incomplete.
      }
      if (frm.doc === doc && state.request === request) {
        renderTradeRows(frm, result);
      }
    }, 300);
  }

  function renderTradeRows(frm, preview) {
    const field = frm.fields_dict.custom_trade_line_review;
    if (!field) return;
    const rows = (frm.doc.items || []).filter(row => row.item_code);
    const saved = !frm.is_new() && !frm.is_dirty();
    const scrollLeft = field.$wrapper.find(".trade-review-scroll").scrollLeft();
    field.$wrapper.empty();
    if (!rows.length) return;

    const taxByItem = new Map();
    const valuationTaxes = new Set((frm.doc.taxes || [])
      .filter(tax => tax.category === "Valuation").map(tax => tax.name));
    for (const detail of frm.doc.item_wise_tax_details || []) {
      if (!valuationTaxes.has(detail.tax_row)) {
        taxByItem.set(detail.item_row, (taxByItem.get(detail.item_row) || 0) + flt(detail.amount));
      }
    }

    const table = $("<table>", {class: "table table-bordered trade-review-table"});
    const header = $("<tr>").appendTo($("<thead>").appendTo(table));
    const headings = [
      "标记", "商品编号", "商品名称", "英文商品名称", "简称", "规格", "型号", "品牌", "仓库",
      "数量", "计量单位", "单位换算", "折扣率", "折扣额（每单位）", "折后不含税单价",
      "折后不含税金额", "税费率（折算）", "含税单价", "含税金额", "英文订单要求",
    ];
    for (const label of headings) $("<th>", {scope: "col"}).text(label).appendTo(header);
    const body = $("<tbody>").appendTo(table);
    const money = value => value == null ? "" : format_currency(value, frm.doc.currency);
    const percent = value => value == null ? "" : `${value}%`;
    for (const [index, row] of rows.entries()) {
      const live = preview?.rows[index];
      const tr = $("<tr>").appendTo(body);
      // Old documents use the original tax allocation when it is present.
      const tax = taxByItem.has(row.name) || !frm.doc.taxes?.length
        ? (taxByItem.get(row.name) || 0) / (flt(frm.doc.conversion_rate) || 1)
        : null;
      const net = flt(row.net_amount);
      const grossAmount = tax != null ? net + tax : (row.custom_trade_gross_amount || null);
      const grossRate = grossAmount != null && row.qty ? grossAmount / row.qty : null;
      const taxPercent = tax != null && net ? flt(tax * 100 / net, 4) : (row.custom_trade_tax_percent || null);
      const values = [
        row.custom_trade_line_mark, row.item_code, __(row.item_name || ""), row.custom_trade_name_en, row.custom_trade_short_name,
        row.custom_trade_specification, row.custom_trade_model, row.brand, row.warehouse,
        row.qty, __(row.uom || ""), row.conversion_factor, percent(row.discount_percentage),
        money(row.discount_amount), money(live?.net_rate ?? row.net_rate), money(live?.net_amount ?? row.net_amount),
        saved ? percent(taxPercent) : percent(live?.tax_percent),
        saved ? money(grossRate) : money(live?.gross_rate),
        saved ? money(grossAmount) : money(live?.gross_amount), row[requirement],
      ];
      for (const value of values) $("<td>").text(value ?? "").appendTo(tr);
    }
    $("<h6>").text("商品核对与金额明细").appendTo(field.$wrapper);
    if (!saved) {
      const message = preview
        ? `草稿预览　不含税合计 ${money(preview.net_total)}　税费 ${money(preview.tax_total)}　含税合计 ${money(preview.grand_total)}`
        : preview === null ? "当前草稿无法预览含税金额，可在保存后核对。" : "正在计算草稿含税金额…";
      $("<p>", {class: "text-muted", "aria-live": "polite"}).text(message).appendTo(field.$wrapper);
    }
    $("<div>", {class: "trade-review-scroll", tabindex: 0, "aria-label": "商品核对与金额明细"})
      .append(table).appendTo(field.$wrapper).scrollLeft(scrollLeft || 0);
  }

  for (const doctype of documents) {
    frappe.ui.form.on(doctype, {
      refresh(frm) {
        for (const [name, label] of Object.entries({
          buying_price_list: "采购价目表", selling_price_list: "报价档位", terms: "条款与附加说明",
          discount_amount: "整单折扣金额", additional_discount_percentage: "整单折扣率",
          apply_discount_on: "整单折扣计算基准", remarks: "备注",
        })) {
          if (frm.fields_dict[name]) frm.set_df_property(name, "label", label);
        }
        queueTradePreview(frm);
      },
      ...Object.fromEntries([
        "company", "currency", "conversion_rate", "transaction_date", "posting_date",
        "taxes_and_charges", "tax_category", "shipping_rule", "apply_discount_on",
        "additional_discount_percentage", "discount_amount", "ignore_pricing_rule", "grand_total",
      ].map(name => [name, queueTradePreview])),
    });
    frappe.ui.form.on(`${doctype} Item`, {
      async item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const code = row.item_code;
        const productField = "custom_trade_requirement_en";
        const item = code ? (await frappe.db.get_value("Item", code, [...details, productField])).message : null;
        if (row.item_code !== code || !frm.doc.items?.includes(row)) return;
        for (const name of details) row[name] = item?.[name] ?? null;
        row[requirement] = item?.[productField] ?? null;
        frm.refresh_field("items");
        queueTradePreview(frm);
      },
      ...Object.fromEntries([
        "qty", "uom", "warehouse", "rate", "discount_percentage", "discount_amount",
        "net_amount", "price_list_rate", "item_tax_template", "brand",
        "custom_trade_line_mark", requirement, "items_add", "items_remove",
      ].map(name => [name, queueTradePreview])),
    });
  }

  for (const doctype of ["Purchase Taxes and Charges", "Sales Taxes and Charges"]) {
    frappe.ui.form.on(doctype, Object.fromEntries([
      "rate", "tax_amount", "charge_type", "included_in_print_rate", "account_head",
      "row_id", "category", "add_deduct_tax", "taxes_add", "taxes_remove",
    ].map(name => [name, queueTradePreview])));
  }
});
