# ERPNext Agent

本目录当前用于五金贸易 ERP 项目的 **Phase 0：ERPNext 原生能力验证**。

当前使用可丢弃的 ERPNext v16 测试环境，验证商品、采购、库存、销售和应收应付链路；另有已获用户授权的轻量中文展示扩展，不改核心或业务规则。这里不是生产部署。

## 当前基线

- ERPNext / Frappe：`v16.33.0` 官方镜像
- MariaDB：`11.8`
- Redis：`6.2-alpine`
- 入口：<http://localhost:8080>
- 测试站点：`frontend`
- 本地测试账号：`Administrator` / `admin`

测试凭据来自 Frappe 官方 disposable demo 配置，只允许用于本机 Phase 0。不得复用于 staging 或 production。

## 启动现有中文工作台

```bash
python3 -m venv .venv
.venv/bin/pip install -r phase0/localization/requirements.txt
./scripts/phase0-workbench-start.sh
./scripts/phase0-check.sh
```

上述工作台脚本用于已有的本地 Site，会构建镜像并迁移，不负责从空卷创建站点。全新隔离验证使用 `./scripts/phase0-validate-lifecycle.sh`，在独立项目和 18081 端口建站；请先确认该端口未被其他演练占用，保留旧卷。查看现有站点服务进度：

```bash
docker compose -f phase0/compose.yaml -f phase0/compose.zh.yaml -f phase0/compose.workbench.yaml logs -f backend
```

## W6 出入库录单试点

运行 `python3 scripts/phase0-pilot-api.py` 并打开 <http://127.0.0.1:8093/>，体验采购入库和销售出库的中文表格录单。试点使用合成主数据，草稿保存在本机进程内，关闭服务即清空。接口及后续 ERPNext 适配验收见 [W6 Business API](docs/BUSINESS_API_W6.md)。

## 商品价格档位与订单核对

在本机测试工作台迁移完成后，可以初始化零售价和五个人民币预设售价档位。重复执行会核对现有档位。

```bash
python3 scripts/phase0-configure-trade-tiers.py --apply
```

完整商品表单的「档位价格」页可随商品保存时录入多档价格，按库存计量单位计价。额外档位可通过原生价目表启用。客户可选择「默认报价档位」，报价与销售开单时由 ERPNext 取价。采购价使用启用的采购价目表。

在单据中展开商品行，可填写英文订单要求和标记。商品核对与金额明细集中显示中英文商品资料、单位、折扣及行金额。普通交易在编辑时可预览逐行含税值和整单合计，保存后可核对正式金额。使用运输规则、POS 或合并发票的草稿以保存后的原生金额为准。

## 库存状况表与商品档位

在「库存管理」打开「库存状况表－商品库存」。按公司、截止日、仓库或分类查询，也可按商品编号、名称、规格和型号筛选。分类沿用商品分类树。账面库存和库存金额来自有权限仓库的原生库存余额，预估售价按报告截止日的通用商品价格读取。

可按报表指定辅助计量单位，留空时使用商品首个辅助单位换算。预估计价档位决定参考销售总价和参考毛利率，未配置的价格留空。使用「下载商品库存 Excel」可输出财务库存数据和预估收益的双层表头。价格由商品上的「档位价格」或原生价目表维护。新增编号 6 以上的档位时，可创建名称为「预设售价6」或「预设售价6档」的启用销售价目表，报表将按编号增加相应列。

## 按业务分类使用资料工具

在中文工作台打开「资料工具」，按采购、销售、库存、收付款、基础资料或报表查找对应工具。单据列表的「资料操作」提供导入文件、下载空白模板、导出当前筛选或勾选的数据、批量 PDF 和打印。保存后的单据可从「资料操作」导出或下载本单。报表通过原生报表菜单导出、下载 PDF 或打印。

导入时先下载对应单据的 Excel/CSV 模板，保留表头及子表关联，先预览校验结果，再执行导入。退货、调拨及收付款的方向和原单关系按模板填写。业务单据导入为草稿，提交时沿用原有审批。各账号可用操作取决于 ERPNext 原生权限及有效单据状态。

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

## 验证销售与应收流程

采购和库存验证完成后，运行：

```bash
python3 scripts/phase0-validate-sales.py
```

脚本读取 `phase0/sales-validation.json`，通过 ERPNext 原生 REST API 和白名单映射方法验证报价、销售订单、完整及分批交货、替代 UOM、销售发票、应收、全额及部分收款、销售退货和贷项通知单。重复运行会读取并严格核验已有单据、库存和总账结果，不重复提交交易。

## 验证语言、权限、审批与审计

交易验证完成后，运行：

```bash
python3 scripts/phase0-validate-access.py
```

