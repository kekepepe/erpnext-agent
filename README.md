# ERPNext Agent

本目录当前用于五金贸易 ERP 项目的 **Phase 0：ERPNext 原生能力验证**。

当前只建立可丢弃的 ERPNext v16 测试环境，用于验证商品、采购、库存、销售和应收应付链路。这里不是生产部署，也不是 Custom App 开发环境。

## 当前基线

- ERPNext / Frappe：`v16.33.0` 官方镜像
- MariaDB：`11.8`
- Redis：`6.2-alpine`
- 入口：<http://localhost:8080>
- 测试站点：`frontend`
- 本地测试账号：`Administrator` / `admin`

测试凭据来自 Frappe 官方 disposable demo 配置，只允许用于本机 Phase 0。不得复用于 staging 或 production。

## 启动

```bash
docker compose -f phase0/compose.yaml up -d
./scripts/phase0-check.sh
```

首次启动需要拉取镜像并创建 Site，通常需要几分钟。查看进度：

```bash
docker compose -f phase0/compose.yaml logs -f create-site
```

## 初始化 Phase 0 合成数据

健康检查通过后，运行幂等初始化脚本：

```bash
python3 scripts/phase0-seed.py
```

脚本读取 `phase0/synthetic-data.json`，通过 ERPNext REST API 创建带 `P0` 前缀的纯合成公司、仓库、供应商、客户、20 个代表性物料、买卖价格和期初库存。重复运行只核对已有数据，不重复创建期初库存单。

如需覆盖本机地址或测试登录信息，可使用 `PHASE0_BASE_URL`、`PHASE0_USERNAME` 和 `PHASE0_PASSWORD` 环境变量。只允许使用本机 disposable Phase 0 凭据，不得传入或记录生产凭据。

## 验证采购流程

主数据初始化且健康检查通过后，运行：

```bash
python3 scripts/phase0-validate-purchase.py
```

脚本读取 `phase0/purchase-validation.json`，通过 ERPNext 原生 REST API 和白名单映射方法验证采购订单、完整及分批收货、替代 UOM、采购发票、应付、全额及部分付款和采购退货。场景使用独立的 P0 合成供应商与物料；重复运行会读取并核验已有单据，不重复提交交易。

## 验证库存流程

采购流程验证完成后，运行：

```bash
python3 scripts/phase0-validate-stock.py
```

脚本读取 `phase0/stock-validation.json`，通过 ERPNext 原生 REST API 核验期初库存，并验证交货出库、跨仓调拨、库存盘点调整、零库存查询和负库存拦截。重复运行会读取并核验已有单据，不重复提交库存交易。

## 停止

保留测试数据：

```bash
docker compose -f phase0/compose.yaml down
```

彻底删除 Phase 0 测试数据：

```bash
docker compose -f phase0/compose.yaml down -v
```

`down -v` 会删除 Site、数据库和队列数据，只应在明确要重建一次性测试环境时执行。

## 验证边界

当前阶段不要：

- 修改 ERPNext Core；
- 创建未经 Gap Analysis 证明必要的 Custom Field / Custom DocType；
- 创建 Agent、MCP Server 或让 Agent 直接访问数据库；
- 把本 Compose 文件当作生产部署方案。

测试公司和代表性主数据已经初始化，采购和库存流程验证已经完成。后续应继续按 `docs/PHASE0_VALIDATION.md` 验证销售、应收、权限、审批和报表场景，并记录证据与 Gap。

## 来源

`phase0/compose.yaml` 基于 Frappe 官方 `frappe_docker` 的 `pwd.yml`（2026-08-30 获取），镜像固定到当时文件中的 `v16.33.0`。官方明确将该方式定位为快速探索和一次性演示环境。
