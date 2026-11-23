/* U1 field vocabulary, scoped to reviewed native fields. Values and IDs are untouched. */
$(document).ready(() => {
  if (frappe.boot.lang !== "zh") return;
  const trade = ["Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Sales Order", "Delivery Note", "Sales Invoice"];
  const shared = {currency:"币种", items:"商品明细", grand_total:"含税总额", net_total:"净额", total_taxes_and_charges:"税费合计", rounded_total:"舍入后金额", rounding_adjustment:"舍入调整", workflow_state:"审批状态", terms:"条款说明"};
  const purchase = {transaction_date:"订单日期", schedule_date:"要求到货日期", set_warehouse:"默认收货仓库", status:"执行状态", per_received:"入库进度"};
  const children = {item_code:"商品编码", item_name:"商品名称", description:"商品说明", qty:"数量", uom:"计量单位", stock_uom:"库存单位", conversion_factor:"单位换算", rate:"成交单价", amount:"成交金额",
    brand:"品牌", warehouse:"仓库", price_list_rate:"价目表单价", discount_percentage:"折扣率",
    discount_amount:"折扣额（每单位）", net_rate:"折后不含税单价", net_amount:"折后不含税金额"};
  function labels(frm, mapping) {
    for (const [field, label] of Object.entries(mapping)) {
      if (frm.fields_dict[field]) frm.set_df_property(field, "label", label);
    }
  }
  for (const dt of [
    ...trade, "Payment Entry", "Stock Entry", "Stock Reconciliation",
    "Item", "Item Group", "Customer", "Supplier", "Warehouse", "UOM", "Item Price", "Price List",
  ]) {
    frappe.ui.form.on(dt, {
      refresh(frm) {
        window.hardware_workbench?.sync_form(frm);
        if (trade.includes(dt)) {
          labels(frm,shared);
          if (dt === "Purchase Order") labels(frm,purchase);
          if (dt === "Delivery Note") {
            labels(frm,{issue_credit_note:"办理销售贷项",return_against:"原销售出库单"});
            frm.set_df_property("issue_credit_note","description","用于退货账务处理，不表示已经退还资金。");
          }
          const grid = frm.fields_dict.items?.grid;
          if (grid) {
            const mapping = dt === "Purchase Order" ? {...children,schedule_date:"要求到货日期",warehouse:"收货仓库"} : children;
            for (const [field,label] of Object.entries(mapping)) {
              if (grid.docfields.some(df=>df.fieldname===field)) grid.update_docfield_property(field,"label",label);
            }
          }
        }
        if (frm.doc.docstatus === 2 && frm.doc.workflow_state === "Rejected") frm.page.set_indicator("已撤销","red");
        if (["Purchase Invoice","Sales Invoice"].includes(dt)) {
          frm.set_intro("本单用于记录采购应付或销售应收，本系统不办理税务开票。退货时请核对是否同时更新库存，避免重复出入库。","blue");
        } else if (dt === "Delivery Note" && frm.doc.is_return) {
          frm.set_intro("本单记录实物退货；销售贷项和资金退款分别办理，请核对原销售出库单。","blue");
        } else if (dt === "Payment Entry") {
          frm.set_intro("收款：客户付款或供应商退款。付款：支付供应商或退还客户。资金转账：企业内部账户划转。请核对往来单位与关联单据。","blue");
        }
      }
    });
  }
});
