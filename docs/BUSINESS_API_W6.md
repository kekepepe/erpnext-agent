# W6 出入库试点 Business API v1

按 DEC-016、DEC-020、DEC-022，先用采购入库和销售出库验证中文表格录单。契约涵盖基础选项、创建草稿、回读和更新草稿。本机演示服务使用合成数据，草稿保存在进程内，重启后清空。正式数据、库存过账、审批、金额、取价、原单匹配和结算留待各自的验收范围明确后实现。

## 本地联调与 ERPNext 适配入口

- **合成演示服务**：在仓库根目录运行 `python3 scripts/phase0-pilot-api.py`，打开 <http://127.0.0.1:8093/>。端口被占用时用 `--port` 指定其他端口。运行 `python3 -m unittest discover -s scripts -p 'test_pilot_api.py'` 可重跑合成契约测试。
- **ERPNext 正式适配**：启动本地中文工作台（`./scripts/phase0-workbench-start.sh`）后，登录系统账号打开 <http://localhost:8080/w6-entry>，页面通过同源 `/api/business/v1` 调用 `hardware_erp.business_api.dispatch`，写入附带 `X-Frappe-CSRF-Token`。运行 `.venv/bin/python scripts/phase0-validate-w6-adapter.py` 可重跑实站权限、仓库隔离、并发幂等、版本冲突与零过账验收；运行 `.venv/bin/python -m unittest scripts/test_business_api.py` 可跑离线单测。

## 请求与返回

路径前缀是 `/api/business/v1`。单据类型为 `purchase_receipt`（采购入库）或 `sales_delivery`（销售出库）。正式适配器的身份及岗位来自服务端会话。当前服务提供单一合成身份和公司。

| 方法与路径 | 用途 | 成功响应 |
|---|---|---|
| GET `/entry-options?kind=purchase_receipt` | 获取当前用户可选的公司、往来单位、仓库、商品和录单能力。销售出库传 `sales_delivery` | 200，选项对象 |
| POST `/drafts` | 创建普通出入库草稿，请求头带 `Idempotency-Key` | 201，草稿对象 |
| GET `/drafts/{id}` | 回读可访问的草稿 | 200，草稿对象 |
| PUT `/drafts/{id}` | 更新草稿。发送完整表单、当前 `revision` 和 `Idempotency-Key` | 200，草稿对象 |

成功响应包装为 `{"data": ...}`。选项对象包含：

- `companies`、`partners`、`warehouses` 为 `{id, label}` 数组。两种单据分别返回供应商和客户。
- `products` 为 `{id, label, englishName, specification, model, uom}` 数组。规格、型号、单位按商品回显。
- `defaults` 含 `companyId`、`postingDate`。`capabilities.saveDraft` 指示当前用户是否可保存。

创建请求示例。

```json
{
  "kind": "purchase_receipt",
  "companyId": "demo-company",
  "partnerId": "demo-supplier-01",
  "postingDate": "2026-11-23",
  "lines": [
    {"productId": "DEMO-BOLT-01", "warehouseId": "demo-warehouse-main", "quantity": "12"}
  ]
}
```

日期采用 `YYYY-MM-DD`。数量为正十进制字符串，最多九位整数及六位小数。每张草稿支持 1–100 行。返回对象包含原字段与 `id`、`revision`、`status: "draft"`。首次保存版本为 1，每次有效更新递增。前端应将 ID 当作不透明字符串。

同一会话对同一操作和目标，以同一个键重试同一内容会得到首次响应。表单内容改变后应使用新键。服务端在执行版本判断前检查重试记录，避免成功写入后响应丢失引发冲突。同键异内容、修改单据类型或版本过期返回 409。收到版本冲突时保留用户输入并提示核对最新草稿。

错误包装为 `{"error":{"code":"VALIDATION_ERROR","message":"请修正录单内容。","issues":[{"path":"lines.0.quantity","message":"数量须大于零。"}]}}`。行索引从零开始。400 为请求或保存标识无效，401 为未登录，403 为权限或会话校验拒绝，404 为草稿不可访问或不存在，409 为重试或版本冲突，422 为字段校验失败。413 和 415 分别表示请求过大或内容类型错误。

## ERPNext 适配验收

- 使用同源登录会话承载真实操作员身份，写入校验 CSRF。服务端按同一岗位配置计算可见、可编辑和可执行权限，并应用 ERPNext 原生公司、仓库及单据权限。拒绝时避免泄露范围外的单据或字段值。
- 两种单据在适配器内部分别映射 `Purchase Receipt` 与 `Delivery Note`。保存走原生草稿验证，原生数据权限与工作流守卫继续生效。提交、撤销、退货、账务及实际过账没有 v1 入口。
- 在同一事务内核验权限、版本并持久化草稿与幂等结果。幂等记录按真实操作者、操作、目标及键隔离，保留请求摘要。审计保留操作者、时间、操作、单据 ID 和结果，业务载荷留在 ERP。
- 用隔离站验证原生权限拒绝、仓库越权拒绝、并发修订、重试无重复单、草稿保存不写库存流水或总账。后续用岗位试录确认来源订单、实际高频单据和首发范围。
