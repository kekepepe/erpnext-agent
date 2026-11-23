export const roles={maker:'采购经办 · 小林',manager:'采购经理 · 陈经理',owner:'业务负责人 · 王总',stock:'库存经办 · 小周'};
export const suppliers=['示例·恒信紧固件','示例·远山五金','示例·启明工具'];
export const catalog=[{code:'HW-001',name:'六角螺栓',desc:'M10 × 50 · 镀锌',unit:'盒',price:85},{code:'HW-002',name:'不锈钢平垫圈',desc:'M10 · 304不锈钢',unit:'袋',price:28},{code:'HW-003',name:'工业切割片',desc:'125 × 1.2mm',unit:'箱',price:320}];
export const seed=()=>['pending','approved','review','approved','cancelled','pending','approved'].map((state,i)=>({id:`DEMO-PO-2026-${String(i+1).padStart(4,'0')}`,supplier:suppliers[i%3],date:`2026-10-${28-i}`,due:'2026-11-03',state,owner:i===5?'manager':'maker',progress:i===1?40:i===3?100:0,lines:[{...catalog[i%3],qty:i===2?500:10+i*3}],terms:'到货后核对数量与商品说明。',events:[{text:'创建采购订单',who:'采购经办',time:'2026-10-28 09:00'}]}));
export const amount=o=>Math.round(o.lines.reduce((n,l)=>n+l.price*l.qty,0)*100)/100;
export const money=n=>n.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
export const labels={pending:'待审批',review:'待负责人复核',approved:'已批准',cancelled:'已撤销'};
export const modules={'基础资料':['商品档案','客户','供应商','仓库','计量单位','商品价格'],'采购':['采购订单','采购入库单','采购退货'],'销售':['报价单','销售订单','销售出库单','销售退货'],'库存':['库存余额表','库存流水账','调拨单','库存盘点调整单'],'收付款':['收款单','付款单','资金转账单'],'报表':['库存余额表','库存流水账','采购分析表','销售分析表','应收账款表','应付账款表','总账'],'系统设置':['用户与权限','审批流程','打印设置']};
