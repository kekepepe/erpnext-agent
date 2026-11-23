/**
 * 五金进销存 · 出入库录单业务逻辑
 */
(function () {
  'use strict';

  const API_PREFIX = '/api/business/v1';

  // 状态管理
  const state = {
    kind: 'purchase_receipt', // purchase_receipt | sales_delivery
    options: {
      companies: [],
      partners: [],
      warehouses: [],
      products: [],
      defaults: {},
      capabilities: {}
    },
    draft: {
      id: null,
      revision: null,
      companyId: '',
      partnerId: '',
      postingDate: '',
      lines: [] // [{ productId, warehouseId, quantity, ...read-only info }]
    },
    pendingSave: null,
    optionsReady: false,
    isDirty: false,
    loading: false
  };

  // DOM 元素引用
  const el = {
    tabPurchase: document.getElementById('tabPurchase'),
    tabSales: document.getElementById('tabSales'),
    partnerLabel: document.getElementById('partnerLabel'),
    companySelect: document.getElementById('companySelect'),
    partnerSelect: document.getElementById('partnerSelect'),
    postingDateInput: document.getElementById('postingDateInput'),
    lineTbody: document.getElementById('lineTbody'),
    addRowBtn: document.getElementById('addRowBtn'),
    saveDraftBtn: document.getElementById('saveDraftBtn'),
    newDraftBtn: document.getElementById('newDraftBtn'),
    alertBanner: document.getElementById('alertBanner'),
    statusBadge: document.getElementById('statusBadge'),
    docInfo: document.getElementById('docInfo'),
    form: document.getElementById('entryForm'),
    retryOptionsBtn: document.getElementById('retryOptionsBtn'),
    totalSummary: document.getElementById('totalSummary'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText')
  };

  function markDirty() {
    state.isDirty = true;
    updateStatusHeader();
  }

  function showLoading(text) {
    state.loading = true;
    el.form.inert = true;
    el.tabPurchase.disabled = el.tabSales.disabled = true;
    el.loadingText.textContent = text || '处理中...';
    el.loadingOverlay.classList.remove('hidden');
  }

  function hideLoading() {
    state.loading = false;
    el.form.inert = false;
    el.tabPurchase.disabled = el.tabSales.disabled = false;
    el.addRowBtn.disabled = el.newDraftBtn.disabled = !state.optionsReady;
    el.saveDraftBtn.disabled = !state.optionsReady || !state.options.capabilities?.saveDraft;
    el.loadingOverlay.classList.add('hidden');
  }

  function showAlert(msg, isSuccess = false) {
    el.alertBanner.textContent = msg;
    el.alertBanner.className = `alert-banner ${isSuccess ? 'alert-success' : 'alert-danger'}`;
    el.alertBanner.classList.remove('hidden');
    el.alertBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function hideAlert() {
    el.alertBanner.textContent = '';
    el.alertBanner.className = 'alert-banner hidden';
  }

  function updateStatusHeader() {
    if (state.draft.id) {
      el.statusBadge.textContent = state.isDirty ? '有未保存修改' : '已保存草稿';
      el.statusBadge.className = 'status-badge saved';
      el.docInfo.textContent = `${state.draft.id} · 版本 ${state.draft.revision}`;
      el.docInfo.hidden = false;
    } else {
      el.statusBadge.textContent = '新草稿';
      el.statusBadge.className = 'status-badge';
      el.docInfo.hidden = true;
    }
  }

  // 加载选项数据
  async function loadOptions(kind) {
    if (state.loading) return;
    state.optionsReady = false;
    el.retryOptionsBtn.classList.add('hidden');
    showLoading('正在加载录单选项…');
    hideAlert();
    try {
      const res = await fetch(`${API_PREFIX}/entry-options?kind=${encodeURIComponent(kind)}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      if (!res.ok) {
        throw new Error(`加载基础选项失败: HTTP ${res.status}`);
      }
      const json = await res.json();
      state.options = json.data || {};

      // 渲染公司与往来伙伴
      renderSelectOptions(el.companySelect, state.options.companies || [], '请选择公司');
      renderSelectOptions(el.partnerSelect, state.options.partners || [], state.kind === 'purchase_receipt' ? '请选择供应商' : '请选择客户');

      // 赋默认值
      if (!state.draft.id) {
        if (state.options.defaults) {
          if (state.options.defaults.companyId) {
            el.companySelect.value = state.options.defaults.companyId;
            state.draft.companyId = state.options.defaults.companyId;
          }
          if (state.options.defaults.postingDate) {
            el.postingDateInput.value = state.options.defaults.postingDate;
            state.draft.postingDate = state.options.defaults.postingDate;
          }
        }
      }

      // 如果当前没有行，则默认添加一行空行
      if (state.draft.lines.length === 0) {
        addNewRow(false);
      } else {
        renderLines();
      }
      state.optionsReady = true;
    } catch {
      showAlert('录单选项加载失败，请重新加载。');
      el.retryOptionsBtn.classList.remove('hidden');
    } finally {
      hideLoading();
    }
  }

  function renderSelectOptions(selectEl, list, placeholder) {
    selectEl.replaceChildren();
    const emptyOpt = document.createElement('option');
    emptyOpt.value = '';
    emptyOpt.textContent = `-- ${placeholder} --`;
    selectEl.appendChild(emptyOpt);

    list.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = item.label;
      selectEl.appendChild(opt);
    });
  }

  // 格式化产品展示文本
  function formatProductLabel(prod) {
    const parts = [prod.label];
    if (prod.englishName) parts.push(`(${prod.englishName})`);
    if (prod.id) parts.push(`[${prod.id}]`);
    return parts.join(' ');
  }

  // 行明细管理
  function addNewRow(focus = true) {
    if (state.draft.lines.length >= 100) {
      showAlert('一张草稿最多可录入 100 行。');
      return;
    }
    state.draft.lines.push({
      productId: '',
      warehouseId: state.options.warehouses?.[0]?.id || '',
      quantity: ''
    });
    renderLines();
    if (focus) el.lineTbody.lastElementChild.querySelector('.line-product').focus();
  }

  function removeRow(index) {
    if (state.draft.lines.length <= 1) {
      // 保持至少一行
      state.draft.lines[0] = {
        productId: '',
        warehouseId: state.options.warehouses[0]?.id || '',
        quantity: ''
      };
    } else {
      state.draft.lines.splice(index, 1);
    }
    renderLines();
    markDirty();
  }

  function updateTotals() {
    const count = state.draft.lines.filter(line => line.productId).length;
    el.totalSummary.textContent = `商品 ${count} 行`;
  }

  function renderLines() {
    el.lineTbody.replaceChildren();
    const products = state.options.products || [];
    const warehouses = state.options.warehouses || [];

    state.draft.lines.forEach((line, idx) => {
      const tr = document.createElement('tr');
      tr.dataset.index = idx;

      // 序号
      const tdSeq = document.createElement('td');
      tdSeq.className = 'col-seq text-center';
      tdSeq.textContent = String(idx + 1);
      tr.appendChild(tdSeq);

      // 产品选择
      const tdProd = document.createElement('td');
      tdProd.className = 'col-product';
      const selectProd = document.createElement('select');
      selectProd.className = 'table-select line-product';
      selectProd.dataset.field = 'productId';
      selectProd.dataset.index = idx;
      selectProd.setAttribute('aria-label', `第 ${idx + 1} 行商品`);

      const emptyProdOpt = document.createElement('option');
      emptyProdOpt.value = '';
      emptyProdOpt.textContent = '-- 请选择商品 --';
      selectProd.appendChild(emptyProdOpt);

      products.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = formatProductLabel(p);
        if (p.id === line.productId) opt.selected = true;
        selectProd.appendChild(opt);
      });
      tdProd.appendChild(selectProd);
      tr.appendChild(tdProd);

      // 查询当前选中的商品信息
      const currentProduct = products.find(p => p.id === line.productId);

      // 规格/型号 (只读)
      const tdSpec = document.createElement('td');
      tdSpec.className = 'col-spec';
      const spanSpec = document.createElement('span');
      spanSpec.className = 'read-only-cell line-spec';
      const specText = [currentProduct?.specification, currentProduct?.model].filter(Boolean).join(' / ') || '-';
      spanSpec.textContent = specText;
      spanSpec.title = specText;
      tdSpec.appendChild(spanSpec);
      tr.appendChild(tdSpec);

      // 单位 (只读)
      const tdUom = document.createElement('td');
      tdUom.className = 'col-uom text-center';
      const spanUom = document.createElement('span');
      spanUom.className = 'read-only-cell line-uom';
      spanUom.textContent = currentProduct?.uom || '-';
      tdUom.appendChild(spanUom);
      tr.appendChild(tdUom);

      // 仓库选择
      const tdWh = document.createElement('td');
      tdWh.className = 'col-warehouse';
      const selectWh = document.createElement('select');
      selectWh.className = 'table-select line-warehouse';
      selectWh.dataset.field = 'warehouseId';
      selectWh.dataset.index = idx;
      selectWh.setAttribute('aria-label', `第 ${idx + 1} 行仓库`);

      const emptyWhOpt = document.createElement('option');
      emptyWhOpt.value = '';
      emptyWhOpt.textContent = '-- 选择仓库 --';
      selectWh.appendChild(emptyWhOpt);

      warehouses.forEach(w => {
        const opt = document.createElement('option');
        opt.value = w.id;
        opt.textContent = w.label;
        if (w.id === line.warehouseId) opt.selected = true;
        selectWh.appendChild(opt);
      });
      tdWh.appendChild(selectWh);
      tr.appendChild(tdWh);

      // 数量输入
      const tdQty = document.createElement('td');
      tdQty.className = 'col-qty';
      const inputQty = document.createElement('input');
      inputQty.type = 'text';
      inputQty.inputMode = 'decimal';
      inputQty.className = 'table-input text-right line-quantity';
      inputQty.dataset.field = 'quantity';
      inputQty.dataset.index = idx;
      inputQty.setAttribute('aria-label', `第 ${idx + 1} 行数量`);
      inputQty.placeholder = '0.00';
      inputQty.value = line.quantity || '';
      tdQty.appendChild(inputQty);
      tr.appendChild(tdQty);

      // 操作
      const tdOp = document.createElement('td');
      tdOp.className = 'col-op text-center';
      const delBtn = document.createElement('button');
      delBtn.type = 'button';
      delBtn.className = 'btn-danger-link';
      delBtn.textContent = '删除';
      delBtn.setAttribute('aria-label', `删除第 ${idx + 1} 行`);
      delBtn.addEventListener('click', () => removeRow(idx));
      tdOp.appendChild(delBtn);
      tr.appendChild(tdOp);

      el.lineTbody.appendChild(tr);
    });

    updateTotals();
  }

  // 事件委托处理明细行更改与键盘快捷键
  el.lineTbody.addEventListener('change', function (e) {
    const target = e.target;
    const index = parseInt(target.dataset.index, 10);
    const field = target.dataset.field;
    if (isNaN(index) || !field) return;

    state.draft.lines[index][field] = target.value;
    target.classList.remove('input-error');

    if (field === 'productId') {
      // 联动商品只读字段
      const prod = state.options.products.find(p => p.id === target.value);
      const row = target.closest('tr');
      if (row) {
        const specSpan = row.querySelector('.line-spec');
        const uomSpan = row.querySelector('.line-uom');
        const specText = [prod?.specification, prod?.model].filter(Boolean).join(' / ') || '-';
        if (specSpan) {
          specSpan.textContent = specText;
          specSpan.title = specText;
        }
        if (uomSpan) {
          uomSpan.textContent = prod?.uom || '-';
        }
      }
    }

    markDirty();
    updateTotals();
  });

  el.lineTbody.addEventListener('input', function (e) {
    const target = e.target;
    if (target.dataset.field === 'quantity') {
      const index = parseInt(target.dataset.index, 10);
      if (!isNaN(index)) {
        state.draft.lines[index].quantity = target.value;
        target.classList.remove('input-error');
        markDirty();
        updateTotals();
      }
    }
  });

  el.lineTbody.addEventListener('keydown', function (e) {
    const target = e.target;
    if (!target.classList.contains('table-input') && !target.classList.contains('table-select')) return;

    if (e.key === 'Enter') {
      e.preventDefault();
      const currentIdx = parseInt(target.dataset.index, 10);
      if (target.dataset.field === 'quantity') {
        // 在最后一行的数量回车时自动增加一行
        if (currentIdx === state.draft.lines.length - 1) {
          addNewRow();
        } else {
          // 聚焦下一行的产品
          const nextRow = el.lineTbody.querySelector(`tr[data-index="${currentIdx + 1}"]`);
          if (nextRow) {
            const nextInput = nextRow.querySelector('.line-product');
            if (nextInput) nextInput.focus();
          }
        }
      } else if (target.dataset.field === 'productId') {
        const row = target.closest('tr');
        const whSelect = row.querySelector('.line-warehouse');
        if (whSelect) whSelect.focus();
      } else if (target.dataset.field === 'warehouseId') {
        const row = target.closest('tr');
        const qtyInput = row.querySelector('.line-quantity');
        if (qtyInput) qtyInput.focus();
      }
    }
  });

  // 单据头字段监听
  el.companySelect.addEventListener('change', function () {
    state.draft.companyId = this.value;
    this.classList.remove('input-error');
    markDirty();
  });

  el.partnerSelect.addEventListener('change', function () {
    state.draft.partnerId = this.value;
    this.classList.remove('input-error');
    markDirty();
  });

  el.postingDateInput.addEventListener('change', function () {
    state.draft.postingDate = this.value;
    this.classList.remove('input-error');
    markDirty();
  });

  // 模式切换 (采购入库 / 销售出库)
  function switchMode(kind) {
    if (state.loading || state.kind === kind || !canDiscardEdits()) return;
    state.kind = kind;

    if (kind === 'purchase_receipt') {
      el.tabPurchase.classList.add('active');
      el.tabPurchase.setAttribute('aria-pressed', 'true');
      el.tabSales.classList.remove('active');
      el.tabSales.setAttribute('aria-pressed', 'false');
      el.partnerLabel.textContent = '供应商 ';
    } else {
      el.tabSales.classList.add('active');
      el.tabSales.setAttribute('aria-pressed', 'true');
      el.tabPurchase.classList.remove('active');
      el.tabPurchase.setAttribute('aria-pressed', 'false');
      el.partnerLabel.textContent = '客户 ';
    }
    const reqSpan = document.createElement('span');
    reqSpan.className = 'req';
    reqSpan.textContent = '*';
    el.partnerLabel.appendChild(reqSpan);

    // 切换模式显式重置单据 ID 与幂等键
    resetDraftState(false);
    renderSelectOptions(el.partnerSelect, [], '加载中');
    loadOptions(kind);
  }

  el.tabPurchase.addEventListener('click', () => switchMode('purchase_receipt'));
  el.tabSales.addEventListener('click', () => switchMode('sales_delivery'));

  // 显式重置新草稿
  function canDiscardEdits() {
    return !state.isDirty || window.confirm('当前草稿有未保存的内容，确定离开吗？');
  }

  function resetDraftState(addRow = true) {
    state.draft.id = null;
    state.draft.revision = null;
    state.draft.companyId = state.options.defaults?.companyId || '';
    state.draft.partnerId = '';
    state.draft.postingDate = state.options.defaults?.postingDate || new Date().toISOString().slice(0, 10);
    state.draft.lines = [];
    state.pendingSave = null;
    state.isDirty = false;

    el.companySelect.value = state.draft.companyId;
    el.partnerSelect.value = '';
    el.postingDateInput.value = state.draft.postingDate;

    // 清除校验样式
    document.querySelectorAll('.input-error').forEach(node => node.classList.remove('input-error'));

    updateStatusHeader();
    hideAlert();
    if (addRow) addNewRow();
    else renderLines();
  }

  el.newDraftBtn.addEventListener('click', () => {
    if (canDiscardEdits()) resetDraftState();
  });

  el.retryOptionsBtn.addEventListener('click', () => loadOptions(state.kind));
  el.form.addEventListener('submit', event => event.preventDefault());

  el.addRowBtn.addEventListener('click', () => addNewRow());

  // 保存草稿
  async function saveDraft() {
    if (state.loading || !state.optionsReady || !state.options.capabilities?.saveDraft) return;
    hideAlert();
    document.querySelectorAll('.input-error').forEach(node => node.classList.remove('input-error'));

    // 前端基础完整性检查
    let hasClientError = false;
    const clientErrors = [];

    if (!el.companySelect.value) {
      el.companySelect.classList.add('input-error');
      clientErrors.push('所属公司不能为空');
      hasClientError = true;
    }
    if (!el.partnerSelect.value) {
      el.partnerSelect.classList.add('input-error');
      const roleText = state.kind === 'purchase_receipt' ? '供应商' : '客户';
      clientErrors.push(`${roleText}不能为空`);
      hasClientError = true;
    }
    if (!el.postingDateInput.value) {
      el.postingDateInput.classList.add('input-error');
      clientErrors.push('单据日期不能为空');
      hasClientError = true;
    }

    const inputRows = state.draft.lines
      .map((line, index) => ({ line, index }))
      .filter(({ line }) => line.productId || line.quantity);
    if (inputRows.length === 0) {
      clientErrors.push('请至少添加一行商品明细');
      hasClientError = true;
    } else {
      inputRows.forEach(({ line, index: idx }) => {
        const rowEl = el.lineTbody.querySelector(`tr[data-index="${idx}"]`);
        if (!line.productId) {
          clientErrors.push(`第 ${idx + 1} 行商品未选择`);
          hasClientError = true;
          if (rowEl) rowEl.querySelector('.line-product')?.classList.add('input-error');
        }
        if (!line.warehouseId) {
          clientErrors.push(`第 ${idx + 1} 行仓库未选择`);
          hasClientError = true;
          if (rowEl) rowEl.querySelector('.line-warehouse')?.classList.add('input-error');
        }
        if (!/^(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,6})?$/.test(line.quantity)
            || !/[1-9]/.test(line.quantity)) {
          clientErrors.push(`第 ${idx + 1} 行数量须大于零，整数最多九位，小数最多六位`);
          hasClientError = true;
          if (rowEl) rowEl.querySelector('.line-quantity')?.classList.add('input-error');
        }
      });
    }

    if (hasClientError) {
      showAlert(`录入校验未通过: ${clientErrors[0]}`);
      return;
    }

    // 构建提交负载
    const payload = {
      kind: state.kind,
      companyId: el.companySelect.value,
      partnerId: el.partnerSelect.value,
      postingDate: el.postingDateInput.value,
      lines: inputRows.map(({ line: l }) => ({
        productId: l.productId,
        warehouseId: l.warehouseId,
        quantity: String(l.quantity)
      }))
    };

    const isUpdate = Boolean(state.draft.id);
    let url = `${API_PREFIX}/drafts`;
    let method = 'POST';

    if (isUpdate) {
      url = `${API_PREFIX}/drafts/${encodeURIComponent(state.draft.id)}`;
      method = 'PUT';
      payload.revision = state.draft.revision || 1;
    }

    const body = JSON.stringify(payload);
    if (state.pendingSave?.body !== body) {
      state.pendingSave = { body, key: crypto.randomUUID() };
    }

    showLoading(isUpdate ? '正在更新草稿...' : '正在保存新草稿...');

    try {
      const res = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Idempotency-Key': state.pendingSave.key
        },
        body
      });

      const json = await res.json().catch(() => null);

      if (res.ok && json && json.data) {
        // 保存成功
        state.draft.id = json.data.id;
        state.draft.revision = json.data.revision;
        state.draft.companyId = json.data.companyId;
        state.draft.partnerId = json.data.partnerId;
        state.draft.postingDate = json.data.postingDate;
        state.draft.lines = json.data.lines || payload.lines;
        state.isDirty = false;
        state.pendingSave = null;

        updateStatusHeader();
        renderLines();
        showAlert('草稿已保存。', true);
      } else {
        // 接口报错处理 (例如 409 或 400/422 等)
        handleServerError(res.status, json, inputRows);
      }
    } catch {
      showAlert('保存响应中断，当前录入内容已保留。可再次保存重试。');
    } finally {
      hideLoading();
    }
  }

  function handleServerError(status, json, inputRows) {
    const errorInfo = json && json.error ? json.error : {};
    let errorMsg = errorInfo.message || `请求失败 (HTTP ${status})`;

    // 高亮问题字段
    if (Array.isArray(errorInfo.issues)) {
      errorInfo.issues.forEach(issue => {
        if (!issue.path) return;
        const parts = issue.path.split('.');
        if (parts[0] === 'companyId') el.companySelect.classList.add('input-error');
        if (parts[0] === 'partnerId') el.partnerSelect.classList.add('input-error');
        if (parts[0] === 'postingDate') el.postingDateInput.classList.add('input-error');
        if (parts[0] === 'lines' && parts.length >= 3) {
          const rowIdx = inputRows[Number(parts[1])]?.index;
          const field = parts[2];
          const rowEl = el.lineTbody.querySelector(`tr[data-index="${rowIdx}"]`);
          if (rowEl) {
            if (field === 'productId') rowEl.querySelector('.line-product')?.classList.add('input-error');
            if (field === 'warehouseId') rowEl.querySelector('.line-warehouse')?.classList.add('input-error');
            if (field === 'quantity') rowEl.querySelector('.line-quantity')?.classList.add('input-error');
          }
        }
      });
      if (errorInfo.issues[0]?.message) {
        errorMsg += ` - ${errorInfo.issues[0].message}`;
      }
    }

    if (status === 409) {
      showAlert(`${errorMsg} 当前录入内容已保留。`);
    } else {
      showAlert(`保存失败: ${errorMsg}`);
    }
  }

  el.saveDraftBtn.addEventListener('click', saveDraft);

  // 初始化入口
  function init() {
    updateStatusHeader();
    loadOptions(state.kind);
  }

  init();
})();
