/* Native Desk extension: no business writes, role simulation or content replacement. */
(() => {
  if (frappe.boot?.lang === "zh" && frappe._messages) frappe._messages["Product Inventory"] = "库存状况表－商品库存";
  const escape = value => frappe.utils.escape_html(String(value ?? ""));
  const state = {context: null, pending: null};
  const disabled = () => sessionStorage.getItem("hardware-workbench-off") === "1";
  function context(force = false) {
    if (force) state.context = null;
    if (state.context) return Promise.resolve(state.context);
    if (!state.pending) {
      state.pending = Promise.resolve(frappe.call({method: "erpnext_zh.workbench.get_context"}))
        .then(r => state.context = r.message).finally(() => state.pending = null);
    }
    return state.pending;
  }
  function navigate(action) {
    if (frappe.get_route()[0] === "Form" && window.cur_frm?.is_dirty()) {
      return new Promise(resolve => frappe.confirm("有尚未保存的修改。确定放弃修改并离开？", () => resolve(action()), () => resolve(false)));
    }
    return action();
  }
  function go(item) {
    return navigate(() => {
      state.selected = item.id;
      // A report may still be writing its URL filters as the next view loads.
      // Enter each native report with its own URL and standard defaults.
      if (item.report) return window.location.assign("/desk/query-report/" + encodeURIComponent(item.report));
      if (item.single) return frappe.set_route("Form", item.doctype, item.doctype);
      // On first load the Desk list can replace route_options with saved filters.
      // Native deep links restore the explicit subtype even for numeric zero.
      if (Object.keys(item.filters || {}).length) {
        const slug = frappe.router.slug(item.doctype);
        return window.location.assign("/desk/" + slug + "/view/list?" + new URLSearchParams(item.filters));
      }
      frappe.route_options = {};
      return frappe.set_route("List", item.doctype, "List");
    });
  }
  function shell(data) {
    document.querySelector(".hw-nav")?.remove();
    document.querySelector(".hw-toggle")?.remove();
    document.body.classList.toggle("hw-enabled", !disabled());
    const toggle = document.createElement("button");
    toggle.className = "hw-toggle"; toggle.textContent = disabled() ? "中文工作台" : "业务导航";
    toggle.onclick = () => {
      if (disabled()) {sessionStorage.removeItem("hardware-workbench-off"); shell(data); frappe.set_route("hardware-workbench");}
      else document.body.classList.toggle("hw-menu-open");
    };
    document.body.append(toggle);
    if (disabled()) return;
    const nav = document.createElement("nav");
    nav.className = "hw-nav"; nav.setAttribute("aria-label", "业务导航");
    nav.innerHTML = `<div class="hw-brand"><b>五金业务工作台</b><small>采购 · 库存 · 销售 · 收付款</small></div><button class="hw-home">工作台</button>`;
    const tools = document.createElement("button");
    tools.textContent = "资料工具";
    tools.onclick = () => {navigate(() => frappe.set_route("hardware-data-tools")); document.body.classList.remove("hw-menu-open");};
    nav.append(tools);
    nav.querySelector(".hw-home").onclick = () => {navigate(() => frappe.set_route("hardware-workbench")); document.body.classList.remove("hw-menu-open");};
    data.groups.forEach(group => {
      const section = document.createElement("details"); section.dataset.group = group.id;
      const title = document.createElement("summary"); title.textContent = group.label; section.append(title);
      group.items.forEach(item => {
        const button = document.createElement("button"); button.textContent = item.label;
        button.dataset.item = item.id;
        button.onclick = () => {go(item); document.body.classList.remove("hw-menu-open"); highlight();};
        section.append(button);
      });
      nav.append(section);
    });
    const fallback = document.createElement("button"); fallback.className = "hw-fallback"; fallback.textContent = "返回原生导航";
    fallback.onclick = () => {sessionStorage.setItem("hardware-workbench-off", "1"); document.body.classList.remove("hw-menu-open"); shell(data);};
    nav.append(fallback); document.body.append(nav);
    const route = frappe.get_route();
    if (route[0] === "List" && window.cur_list?.doctype === route[1] && window.cur_list.filter_area) sync_list(window.cur_list);
    else if (route[0] === "Form" && window.cur_frm?.doctype === route[1]) sync_form(window.cur_frm);
    else highlight();
  }
  function highlight() {
    const route = frappe.get_route();
    const matches = state.context?.groups.flatMap(g => g.items).filter(i =>
      i.report ? route[0] === "query-report" && route[1] === i.report : ["List", "Form"].includes(route[0]) && route[1] === i.doctype) || [];
    // Avoid falsely labelling a return or a payment purpose after direct navigation/refresh.
    const selected = matches.find(i => i.id === state.selected) || (matches.length === 1 ? matches[0] : null);
    document.querySelectorAll(".hw-nav [data-item]").forEach(button => {
      const active = button.dataset.item === selected?.id;
      button.classList.toggle("active", active);
      if (active) {button.setAttribute("aria-current", "page"); button.parentElement.open = true;}
      else button.removeAttribute("aria-current");
    });
  }
  async function render(page) {
    const host = page.main.get ? page.main.get(0) : page.main;
    host.classList.add("hw-page");
    host.innerHTML = '<div class="hw-state" role="status">正在读取业务工作台…</div>';
    try {
      const data = await context(true); shell(data);
      host.innerHTML = `<section class="hw-intro"><div><h2>业务工作台</h2><p>从左侧选择业务，或直接打开下方单据与报表。</p></div><span>当前账号：${escape(data.user)}</span></section>
        <div class="hw-note">发票单据用于采购、销售记账，不代表已开具税务发票。退款请核对收付方向；退货从原单办理。</div>
        <section class="hw-actions"></section><section class="hw-grid"></section>
        <section class="hw-recent"><h3>近期修改的单据</h3><p>仅显示当前账号有权查看的记录，按修改时间排序。</p><div class="hw-table-wrap"><table><thead><tr><th>单据类型</th><th>单据编号</th><th>单据状态</th><th>最后修改</th></tr></thead><tbody></tbody></table></div></section>`;
      const tools = document.createElement("button");
      tools.className = "btn btn-default";
      tools.textContent = "资料工具";
      tools.onclick = () => frappe.set_route("hardware-data-tools");
      host.querySelector(".hw-actions").append(tools);
      if (data.can_view_actions) {
        const b = document.createElement("button"); b.className="btn btn-default"; b.textContent="查看审批任务";
        b.onclick=()=> {frappe.route_options={status:"Open"}; frappe.set_route("List","Workflow Action");};
        host.querySelector(".hw-actions").append(b);
      }
      if (!data.groups.length) host.querySelector(".hw-grid").textContent="当前账号暂无首版业务权限，请联系管理员。";
      data.groups.forEach(group => {
        const card = document.createElement("section"); card.className="hw-card";
        const h = document.createElement("h3"); h.textContent=group.label; card.append(h);
        group.items.forEach(item=> {
          const b=document.createElement("button"); b.textContent=item.label;
          b.onclick=()=>{go(item);}; card.append(b);
        }); host.querySelector(".hw-grid").append(card);
      });
      const tbody=host.querySelector("tbody");
      data.recent.forEach(doc=>{
        const tr=document.createElement("tr");
        tr.innerHTML=`<td>${escape(doc.label)}</td><td><button class="hw-doc">${escape(doc.name)}</button></td><td>${["草稿","已提交","已撤销"][doc.docstatus] || "—"}</td><td>${escape(frappe.datetime.str_to_user(doc.modified))}</td>`;
        tr.querySelector("button").onclick=()=> {navigate(() => {state.selected=null; return frappe.set_route("Form",doc.doctype,doc.name);});}; tbody.append(tr);
      });
      if (!data.recent.length) tbody.innerHTML='<tr><td colspan="4">暂无可查看的近期单据</td></tr>';
    } catch (error) {
      host.innerHTML='<div class="hw-state" role="alert">工作台加载失败。请检查登录状态与权限后重试。</div>';
      const retry=document.createElement("button"); retry.className="btn btn-default"; retry.textContent="重新加载"; retry.onclick=()=>render(page); host.append(retry);
    }
  }
  function sync_list(list) {
    const candidates = state.context?.groups.flatMap(group => group.items).filter(item => item.doctype === list.doctype) || [];
    const matches = candidates.filter(item => Object.entries(item.filters || {}).every(([field, value]) =>
      list.filter_area.get().some(([dt, key, operator, actual]) => dt === list.doctype && key === field && operator === "=" && String(actual) === String(value))));
    state.selected = matches.length === 1 ? matches[0].id : null;
    highlight();
    window.hardware_data_tools?.listActions(list, candidates[0]);
  }
  function sync_form(frm) {
    const matches = state.context?.groups.flatMap(group => group.items).filter(item =>
      item.doctype === frm.doctype && Object.entries(item.filters || {}).every(([field,value]) => String(frm.doc[field] ?? 0) === String(value))) || [];
    state.selected = matches.length === 1 ? matches[0].id : null;
    highlight();
    window.hardware_data_tools?.formActions(frm, matches[0]);
  }
  window.hardware_workbench={render, sync_list, sync_form, context, go};
  $(document).on("app_ready",()=>{
    context().then(shell).catch(()=>{/* Native Desk remains usable if workbench loading fails. */});
    frappe.router.on("change", highlight);
    document.addEventListener("keydown",event=>{if(event.key==="Escape") document.body.classList.remove("hw-menu-open");});
  });
})();
