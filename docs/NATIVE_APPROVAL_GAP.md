# N2 原生审批边界证据及最小修复提案

2026-10-11；R1-scope-v1.1 / R1-09、R1-10；处置 **所有者已批准，最小守卫合成技术验收完成**。

## 已执行的结果

在本机可丢弃站点、`R1合成发布验证公司`，临时给原有采购订单 Workflow 加入条件：人民币、总额 0–10,000、创建人与审批人不同；其他公司的原审批分支保留。测试使用既有 P0 合成采购经办和经理，均不是 Administrator/System Manager。运行版本 Frappe 16.31.0 / ERPNext 16.33.0。

| 调用 | 预期 | 两轮实际 |
|---|---|---|
| 经理正常 `apply_workflow`，10,000 | 可批准 | 已批准 |
| 经理正常 `apply_workflow`，10,000.01 | 不可直接批准 | 拒绝，WorkflowTransitionError |
| 经理一次 REST PUT 将 10,000 改价至 10,000.01，同时设置 Approved/docstatus=1 | 拒绝，重新分级审批 | 成功提交 10,000.01 |
| 经理 `frappe.client.submit` 10,000.01，仍携带 Pending | 拒绝 | 自动成为 Approved/docstatus=1 |
| 创建人 `frappe.client.submit` 自己的 10,000.01 Pending 单据 | 拒绝 | 创建人自行提交成功 |
| 用原生 Property Setter 将 items 置于无写权限的 permlevel=2，再由经理直接提交未修改的 10,000.01 | 拒绝 | 仍成功提交 |

这是采购订单的实测阻断，不声称销售/付款/库存同类路径已经测试。不是生产漏洞披露，也不是完整最小权限包通过。

原生字段权限另一次隔离试验能把经理的 items 改价还原为原来的 10,000；默认 Purchase Manager 已有 permlevel=1 写权限，所以必须使用不同权限级别。字段保护有作用，但不能使“不改任何业务字段、直接提交”遵守审批状态。删除经办 submit 权限能限制经办直接提交；经理正常低额批准本身也需要 write/submit，因此只删除经理 submit 会同时破坏正常批准。此后仍须在角色配置中取消经办提交、删除和共享等多余权限，不能仅靠守卫代替最小权限。

## 当前运行源码解释

只读检查容器中的原生源码，没有查询数据库或修改源码：

- `frappe/model/workflow.py:validate_workflow` 仅在前后 Workflow State 不同时校验转移；条件读取 `_doc_before_save`，不能据此保证同一次请求提交的新金额符合阈值。
- `frappe/model/document.py:validate_workflow` 校验后调用 `set_workflow_state_on_action`，提交会自动选取 doc_status=1 的状态。
- `frappe/client.py:submit` 直接构建文档并调用 `doc.submit()`，与正常 Workflow 提交使用同一文档权限。
- 单纯隐藏按钮、锁定表格、限定正常 Workflow 动作，不能替代服务器上的状态/金额/自审批校验。

## 重放和恢复

```bash
.venv/bin/python scripts/phase0-probe-approval.py
.venv/bin/python scripts/phase0-probe-approval.py --exercise --output /private/tmp/r1-n2-probe.json
```

第一条只读取配置。第二条明确写入合成采购订单，每次新增六个订单编号；**不具备交易编号幂等性**，不可用作日常启动或生产检查。退出码 2 表示成功复现发布阻断，并非验收通过。保存证据见 `phase0/evidence/n2-native-approval-20261011.json`，两轮结果一致。

执行前拒绝非 localhost:8080、缺失/变更的 P0 Workflow、已有 items 权限覆盖或异常测试身份。临时 Workflow 备份写入 /private/tmp。finally 撤销已提交测试订单、删除未提交测试草稿、删除本次临时 Property Setter，并恢复/核对原 Workflow 配置；已撤销订单保留原生审计。此探针不产生采购发票、库存或 GL 凭证。强制终止进程不能保证 finally 执行，故仅用于可丢弃环境；中断后按输出的备份路径恢复 Workflow，并检查本轮合成单据状态，再运行原回归。不要执行 `down -v`。

## 已批准的最小范围变更提案（2026-10-12 批准并实施）

建议把已证实的 Must 审批缺口作为 N2 必要依赖，纳入一个独立、最小 `hardware_erp` 应用中的文档事件校验；不改 ERPNext/Frappe Core，不建立外部 API/MCP/Agent，也不把业务守卫混入中文展示应用。

1. 对配置范围内的单据，在 save/submit/cancel 的服务器入口校验前后状态、目标 docstatus、执行人角色、创建人及独立复核身份。直接 submit/cancel 必须满足批准/撤销转移，不能依赖事后自动状态赋值。
2. 在审批时校验本次将保存的币种、含税金额/付款绝对金额和阈值；审批与业务金额、公司、往来方、仓库或税费等改动同时发生时拒绝，要求重新提交审批。高额订单需经理后由负责人复核。
3. 继续以原生 Workflow、Role、User Permissions 承载流程和公司/仓库权限；应用只补齐已证实的入口校验。真实税率、用户、公司、科目不进入公开仓库。
4. 先复测本证据的六条路径，再覆盖 10,000/10,000.01、20,000/20,000.01、自审批、跨公司/仓库、退货/撤销、身份或金额篡改和正常审批链；分别验证原生 REST、白名单 submit/cancel、正常/批量 Workflow 路径。其他单据的保护必须以实际扩展测试为验收，不推断已通过。
5. 应用关闭/卸载不能成为生产审批绕过开关。部署前校验应用、Workflow、角色和权限基线全部存在；配置漂移阻断上线。回滚时先停业务写入并恢复受控配置，再执行回归。

批准后记录 R1 范围修订和架构决策，再实施 N2 依赖；完成 N2 后按序做 N3 PDF/实时通信及 N4 SOP。未批准前维持现有 Phase 0 配置，不把试验条件作为发布配置启用。

所有者已选择“批准最小审批守卫”。DEC-012 和 R1-scope-v1.1 已记录授权，不再需要重复确认此提案。后续分级/库存/退货/撤销验收必须基于最终守卫及原生配置执行。旧六条探针仅适用于原三态配置；N2 配置后使用 `phase0-validate-release-access.py`，不要撤掉新 Workflow 来跑旧探针。

## 修复验收 — 2026-10-12

独立 `hardware_erp`0.1.0 通过最终 24 案例验收，正常九类 Workflow 及原生实物/财务链保留；直接提交/撤销、审批或撤销时改价、客户端 save/flags、公司切换、双角色自审批均被拒绝。高额经理→独立负责人、库存/商业→独立财务、退回重填和盘点 Version 验证通过。最终扩大一轮67检查，再次复用一轮54检查、created[]；具体审计见 `phase0/evidence/n2-access-runtime.json`，技术汇总见 `P09_ACCEPTANCE.md`。原生 gap 的两轮失败证据保留，不能把旧探针带入新工作流。干净环境安装/生命周期、真实角色与业务 UAT 仍在 C0/A1。