脚本读取 `phase0/access-validation.json`，将站点及五类合成用户统一为简体中文，验证原生角色的允许与拒绝访问、采购订单/销售订单/付款单审批、自审批阻断、提交/撤销和审计记录。历史英文覆盖试验仍保留证据，但不再是当前配置。重复运行会复用用户、审批流程和已撤销的验证单据。角色密码只用于本机 disposable 环境，可通过 `PHASE0_ROLE_PASSWORD` 覆盖，不得复用于其他环境。

## 验证原生报表与双语打印预览

交易与权限验证完成后，运行：

```bash
python3 scripts/phase0-validate-reporting.py
```

脚本读取 `phase0/reporting-validation.json`，通过原生报表 API 和 REST 只读验证库存余额与流水、采购/销售分析、应收应付、总账、撤销记录和采购/销售单据中英文 HTML 预览。它核对采购退货原单关联及具体科目冲回金额，不创建业务交易。报表日期固定为原始合成场景的 `2026-10-03`；复验日期单独记入证据文档。

P0.9 的 N1–N4 合成技术实施已完成：九类单据分级审批与最小权限、已批准的独立审批守卫、七类原生报表、十类中文 PDF、实时连接及操作 SOP 均有执行证据。见 [验收记录](docs/P09_ACCEPTANCE.md) 和 [操作 SOP](docs/OPERATOR_SOP.md)。P0.10/C0 固定版本合成生命周期已通过，见 [C0验收记录](docs/C0_ACCEPTANCE.md)。中文工作台入口为 `/desk/hardware-workbench`；完整语义/操作验收、真实映射、全量迁移、恢复和岗位 UAT 仍未完成。

中文扩展安装后，必须使用上述启动脚本或同时传入 `phase0/compose.zh.yaml` 与 `phase0/compose.workbench.yaml`，不能仅用基础 Compose 重建服务。首次启动前创建 `.venv` 并执行 `.venv/bin/pip install -r phase0/localization/requirements.txt`。这是一次性 Phase 0 环境，不是生产部署方案。

## 首版原生配置合成基线

范围见 `docs/FIRST_RELEASE_SCOPE.md`，N1配置及受控生产映射流程见 `docs/NATIVE_CONFIGURATION.md`。

```bash
.venv/bin/python scripts/phase0-configure-release.py --apply
.venv/bin/python scripts/phase0-configure-release.py
.venv/bin/python scripts/phase0-validate-release.py --create-drafts
.venv/bin/python scripts/phase0-validate-release.py
```

仅本机 R1 合成公司：默认只读，显式参数创建配置/草稿；不提交交易、不修改 P0余额或生产数据。合成5%税率、价格和信用额度不能用于真实业务。阈值和正式PDF已通过合成技术验收；实际财务/税务映射、迁移和UAT仍是后续发布门槛。

## 权限、报表与输出验收

```bash
.venv/bin/python scripts/phase0-configure-access.py --apply
.venv/bin/python scripts/phase0-configure-reports.py --apply
.venv/bin/python scripts/phase0-validate-release-access.py --exercise
.venv/bin/python scripts/phase0-validate-output.py
.venv/bin/python scripts/phase0-validate-realtime.py
```

审批 exercise 仅运行本机合成环境，创建/复用受控案例，按依赖顺序撤销并保留审计。配置脚本不带 `--apply` 时只读。输出验证通过原生 PDF 接口下载并用 Poppler 渲染，文件保存在仓库外的本地临时目录；生成后仍须逐页视觉检查。不要在生产运行这些合成脚本或旧审批缺口探针。

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

- 修改 ERPNext Core 的业务逻辑；用户于 2026-10-06 明确批准的展示翻译补丁是唯一限定例外，见 DEC-010 与 `phase0/localization/README.md`；
- 创建未经 Gap Analysis 证明必要的 Custom Field / Custom DocType；
- 创建 Agent、MCP Server 或让 Agent 直接访问数据库；
- 把本 Compose 文件当作生产部署方案。

测试公司、主数据、采购、库存、销售、退货、应收应付、语言、权限、审批、审计和报表已有合成场景执行证据，Gap Analysis 已形成。P0.8 范围冻结已完成；Phase 0 仍须完成 P0.9–P0.12 的配置、必要开发与发布准备；Phase 1 才进入部署。下一步按 `docs/AI_HANDOFF.md` 执行工作台验收及 M1/A1；P0.12 发布就绪评审通过前不进入部署。

## 来源

`phase0/compose.yaml` 基于 Frappe 官方 `frappe_docker` 的 `pwd.yml`（2026-08-30 获取），镜像固定到当时文件中的 `v16.33.0`。官方明确将该方式定位为快速探索和一次性演示环境。
