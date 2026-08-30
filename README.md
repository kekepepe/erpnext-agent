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

下一步是在 ERPNext Desk 完成测试公司初始化，再准备约 20 个 SKU、3 个供应商和 3 个客户，按采购链与销售链逐项记录验证证据和 Gap。

## 来源

`phase0/compose.yaml` 基于 Frappe 官方 `frappe_docker` 的 `pwd.yml`（2026-08-30 获取），镜像固定到当时文件中的 `v16.33.0`。官方明确将该方式定位为快速探索和一次性演示环境。
