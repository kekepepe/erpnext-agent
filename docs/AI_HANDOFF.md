---
project: ERPNext-agent
status: active
current_phase: Phase 0
current_task: P0 - validate the two-document W6 draft pilot and prepare the ERPNext adapter
last_updated: 2026-11-23
updated_by: Codex
---

# AI Project Handoff

## Current Objective

### 2026-11-23 检查点与出入库试点联调

- **版本检查点已完成。** 按文件复点为 105 个（23 个修改、82 个未跟踪），归档为 8 个生成于本轮的提交，从 `f4ad41f` 到 `995da6f`。工作台、交易字段与资料导入因共用应用钩子和配置而合为一组。暂存快照通过差异空白检查；复核了凭据模式、邮箱、个人路径、合成迁移样例和两张 U2 图片。保留容器路径、示例邮箱及本机 disposable 测试默认值。真实期初文件、异常明细和日志留在本机受控目录。
- **Business API 契约与合成后端已完成。** [契约](BUSINESS_API_W6.md) 定义两类单据的选项、草稿新建、读取及更新。演示服务 `scripts/phase0-pilot-api.py` 验证商品、往来单位、仓库和数量，处理并发重试、版本冲突和字段错误，草稿保存在本机进程内。
- **前端两张试点表单已交付并通过合成联调。** Antigravity 在独立目录完成 HTML、CSS 和 JavaScript，Codex 集成到 `prototypes/w6/`，复核并修正草稿重试、跨计量单位汇总提示及无障碍标签。采购入库和销售出库共用录单结构，分别切换供应商和客户。支持中英文商品、规格型号、单位、仓库、数量、键盘增行、删行及草稿修订。启动命令为 `python3 scripts/phase0-pilot-api.py`。
- **浏览器验收。** Chrome／Playwright 在 1280×720 和 390×844 下实测。桌面覆盖必填提示、键盘加行和删除、采购入库保存与读回、版本更新、保存回包丢失后的同键去重、修改后换键、版本冲突输入保留、销售出库和新建重置。窄屏覆盖表格内横向滚动和销售草稿保存。检查两张合成截图，交互无未预期页面异常。
- **验证。** `compileall -q apps scripts`、`unittest discover -s scripts -p 'test_*.py'`（46 项，含 4 项 HTTP 测试）、`node --test scripts/test_phase0_form_display.js` 和 `./scripts/phase0-check.sh` 通过。ERPNext 健康检查证明现有服务可用；W6 API 测试使用独立本机合成服务。
- **发布门槛。** 正式 ERPNext 适配器、真实岗位和仓库隔离、原生审批与库存对账仍待隔离站验证。客户岗位、财务口径、英文原单来源与目标单据及脱敏样本仍待确认。首发候选需与冻结 R1 对齐，正式 UAT、RC 审核和 Phase 1 部署仍未完成。

### 2026-11-23 所有者复核：渐进试点与英文原单录单顺序

W6 已选丙。先以采购入库、销售出库为试点，按实际岗位的开单频次确认。先定义试点所需的内部 Business API 契约。两张试点单据及对应权限列为首发候选，正式范围发布前与 R1 对齐。

英文原单流程已确认：上传原单 → 匹配中文商品并人工确认 → 生成中英对照新单 → 业务人员依据新单录入 ERP 草稿 → 按普通订单走权限、审批、提交与后续履约。待确认原单来自客户还是供应商、ERP 目标单据类型，再收集 3–5 家对应来源的脱敏样本。是否列为首发门槛取决于客户日常操作是否依赖该流程。

本次同步 `OWNER_DIRECTION_20261123.md` 第 5、7、8、11、12 节和 DEC-016/019/021，修正 Git 检查点的价格档位配置依赖。`git diff --check` 及总纲第 7、8 节流程顺序检查通过。本次为文档更新，未运行 ERP 测试。近期 P0 仍是复核检查点文件清单、敏感信息和测试，再按仓库授权规则提交。

### 2026-11-23 第二轮补充想法：底座替换路线与三项新增需求（历史记录，执行口径以上方复核为准）

所有者补充四类想法：逐步换掉 ERPNext 底座改自研、只服务这一家客户、英文采购单导入并模糊匹配中文后导出中英对照单、分级权限前端一致但按岗位锁住、以及多家供应商订单格式不同需按供应商匹配。全部内容已合并进 `docs/OWNER_DIRECTION_20261123.md`（该文件为本项目唯一方向总纲，第二轮内容并入第 4、6、7、8 节），并落成 DEC-018（单租户）、DEC-019（英文匹配与中英对照）、DEC-020（岗位视图预设）、DEC-021（供应商导入 profile 配置化）、DEC-022（底座替换采用分层抽离，已于 2026-11-23 确认）。本轮只更新项目文档，未改代码、未提交。

评估要点：重新实现与 ERPNext 等价的核算、库存、税务、审批、权限、报表与表单内核约需 15–20 人月（熟练团队口径），且 C0/M1/A1 三道演练、9 个证据文件、十类 PDF 与九岗位权限矩阵全部建立在现有内核之上，换底座等于证据链归零。而已记录的具体抱怨几乎全在表现层与交互层，DEC-016 本就要重做。因此已定 DEC-022 分层抽离：L1 表现层与 L2 业务编排层自研，L3 定义自有 Business API 契约作为隔离层，L4 核算内核暂用 ERPNext；L1/L2 只依赖契约不依赖 DocType 结构，将来换内核只需写新适配器。终局替换设四条触发门槛（真实订单后仍无法表达、上游升级断裂、客户要求数据自主且愿担维护、有人力与预算重写并全量重验）。当下唯一低成本动作就是先定义该契约。

工程基础核实：主数据已有 `custom_trade_name_en`（英文商品名称）、`custom_trade_requirement_en`、`custom_trade_line_requirement_en`，是别名库的现成起点；`apps/hardware_erp/hardware_erp/approval.py` 已确立"前端呈现与后端校验分离、后端为准"的范式，是岗位权限锁定机制的可复用先例；`phase0/migration/mapping-*.json` 与 `scripts/phase0-preflight-migration.py` 是供应商导入 profile 可复用的配置化结构。

已识别两个 blocker：一是 3–5 家供应商的真实英文采购单样本未到手，英文匹配与导入 profile 只能停在设计；二是岗位视图预设的粒度依赖客户真实岗位与人数（Q4）。已定方案不单独征询的项：匹配输出候选与置信度并支持人工确认后回写别名库，绝不自动替换；导入 profile 保持配置化、客户自助维护，导入一律进草稿走原有审批。

下一步：（1）按 `docs/OWNER_DIRECTION_20261123.md` 第 2.2 节把 75 个文件切成 10 个 checkpoint commit，提交前须完成敏感信息扫描、`compileall` 与 42 项 Python 测试全绿；（2）请所有者确认 W6 前端改造走甲/乙/丙哪条路径，并提供真实岗位清单与人数；（3）向客户索取 3–5 家供应商真实采购单（脱敏）。是否 push 到 origin 需所有者明确授权。

### 2026-11-23 所有者方向整理与交付路线确定

所有者就「与管家婆／金蝶差距」评审提出的六个问题给出答复，已整理为 `docs/OWNER_DIRECTION_20261123.md`，并落成三条决策：DEC-015（ERPNext 自建、为一家指定的五金工具公司定制、后期部署到 Web 域名）、DEC-016（前端形态按国内进销存习惯重做，含核心单据自定义高密度录入表单）、DEC-017（成本算法、毛利口径、折算税费率、折扣分摊、运费与尾差等财务口径延后，待客户财务部确认）。本轮只更新项目文档，未改代码、未提交。

新发现并已写入方向文档的事实：最后提交为 2026-10-27 17:18（`5aef96b`），至 11-23 工作区累积 75 个未提交文件（23 修改、52 未跟踪），`origin/main` 停在同一提交。11-04 至 11-22 的 C0 验收、M1 两轮期初迁移、A1 异站恢复、中文工作台实现、管家婆差距分析、库存状况表与含税预览引擎全部只存在于工作区，尚无 git 记录。方向文档第 2 节给出 10 组 checkpoint commit 的完整分组方案与文件归属。

方向文档同时识别出两处合并与分叉：D-3（单据手感与批量录入）与 D-6（界面偏西方、用词英译中）实为同一交付物，合并为「前端形态重做」，避免重复施工；DEC-015 留有未闭合分叉——本次仅服务这一家客户，还是需按可复制多家的架构约束设计，该答案决定租户与权限架构，越晚回答返工代价越高。另需注意 D-4 的连带风险：若先按真实财务习惯做完录入界面再与财务部对齐口径，会因输入侧锁定口径而返工，故录单应先做字段与交互顺序、计算规则留待财务确认后填充。

下一步：（1）按方向文档第 2.2 节把 75 个文件切成 10 个 checkpoint commit，提交前须完成敏感信息扫描、`compileall` 与 42 项 Python 测试全绿；（2）请所有者确认单客户 vs 可复制多家的租户模型，以及前端改造走「核心单据全定制 / 原生表单增强 / 两张单据渐进试点」哪条路；（3）与财务部开会确认方向文档第 9.1 节的口径清单。是否 push 到 origin 需所有者明确授权。

### 2026-11-22 本机期初库存草稿准备

用户确认建专用期初仓，先准备正常记录草稿，异常单列。通过本地原生服务导入所需商品资料，生成期初库存盘点草稿，并逐行回读仓库、数量、估值金额与草稿状态。负数量、正数量零金额、正数量负金额列入本机受控异常清单，零量行无需入库。未提交期初单，复核该批未创建库存流水及库存盘点总账记录。原始文件、异常记录、导入日志和单号清单留在受控环境，未写入仓库。实际过账与库存对账仍按既有审批完成，本次不构成 M1/A1 正式签核。

### 2026-11-22 商品库存格式与预设售价

用管家婆库存导出的表头核对布局，按「库存管理 → 库存状况表－商品库存」提供新报表。列包含商品图片、四级分类、编号/名称/规格/型号/品牌、零售和参考成本、财务库存数据、五档预设售价及预估收益。原生库存余额按有权访问的仓库汇总，支持仓库、日期、商品分类和快速查询。辅助成本按商品单位换算计算。参考销售总价为所选档位价乘账面库存，参考毛利率为参考销售总价扣库存金额后除参考销售总价。缺价留空，价目表记录有效期按报表截止日。下载 Excel 提供双层合并表头。新增商品价格维护按「零售价、预设售价1–5」排序，既有价目表内部名称继续使用。仅在本机新增缺少的第五档价目表及一条合成试价，附件未导入。

本机迁移和健康检查通过。合成商品跨仓汇总及单仓账面库存、金额与原生 Stock Balance 相等。检查 50 倍辅助单位换算、空白一档、第五档价格、参考收入和毛利、Excel 合并表头及实际价格位置。库存复核测试角色可读报表，销售测试角色被拒绝。Chrome 实测中文标题、筛选后下载合并表头 Excel、新增商品显示有序的零售价和五档售价均通过。41 项 Python、JS 检查和 Git 空白检查通过。

### 2026-11-22 资料工具与导入导出

在中文工作台新增「资料工具」，按采购、销售、库存、收付款、基础资料和报表分类。新增列表和已保存表单的「资料操作」，复用原生 Data Import、DataExporter、Print 和 PDF。按当前筛选或勾选记录导出，向导提供空白 Excel/CSV 模板。启用盘点单的原生整单导入配置，禁止业务导入任务启用自动提交，仍走原有审批。工具显示由目标单据及 Data Import 原生权限决定。未改变岗位授权。

本机迁移通过。Chrome 可打开六类、33 个入口的资料工具，下载报价 Excel 模板和按列表筛选的 Excel 数据、预填原生导入向导、进入报价打印，390×844 下操作按钮正常换行。通过原生接口完成合成商品 CSV 导入和筛选导出、报价及盘点 CSV 导入为草稿、PDF 文件校验以及导入自动提交拒绝。管理员的 18 个交易入口显示导入、导出和打印能力。九岗位工作台访问及访客拒绝通过，41 项 Python、原展示 Node 检查、JS 语法和 git diff 检查通过。下一步可在岗位验收时逐个验证本岗位所需交易模板和导出范围，继续[功能补齐计划](ERP_TRADE_GAP_COMPLETION_PLAN.md)的价格来源与批量录单。

### 2026-11-22 首批补齐开始执行

按[功能补齐计划](ERP_TRADE_GAP_COMPLETION_PLAN.md)启动 1A/1B。新增 `hardware_erp/trade_preview.py` 与草稿表单联动，在编辑时通过原生只读计算显示逐行含税值与整单合计。采购/销售取价通过 18081 隔离站 12 个原生场景，覆盖客户/供应商专价、数量门槛、优先级、时效、通用档位及按盒换算。两个可重复执行的验证脚本为 `scripts/phase0-validate-trade-pricing.py` 和 `scripts/phase0-validate-trade-preview.py`。本机 8080 已重建。四张合成报价通过逐行和整单预览与保存对账，验证脚本只读重跑通过。另只读复算原采购入库 36 元、采购退货 -17.50 元、销售退货 -32.50 元。Chrome 实测改数量由 2 到 3，预览从 170.10 元变为 255.15 元，实际保存同额，Desk 启动仍有已知非阻断 404。40 项 Python 测试和 Node 展示验证通过。真实顺序和历史取价决策仍需业务确认。下一步继续 1A 价格来源与历史价边界、1B 批量录单和岗位验收。管家婆保持只读，本轮无界面操作。

### 2026-11-22 本地 ERP 功能补齐计划

新增[本地 ERP 功能补齐计划](ERP_TRADE_GAP_COMPLETION_PLAN.md)，涵盖取价、录单、来源关联、同屏结算、物流成本、报表和主数据迁移。将调拨申请、智能补货、组装、外部开票等列为待确认范围。首个可执行任务为在隔离站用既有五档商品建立取价冲突与含税预览样例。计划尚未实施，本轮仅更新项目文档。

### 2026-11-22 管家婆功能对照

用户要求只读查看管家婆并逐项对比本地 ERP。查看了采购/销售开单表单、两种价格策略、往来资料及库存/财务菜单，并核对本机采购订单、ERP 原生对象定义、工作台入口和现有验收证据。新增 [网上管家婆与本地 ERP 功能差距](GUANJIAPO_ERP_GAP_ANALYSIS.md)，记录出入库与收付操作的边界、取价顺序、保存前含税核对、运费成本、开票及报表等差异。仅更新项目文档。下一步请采购、销售和财务在 W4 优先确认结算时点、取价顺序与折扣税费样例，再判断配置或开发范围。

### 2026-11-22 订单词条与档位定价

按用户提供的旧系统参考图，在报价、采购订单/入库/发票、销售订单/出库/发票补齐标记、简称、规格、型号、英文名称、英文订单要求、摘要和金额核对视图。复用原生品牌、计量单位及换算、仓库、折扣和逐行税费。新增中文操作词条，英文集中在商品及交易的名称和要求。新增品时用完整商品表单，在「档位价格」按库存单位一次录入多个原生价格，客户用「默认报价档位」设置一次，原生开单选价。实现见 `hardware_erp/trade_fields.py`、`erpnext_zh/public/js/trade_forms.js` 和 DEC-014。本机迁移已执行，`scripts/phase0-configure-trade-tiers.py --apply` 创建五档，随后只读复核新增零档。

验证通过：`scripts/phase0-check.sh`、40 项 Python 测试、Node 展示检查、九岗工作台权限及访客拒绝。Chrome 新商品保存五档，客户档位在原生报价表单带出 90 元并成功保存。1440×920 和重新加载的 390×844 均显示核对明细，窄屏可横向滚动。原生销售订单取价接口也返回 90 元。原生 API 草稿验证：采购两盒、每盒 50 件、九折、含税金额 36 元，Chrome 入库单复核中文单位「盒」、换算系数和英文备注。报价两件、档位 90 元、九折及合成税率 5%，不含税单价 81 元，含税单价 85.05 元，含税金额 170.10 元，并保存商品型号及英文要求。提交非法档位会回滚整个首次商品保存。N1 全量配置预检遇到现站合成供应商默认币种差异，现有配置保留，另取四张已存采购/报价合成草稿只读验证含税/未税金额均为 100 + 5 = 105 元。Chrome 启动阶段返回一条 `/undefined` 404，受测表单及业务交互通过。

行含税金额在保存后显示。历史单据可按留存的原生行税明细核对，缺失的商品规格或其他主数据快照留空。参考成本和最低售价是商品资料，实际价格、税务模板、角色验收及发布准入继续由业务确认。下一步以实际使用的品类、计量单位和客户档位走 W4 岗位验收，再复核正式候选全生命周期和权限矩阵。

### 2026-11-13 晚间复核与下一步

W3 业务入口及 W5 技术回归完成。修复 `workbench.js` 首次进入原生列表丢失单据类型以及报表切换串用筛选的问题。1280×720 与 390×844 各走完 38 个入口，所有列表筛选、原生目的地及高亮通过。退货办理按钮能引导到已提交普通原单。访客被拒绝、九岗菜单及近期单据权限均通过。[导航证据](../phase0/evidence/workbench-navigation-20261113.json)

M1 扩展实施并验证。另一全新站点使用 11 月 1 日截止、两仓和原生包装单位换算，一箱 50 件；同一客户两张期初发票分别核销，逐张未结 15 和 30 元。库存总值 520 元、应收 45 元、应付 8 元，八行对账相等。八张已过账单重放零新增，前一批次的数据结构仍受支持。公私附件补验通过：财务可下载合成销售发票私有附件，采购与访客被拒。[迁移与附件证据](../phase0/evidence/m1-restore-20261113.json)

A1 同端口切回已实测。候选构建从 C0 备份恢复并同步十类中文打印模板，实际导出十页并核看排版。合成候选站停用销售订单审批后，预检按其工作流名称拒绝。另建空卷，恢复 C0 的 linux/arm64 执行镜像、匹配配置与数据库/公私文件。两代库存、业务及账务对账摘要一致，恢复后七类岗位报表、十份历史模板 PDF 和九岗位权限通过。实测 509 秒，含首次找不到旧镜像、找回执行层、恢复和回读。构建证明附件已从历史缓存淘汰；归档保留经验证的平台清单、配置及执行层。已将镜像可用性预检和候选打印同步纳入演练脚本。详见[回退证据](../phase0/evidence/a1-switchback-20261113.json)及[运行手册](M1_SYNTHETIC_RUNBOOK.md)。

本地验证：40 项 Python、Node 展示检查和相关 shell 语法通过。正式验收仍缺真实组织/身份与税务映射、岗位签核、实际容量和恢复目标、独立保管的不可变候选包及部署批准。下一阶段先执行[发布计划](WORKBENCH_RELEASE_PLAN.md)中“发布评审前”的材料与缺陷核对。真实开账前继续使用合成环境；本轮未提交或推送。

### 2026-11-13 下午合成期初迁移与异站恢复

用户选择先用合成数据。C0、W1/W2 已有验收，本轮完成 M1 固定批次的两次独立迁移及一次中断续跑。18082 和 18083 为新建的独立站，不同数据库卷、同一中文来源、同一截止日（10 月 31 日）。每站六张过账单：期初库存、销售和采购期初发票、逐发票收付核销、期初权益结转。两站重放均新增零张；四份原生报表对齐七行，库存 2 件/20 元、应收 15 元、应付 8 元，过渡科目及现金净额为零。第一站已过账库存后中断，续跑只建剩余五张。此工具仅适用于给定单公司/单商品/两笔未结发票样例，不是旧系统通用导入器。

A1 已开始：对第一站停入口和后台任务，用 Bench 完整备份，并在仅含初始系统的第三站 18084 恢复。源/目标镜像一致，数据库卷和站点卷不同。实际核对七行余额、六张凭证、九条版本记录、九个岗位及公私附件；数据复验耗时 29 秒（从启动恢复计，不含备份、环境准备、后续 PDF 配置及质量检查）。另验七类原生报表、九个岗位登录及销售越权拒绝。原生 PDF 首次失败为容器内地址不可达；配置内部打印地址后，Standard 销售发票 PDF 单号、外部引用和 19 元金额通过，尚未据此验收恢复后的十类正式 PDF。

新增入口：`phase0-export-opening.py`、`phase0-rehearse-opening.py`、`phase0-new-migration-site.sh`、`phase0-restore-opening.sh`、`phase0-verify-opening-restore.py`（均在 scripts）。对账现在同时验证目标包截止日、币种、时区及两份文件摘要。复现步骤见 [演练手册](M1_SYNTHETIC_RUNBOOK.md)，脱敏实测结果见 [证据](../phase0/evidence/m1-restore-20261113.json)。39 项 Python 测试、Node 原有展示检查通过。真实资料/审批人不参与本轮；不以合成过账或技术恢复代替正式签核。

销售退货字段已在 8080 独立浏览器以 1280×720 和 390×844（刷新）确认：“办理销售贷项”“用于退货账务处理，不表示已经退还资金。”以及“原销售出库单”均出现。下一阶段计划与剩余发布条件见 [交付计划](WORKBENCH_RELEASE_PLAN.md)。

### 2026-11-13 工作台复核与期初迁移预检

C0 的两轮生命周期已在 11 月 4 日完成并归档。11 月 6 日的 W4 增量完成十类中文 PDF、收付款和退货方向及原生报表复核，证据见 `phase0/evidence/u1-output-20261106.json`。付款与销售退货详情打开、刷新后高亮通过。销售退货页的原生 issue_credit_note 字段已由“退款”改为“办理销售贷项”，该最后一次措辞修改的浏览器显示仍待复核。

11 月 13 日实测 8080 健康、四应用版本、访客拒绝、九类工作台账号与近期记录权限。13 个只读打印预览通过，已撤销单据触发预期原生拒绝，8 份来源单据回读相同。本次内置浏览器建立连接及恢复标签均超时，保留屏幕复核项。

M1 开始实施来源到目标的期初映射预检。新增 `scripts/phase0-preflight-migration.py`、`phase0/migration/mapping-example.json` 和七行标准化样例；校验源文件摘要、公司/两仓、编码和单位，核对库存/应收/应付明细与试算控制科目。原生 API 实际校验演示公司、库存商品和单位、往来、两座仓库及叶科目类型通过。第二套名称映射、源文件被替换、总账平衡但明细差一分和重复仓库映射已测试。36 项 Python 和 Node 展示检查通过。迁移预检的目标报表快照、真实身份与税务映射、受控期初单据导入及两次独立重放仍待完成。真实源账及岗位确认是正式验收输入。

当前优先项为复核退货字段在桌面和窄屏上的显示、完成 W3–W5 剩余页面与岗位清单，再按 [M1 执行计划](WORKBENCH_RELEASE_PLAN.md) 进行目标快照导出与隔离导入。A1 全站恢复和发布准入仍在后续队列。

### 2026-11-06 当前执行状态（优先于下方历史记录）

- C0 固定版本合成技术验收完成，执行日期 11 月 4 日，11 月 6 日归档复核。最终新站点完整脚本退出 0，卸载守卫期间入口及后台任务停止；重装前后双轮业务回归通过且库存/AR75/AP60/GL一致。见 [C0验收](C0_ACCEPTANCE.md) 和 `phase0/evidence/c0-validation-20261104.json`。这不是跨版本升级、完整恢复或生产准入。
- W1/W2 已实现权限后端和中文工作台。修复列表标准筛选匹配、工作台与列表加载时序，JS/CSS 资源使用内容版本防止缓存旧代码。实际浏览器收付款切换和刷新后高亮通过，采购表头/子表、未保存两种选择、原生回退、390×844和1280×720已有验证。所有首版组件仍使用原生业务对象和接口。
- M1 已启动：合成商品导入两条，重放新增零条；整批校验缺失单位及已有字段冲突，拒绝前不写入。期初CSV离线对账拒绝重复键、非法数值、不平衡试算和一分钱差异。尚未实现完整期初交易导入、真实映射、两次独立全量迁移或失败恢复。
- 当前继续 W3/W4/W5：十类打印中已发现收付款金额方向混淆及标题不统一，正在实施语义修复和原生打印回归。技术验证不代替业务/财务用词签核。接下来的队列见 [交付与迁移计划](WORKBENCH_RELEASE_PLAN.md)。真实源数据、税务口径、期初对账基准和岗位签核尚无输入；可以继续技术准备，不能虚构这些事实来关闭 M1/A1。
- 本轮保留已有未提交修改，不提交或推送；用户原有8080未保存采购草稿没有操作。源代码、应用配置和测试是进度依据。


### 2026-11-04 工作台与发布验证

本地工作台路径为 `/desk/hardware-workbench`。已部署的展示扩展包含真实权限目录、近期单据和跨路由导航。浏览器复核了新采购订单的订单日期、要求到货日期、商品编码与收货仓库。未保存提醒的“否”保留修改，“是”返回工作台。390×844 可展开导航、退回原生 Desk、重新启用中文工作台。1280×720 的侧栏与内容边界同为 194px。库存余额表可打开原生筛选和后台报表入口，返回后工作台可刷新。

本轮 `scripts/phase0-validate-workbench.py` 通过访客拒绝、九类账号页面访问、授权列表与近期单据回读。8080 的实时连接、异源拒绝与匿名拒绝通过。离线 Python 32 项及 Node 原有表单检查通过。M1 已有脱敏期初模板与离线对账工具，样例五行一致通过，改一分钱返回失败。详见 [下一阶段执行计划](WORKBENCH_RELEASE_PLAN.md)。

C0 使用新项目、新卷、127.0.0.1:18081 和逐次独立证据目录。已完成应用安装、迁移、缺少审批角色的特定原因拒绝，以及配置九类角色、九个工作流后的预检。两轮业务验收、重装后对账、M1 导入演练和 A1 恢复与岗位签核分别记录，不由已有 8080 的通过结果推定。

### Full workbench implementation authorization — 2026-10-28

Owner requested a plan followed by implementation of all first-release UI components and backend integration, beyond the prototype. `docs/WORKBENCH_IMPLEMENTATION_PLAN.md` defines W0–W6 as the grouped current task. Extend erpnext_zh presentation only; keep hardware_erp approval guard and native transactional APIs. No independent ERP rebuild or expansion into deferred business modules. This supersedes the earlier prototype-only implementation restriction; C0, M1 and A1 release gates remain open and mandatory. No commit/push in this scope unless separately requested.

### U2 first interactive prototype — 2026-10-28

- Added isolated static prototype in `prototypes/u2/` (HTML/CSS/ES modules, synthetic in-memory data; no ERP connection). Workbench, purchase list and detail/new form are connected; remaining modules explicitly show navigation previews. Local preview: http://127.0.0.1:8092 . Refresh resets mock data.
- IAB checks passed: list navigation, empty search/reset, required-field validation, supplier/item selection and save, independent manager approval, high-value return-for-edit → manager escalation → owner approval, unsaved-change confirmation and small-screen menu. Node syntax checks and git diff whitespace check passed. No backend/business regression claimed.
- Reference and actual narrow-browser screenshots inspected; retained in prototype assets. Exact 1280×720/390×844 and full desktop visual acceptance remain pending; Chrome wide-view verification was interrupted. This is a reviewable first draft, not U2 final acceptance or U3 implementation. See prototype README for design comparisons and intentional deviations (U1-compliant synthetic names/statuses, additional filters, responsive drawer).
- Existing C0 priority and U0/U1 remaining checks unchanged. No commit/push. Next UI action: owner review of layout/wording, then complete responsive/interaction QA and revise prototype before real integration.

### U0/U1 v0.2 research and prototype input — 2026-10-28

- Owner requested additional research and optimization of the two local U0/U1 drafts. Updated `docs/UI_U0_RESEARCH.md` and `docs/UI_CHINESE_TERMS.md` to v0.2; preserved original drafts in `docs/archive/*_v0.1.md`. No UI implementation, commit or push in this turn.
- Added official 管家婆 sales/receipt help, current public 金蝶星辰 function naming and a version-qualified product notice; distinguished historical summaries from read source text. Old S5 PDF timed out and is not used for business conclusions. Fixed-version ERPNext v16.33.0 payment mapping and Purchase Order metadata plus repository Workflow code support the semantic review.
- Corrected Rejected to cancellation semantics in the current R1 workflow, separated return-for-edit, removed invented available-stock/outstanding formulas, distinguished customer/supplier refund directions and conditional stock effects. Added prototype-only term policy, purchase field/action/role matrix, mock-data boundaries and error/unsaved states for U2's three connected pages.
- U2 design inputs are ready for prototype work; U0/U1 full acceptance remains open for online page checks, remaining field/output coverage and business/finance review. Docker socket was absent during the read-only check; no runtime was started or changed. No new UI prototype exists in this change. Technical execution priority remains C0 before U3; research/prototype preparation remains allowed by the UI plan.

### Public repository synchronization — 2026-10-27

- Owner explicitly authorized committing and pushing all current project changes except sensitive information. This supersedes earlier no-commit/no-push statements for this synchronization only.
- Publication scope: existing P0.9 implementation and synthetic evidence, incomplete C0 lifecycle work, release documentation and the new UI/Chinese terminology plan. C0 remains unaccepted and UI work remains planned, not implemented.
- Pre-publication checks: 25 Python tests PASS; Node display checks PASS; lifecycle shell syntax and git diff whitespace checks PASS. Changed/untracked file inventory checked for secret patterns, non-example email addresses and personal local paths: none detected. Runtime evidence uses synthetic identities. Vendored font/wheel hashes match the Dockerfile and include licenses. Local secret/backup exclusions added to .gitignore. No full lifecycle/runtime acceptance is claimed by these checks.

### UI and Chinese business terminology planning — 2026-10-27

- Owner requested a plan first, with later coordinated implementation: fixed left business categories/right content, and terminology grounded in Chinese ERP usage (管家婆、金蝶), rather than literal translation. Plan: `docs/UI_CHINESE_WORKBENCH_PLAN.md` (U0 research → U1 terminology → U2 prototype → U3 native integration → U4 acceptance). No UI code or terminology replacements implemented in this planning turn.
- Recommended architecture remains ERPNext business backend/native forms plus a bounded presentation extension in this repository; no independent ERP rebuild. Exact extension ownership and cross-route feasibility remain U3 validation items. Research/prototype can precede implementation; current technical execution priority remains C0, followed by UI implementation and affected lifecycle revalidation before M1/A1 final acceptance. Register the presentation scope amendment before implementation; historical P0.9 evidence does not accept the new UI.
- Runtime update superseding the earlier offline inspection: existing local Docker services were started at the owner's request; frontend restart resolved HTTP 502, and an authenticated Chinese Desk rendered successfully. This is page availability evidence only, not C0 or full business regression acceptance.
- Next planning deliverables are an evidence-backed terminology table and three linked prototype pages. All tasks are currently unchecked. No commit/push or deployment performed.

### Progress inspection and pre-Phase-1 plan — 2026-10-27

- Owner requested progress inspection and planning before further implementation. Plan: `docs/PRE_PHASE1_PLAN.md`; current execution priority remains P0.10/C0. No milestone was accepted by this planning pass.
- P0.9 has the recorded 2026-10-12 synthetic technical acceptance. C0 is partially implemented: clean-site initialization, global CNY/language/time-zone, local-account resolution, seed dependencies and ordinary-session CSRF fixes are present. The last purchase-return GL account fix has no subsequent complete runtime acceptance; uninstall/reinstall and two-round full regression are still unproven.
- Current read-only inspection: Docker socket absent, localhost8080/18080 unreachable; `/private/tmp/p010-lifecycle-accepted` absent. Offline execution: 25 Python tests PASS, Node display checks PASS, lifecycle shell syntax PASS, git diff --check PASS. HEAD f908acc; later work remains uncommitted/untracked; remote refs not refreshed.
- Before Phase 1: finish C0; complete controlled real-company/identity/configuration mapping plus M1 migration tooling and **two** isolated migration rehearsals (the frozen scope is stricter than the generic checklist); then A1 production-like rebuild, full regression, whole-site recovery/version rollback, employee UAT and immutable RC approval. Existing localhost/R1-only fixtures/preflight are not the real-company release configuration path. External integration/Business API/MCP/Agent items are out of scope, not unfinished mandatory development.
- This dated note supersedes stale historical next-action/production-readiness statements below. Next implementation action: verify available isolated runtime state, review/retest the final reporting fix, then run the complete C0 lifecycle and persist sanitized evidence outside temporary-only storage. No runtime mutation, commit or push was performed during this inspection.

P0.7 capability discovery and its explicit presentation repair are closed for progression as of 2026-10-09. The owner requested progression to P0.8, confirmed the single-company/CNY/Chinese/core-trading scope and delegated the remaining release-design parameters. `docs/FIRST_RELEASE_SCOPE.md` freezes R1-scope-v1 with a requirement/evidence matrix, named owner roles, measurable acceptance criteria and ordered implementation packages. This is not independent Web GPT review, production UAT or deployment authorization.

**P0.9 / N1–N4 technical implementation completed 2026-10-12 under R1-scope-v1.1. Recommended next task: P0.10 / C0, clean-site installation and lifecycle acceptance of the already-approved approval guard.** Real company/fiscal/tax/identity mapping, migration, employee UAT, full backup/restore/rollback and RC approval remain P0.11/P0.12 release gates. No deployment, commit or push is authorized or performed.

### P0.9 closeout — 2026-10-12

- N2: independent `hardware_erp`0.1.0 installed in the fixed image; nine native Workflows, nine isolated functional identities, Company/stock Warehouse User Permissions and native least-privilege permissions configured. Guard protects state/docstatus, current thresholds, company/creator identity, independent approvers and business-input integrity; return-to-Pending permits correction/reapproval. No new business Core patch, custom schema or external endpoint.
- Acceptance: 24 synthetic cases. Final expanded exercise exit0 with67 checks (two new positive fixtures); second repeat exit0 with54 checks, created[]. Repeat rechecks persistent negatives and retained audit; cancelled positive fixtures are reused, not resubmitted. Both order boundaries10,000/10,000.01 and payment20,000/20,000.01, nine types, linked receipts/invoices/returns/credits, transfers/counts, reverse cancellation, dual-role self approval, client-save/flag mutation, direct submit/cancel, intermediate edits, cancellation price changes, credit1000.01/limit1000, company/warehouse/price/admin/audit rejection verified. Twenty-one positive cases cancelled; three deliberate negative drafts retained. Native Version/Comment/Permission Log absent from automatic cleanup; SR track_changes enabled and new SR Version verified.
- N3: seven native reports assigned through Custom Role, preserving standard definitions/native role grants; stock/financial source ledgers and Journal Entry dependency are read-only. Proper functional roles run all seven; cross-company filters reject/return no business data. Ten controlled Chinese native PDF downloads/text-data checks and every rendered page reviewed; 10 PDFs/10 pages, repeated successfully. CJK font with pinned hash and native host_name internal Docker URL fix resources. Fixed NGINX socket topology validates external origins before matching private Host/Origin; authenticated native namespace passes, foreign origin403 and missing authentication rejected. Fresh browser has no error/warn messages.
- Chinese UI: in-app browser technical checklist of ten details, ten R1-filtered lists and seven reports at1280×720 /390×844; dictionary additions close observed report/actions/onboarding/help/name omissions. Stored English business fields, internal identifiers and raw content remain preserved. Native System Settings.enable_onboarding=0 removes obstructing onboarding cards; fresh browser screenshots confirm this at both sizes; full role-by-role employee UAT remains A1. See `docs/P09_ACCEPTANCE.md` for precise evidence and limitations.
- N4: `docs/OPERATOR_SOP.md` covers master/price/tax/credit, purchase/receipt/invoice/payment, stock/count, sales/shipping/receivable, returns/net-delivery explanation, reapproval/cancellation/audit, reconciliation/month close, manual legal-invoice reference, PDF and restart/recovery boundaries. Native API technical role walk-through performed; actual employee training/sign-off remains A1.
- Rebuilt/restarted final image and verified deployed approval/rules/proxy hashes match repository. Versions ERPNext16.33.0/Frappe16.31.0/erpnext_zh0.1.1/hardware_erp0.1.0. Health passes. Existing purchase/stock/sales/access/reporting/release/realtime validators each ran twice exit0; P0 AR75/AP60, six stock balances and eleven active GL vouchers preserved. Python21 tests, Node display checks, compilation and diff whitespace checks pass.
- Synthetic evidence in `phase0/evidence/`; binary PDFs/screenshots remain local outside public repository. `phase0-validate-release.py` now accepts retained cancelled N2 history while asserting zero active stock/GL balances; N1 four draft tax arithmetic fixtures still100+5=105. Unused pre-guard negative-payment draft removed; all submitted audit retained.
- Reproduce: start.sh → configure-release --apply → configure-access --apply → configure-reports --apply → validate-release → validate-release-access --exercise → validate-output → validate-realtime. Native config defaults to read-only; exercise only disposable localhost. Do not rerun old native gap probe against the expanded active Workflows or switch to base-only Compose.
- Remaining gates: clean site/migration/uninstall/upgrade lifecycle (C0), controlled real mapping, missing/incorrect actual tax applicability validation, return-tax/discount/period cases, migration rehearsal, backups/full-site version rollback, role UAT and immutable RC. Synthetic5% and untaxed threshold fixtures are not actual tax policy; neither real finance inputs nor production readiness is claimed.


### P0.9.2 / N2 guard authorization and implementation — 2026-10-12

The owner explicitly approved the minimum server-side approval guard proposal. DEC-012 and R1-scope-v1.1 record the narrow amendment. Independent `apps/hardware_erp` is installed in the disposable image; native roles/User Permissions/Workflows remain the workflow engine. N2 implementation and expanded normal/negative verification are complete; see the closeout above. The dated approval blocker below is resolved by this decision; do not request that permission again. No unrelated business customization, integration, API/MCP/Agent or Core change is authorized. N3/N4 follow after N2 acceptance.

### P0.9.2 / N2 approval boundary investigation — 2026-10-11 (historical, scope approval now received)

- **Blocked pending a concrete scope amendment:** frozen R1-09/R1-10 require server-side approval/self-approval/bypass rejection. Native Purchase Order Workflow does not enforce these across direct submit or amount changes in the same REST request. Do not mark N2 complete or silently begin N3/N4/P0.10.
- Added `scripts/phase0-probe-approval.py` (readonly default, explicit localhost-only `--exercise`), two-run sanitized evidence in `phase0/evidence/n2-native-approval-20261011.json`, and `docs/NATIVE_APPROVAL_GAP.md` with actual cases, source explanation, temporary-configuration restoration and the smallest reviewable fix proposal.
- Both six-case probes exit2 as expected gap evidence, NOT acceptance pass: normal10,000 approved; normal10,000.01 rejected; manager same-request amount increase+submit, manager direct submit, creator self-submit, and manager direct submit with native items permlevel2 guard all submit10,000.01. Only Purchase Order is evidenced; do not infer other document types have been tested.
- Submitted probe orders are cancelled; unused drafts removed; the original Workflow semantics and absence of the temporary items Property Setter restored in both runs. Four unused earlier experiment drafts also removed. Cancelled synthetic orders/audit remain; no receipts/invoices/payments/stock/GL created. No unsafe release Workflow enabled.
- Docker Desktop restarted; services started using the existing Chinese overlay with `--no-build`; frontend restart cleared initial502. Health passes with ERPNext16.33.0/Frappe16.31.0/erpnext_zh0.1.1. Original purchase/stock/sales/access validators exit0; reporting twice exit0 with identical stdout; N1 readonly config passes. AR75/AP60 and original stock/GL remain intact. P0.6 access success covers only its original narrow tests and does NOT override the new negative evidence.
- Smallest unblock action: owner approval of the isolated server-side approval guard proposed in `docs/NATIVE_APPROVAL_GAP.md`, as an N2 dependency, followed by R1 scope/DEC amendment and implementation. No Core modification, external API/MCP/Agent, or mixing business controls into the Chinese presentation app is proposed. The confirmation request cites FIRST_RELEASE_SCOPE's explicit scope-amendment rule; approval is pending. Alternative: owner explicitly revises the server-side approval requirement; never silently weaken it.
- After unblocking: complete least-privilege roles/company/warehouse restrictions, full tiered approval/return/cancellation/audit negative tests, then N3 PDF/realtime/scoped Chinese UAT and N4 SOP. Real configuration mapping, migration, recovery and production UAT remain later gates. No commit/push.

### P0.9.1 / N1 execution — 2026-10-09

- Source-controlled isolated `phase0/release-baseline.json`, native REST configure/validate scripts, three safety tests and `docs/NATIVE_CONFIGURATION.md` implement the company/two-warehouse/CNY/fiscal/account/tax/master/UOM/price/credit/terms baseline without Core, global settings, permissions or P0 transaction changes.
- New R1D synthetic company uses native chart (96 accounts including one test-tax leaf), 2026 annual fiscal year, two active warehouses, four nondefault tax templates, one independent item/customer/supplier and CNY price lists. Synthetic tax5%, price60/100, limit1000 and terms30days are calculation fixtures, not real-business facts.
- First customer root-group request failed with native validation; corrected to an independent leaf group and resumed without deleting records or overwriting drift. Corrected apply passed; two readonly configuration and tax readbacks passed with identical respective stdout; final reapply creates/changes nothing.
- Four tax fixtures are draft0 only: quotations `SAL-QTN-2026-00002/00003`, purchase orders `PUR-ORD-2026-00006/00007`; included/excluded inputs both produce net100/tax5/gross105. R1D GL/stock ledger empty. Native numbering remains unchanged.
- Full offline suite18 tests passes; JSON/Python compilation passes. Original P0 reporting after N1 passes and matches pre-N1 stdout apart from logger-added final newline; AR75/AP60, six stock balances, eleven active vouchers, cancellation/return evidence unchanged. Final health passes.
- N1 technical configuration package is complete; real fiscal/account/tax/name/user mappings remain controlled deployment/UAT inputs. Missing-tax approval rejection, actual credit blocking, return/discount/period checks are not inferred from the four drafts.
- Next N2: translate R1-scope-v1 thresholds and responsibility roles into native Workflow/Role/User Permission fixtures; prove boundary values, maker/approver separation and direct API rejection. Do not submit high-impact real transactions, introduce business customization without a native gap, or silently begin N3/M1/A1.

### Latest closeout and review — 2026-10-09

- `erpnext_zh` 0.1.1 uses native Item link/field formatting and `timeline_refresh` to translate composite item titles, CNY words and historical system Info status without rewriting records. No new Core patch; original three approved source changes remain bounded by DEC-010.
- New files: `apps/erpnext_zh/erpnext_zh/display.py`, `public/js/form_display.js`, `scripts/test_phase0_form_display.js`; hooks/version/Chinese Compose image updated. Pure authenticated money conversion has no document lookup, database access or write.
- Fixed container build dependency: pinned Flit wheel with SHA-256 verification and offline installation after two container PyPI DNS failures. Subsequent build/start succeeded. Prior amount display was overwritten by native refresh; scoped formatter correction passed rendered verification.
- Actual 2026-10-09 checks: start and pre/post health exit 0; 15 Python tests; Node hook-contract checks; Node syntax/Python compilation; Chinese catalog and ten print previews; purchase, stock, sales, access and reporting validators; source UI audit; REST original-field readback all passed. Two full reporting stdout values identical. AR CNY 75 / AP CNY 60, six selected stock balances, eleven balanced active GL vouchers and cancelled-payment trace preserved. Commands/evidence are in `docs/PHASE0_VALIDATION.md`.
- Native in-app CUA browser: 1280×720 procurement form and 390×844 fresh-load first viewport; item row expands, Chinese money/status render, no blank page/framework overlay. Resize initially retained a sidebar over content; fresh narrow reload resolved it. Existing socket.io Invalid origin remains. No full mobile workflow or complete site recovery was claimed.
- P0.7 progression is recorded from the owner's direct instruction plus this local review. P0.8 is complete under delegated scope authority, not an approval of fictitious real-company facts.
- Release conditions remain open: native PDF (not retried here), realtime origin, full frozen-screen language/mobile UAT, running-site recovery, real configuration data and migration. Protected standard templates and private/free business text remain unchanged. Optional whole-site language candidates are outside R1; retain the audit queue without claiming zero English.
- Scope: one company/two warehouses/CNY/Chinese business PDF/core trading/seven native reports; no business `hardware_erp`, external integration, independent Business API/MCP/Agent. Existing presentation app remains approved. Purchase/sales thresholds 10,000; financial additional approval 20,000; all makers and approvers separated. Tax templates and real fiscal inputs require controlled P0.9 mapping and financial UAT, not a fabricated universal rate.
- Git baseline `f908acc` matched local `origin/main` before this change; no commit/push has been performed in this task and remote refs were not refreshed. Historic repository paragraphs below are prior snapshots.

The 2026-10-06 packages below are historical evidence. Their former P0.7-review and universal-language gates are superseded only by the dated R1 scope and this closeout; later release gates remain open.

### Owner-directed Chinese presentation package — 2026-10-06

The owner requested inspection of language paths and Simplified Chinese system names. This supersedes the active English-user override, retaining its historical capability evidence.

- Inventory: 7,299 source files hashed; 811 DocType metadata files inspected for 6,165 field labels and Select options. This is not a claim of manual review of every business-logic line.
- Native Translation, site/user language, Property Setters and scoped List Client Scripts translate display names without renaming keys.
- Thin `erpnext_zh` app addresses source-proven app-title/sidebar/autocomplete gaps. The first package did not change Core; the later owner-authorized ZH-3a changes three presentation source files only (DEC-010). Privileges, transactions and accounting rules remain unchanged.
- Ten Chinese print templates render through native HTTP, retaining identifiers and source/target warehouses. Uppercase currency has offline regression tests.
- All five synthetic roles now use Chinese. Permission/approval/audit, purchase, stock, sales and native-reporting regressions passed; stock and AR/AP results are unchanged.
- Use `scripts/phase0-start.sh` with the Chinese Compose overlay; base-only recreation is unsafe after app installation.
- Scope, sources/licensing, checks and limitations: `phase0/localization/README.md`.
- Final restart/browser verification passed for the Chinese list and standard-format detail names, buttons, generator labels, sidebar and autocomplete. Repeat apply reports zero translation/user-language/list-script changes. Fresh login without a forced language query resolves to Chinese; ten native Chinese print previews passed.
- Known boundaries: protected standard Print Formats reject edits; retain original internal language properties and use controlled Chinese business defaults. Optional dynamic screens/help/code examples are not exhaustively browser-tested. Existing realtime origin error and PDF download gap remain. Therefore do not claim universal zero-English coverage or close all release gates.
- Next: resolve or explicitly accept the remaining protected-template/dynamic-screen language boundary, then obtain explicit P0.7 progression review. No P0.8/Phase 1 authorization is inferred.

Historical language statements elsewhere are superseded by this dated package.

### Chinese completion sequence — owner authorized 2026-10-06

Record and push each bounded package. The owner's subsequent explicit patch request authorizes ZH-3a now for proven gaps while ZH-2 remains open; it does not authorize unrestricted Core work.

1. [x] **ZH-1 source triage:** broaden metadata-only inventory to literal Python/JavaScript gettext, metadata descriptions, direct UI sinks and template prose; compare actual Chinese session dictionary. `scripts/phase0-audit-language-ui.py` emits `phase0/localization/ui-source-audit.json` with source path/line and classification. All 7,299 Core hashes match the existing baseline. Counts are occurrences, not distinct verified defects: 27,668 translated; 2,448 missing/identity; 663 Latin-bearing translations; 744 heuristic candidates. No extraction errors reported. Health check and three offline audit tests passed. No Core, business data or runtime settings changed. Dynamic expressions, Vue scripts, template conditions and technical/code values still need manual/runtime review; this is not universal coverage.
2. [ ] **ZH-2 native translation/extensions:** inspect prioritized Desk/form/print/report candidates, fix confirmed dictionary gaps through existing native Translation and presentation extension, verify actual-session readback and rendered flows. Do not translate internal IDs or private user content.
3. [ ] **ZH-3 bounded source fallback:** owner explicitly requested patches; first bounded batch ZH-3a below is complete. Apply only for rendered defects with no native translation hook; fixed hashes, upgrade rejection and source recovery are required. Whole-site fallback/rollback acceptance remains open. Never remove standard-template protection, permissions or accounting validation.
4. [ ] **ZH-4 regression:** browser flows, Chinese print previews and existing purchase/stock/sales/access/report validators; record untested pages, failures and unchanged balances before claiming completion.

ZH-1 was committed and pushed as `6a4e7de`, following `1d73da6`. ZH-1 closeout commands: `./scripts/phase0-check.sh`; `.venv/bin/python scripts/phase0-audit-language-ui.py`; `python3 -m unittest discover -s scripts -p 'test_phase0_language_audit.py' -v`. The full remaining triage queue is committed, not a private runtime dump. P0.7 progression approval and Phase 1 remain blocked separately.

#### ZH-2a — Common form messages and Print Format help (completed 2026-10-06)

- Added 16 controlled messages in `ui-overrides.json`: mandatory-field errors, row/bulk editing, audit attribution, markdown image actions, printing warnings and printer-language help. Existing native Translation APIs apply them; no Core or business-record mutation.
- Browser evidence exposed untranslated CSS/Jinja/Bootstrap prose and corrupted code punctuation in the existing official help translation. `print-help-source.json` snapshots the two native Frappe help keys; `print-help-prose.json` translates only prose. The helper preserves source code blocks, entities and link destinations. Source remains covered by the existing Frappe MIT attribution. Protected standard formats remain unchanged.
- Extended source extraction to HTML metadata options (previously omitted); regenerated actual-session queue: 27,698 translated occurrences, 2,438 missing/identity, 670 Latin-bearing translations, 744 heuristic candidates. The increased Latin count reflects added HTML/help scope, not a claim of new defects. All 7,299 Core hashes still match; no extraction errors. These are not unique defect counts or universal coverage.
- Actual commands passed: `.venv/bin/python -m unittest discover -s scripts -p 'test_phase0*.py' -v` (8 tests); `scripts/phase0-localize.py --apply --verify` via `.venv/bin/python` (18 controlled UI entries read back from a fresh Chinese session, installed catalog coverage, 10 Chinese print previews); repeat `--apply` (zero translation/user/list-script changes); source audit; `python3 scripts/phase0-validate-reporting.py`; `./scripts/phase0-check.sh`.
- Report regression preserved AR CNY 75 / AP CNY 60, six selected stock balances, eleven active GL vouchers and cancelled-payment traceability. No new transactions. Purchase/stock/sales/access execution validators were not rerun in this small translation-only batch; full regression remains ZH-4.
- Frontend testing skill guided rendered checks. Browser plugin is absent; the supported native in-app CUA interface was used. Desktop 1280×720 at localhost:8080: Print Format list → Trial Balance Standard detail → refresh/scroll help. Correct Chinese page identity, meaningful content, no framework overlay, Chinese help and unchanged code examples verified. Screenshot: `/private/tmp/erpnext-zh-help.jpg` (temporary, not committed). Existing `socket.io: Invalid origin` persists; no new localization error observed. Mobile and other dynamic prompts were not exercised.
- **Historical next action:** ZH-2b remained open after this batch. The owner's subsequent direct patch request authorizes the proven ZH-3a defects below, not arbitrary heuristic findings. PDF generation, realtime origin, broad dynamic coverage and P0.7 review remain unresolved.

#### ZH-3a — Guarded presentation-source patch batch (completed 2026-10-06)

- Owner explicitly requested patch repairs. DEC-010 records the presentation-only exception to Core preservation; no database access, permissions, template protection, document IDs, accounting or business validation changed.
- `phase0/localization/patches/manifest.json` and `patch_core.py` implement exact three-file patches with before/after hashes and batch prevalidation. Workflow help translates its title/state/roles/actions; version timeline translates Select/workflow values only; tags retain ID/events and gain a translated accessible name. Ten new controlled dictionary entries also close native onboarding/state gaps.
- Dockerfile builds all three apps (`frappe,erpnext,erpnext_zh`) and complete asset manifest; Compose uses distinct `16.33.0-0.1.0-p1`. First two-app asset build caused `setup_tax_filters` undefined and incomplete procurement form; correction rebuilt ERP assets too, then restart/rendered checks passed. The first failed build is not acceptance evidence.
- Audit scripts retain the immutable upstream inventory and recognize exactly three approved changed files; 7,296 others match. Source inventory regeneration refuses patched targets. Actual queue: 27,706 translated / 2,431 missing-or-identity / 670 Latin-bearing / 743 heuristic occurrences, no extraction errors. These are not unique verified defects.
- Executed: `./scripts/phase0-start.sh`; `.venv/bin/python scripts/phase0-localize.py --verify` (28 controlled UI entries and 10 Chinese print previews); `.venv/bin/python scripts/phase0-audit-language-ui.py`; `.venv/bin/python scripts/phase0-validate-{purchase,stock,sales,access,reporting}.py` separately (all exited 0, reused fixtures, unchanged stock, AR 75/AP 60, 11 active balanced GL vouchers).
- Offline full suite: 15 tests passed. Exact source forward/reverse and Node syntax checks passed for all three patched files. `APPLY_ZH_SOURCE_PATCHES=0` recovery image built successfully; isolated container verified original three upstream hashes and complete framework/ERP bundle manifest. `phase0-audit-language-source.py` on the patched runtime deliberately exited 1 with `Cannot overwrite upstream baseline with patched/drifted sources`; original inventory remained unchanged. Final `./scripts/phase0-check.sh` and `git diff --check` passed. Full running-site recovery was **not** exercised; source recovery is not database rollback.
- Frontend testing skill guided native CUA desktop 1280×720 QA at localhost:8080: procurement form renders; onboarding steps, version status change, tag accessible name and workflow help are Chinese; help opens without changing approval state. Corrected reload no longer logs the ERP-module error; existing socket.io Invalid origin persists. Small-screen and optional pages remain untested.
- **First next bounded package:** close the observed item composite-title, stored English in-words display and English historical activity text through safe presentation/native hooks, without rewriting submitted/private data. Then continue ZH-2b dynamic candidates and full ZH-4 coverage. These residuals, protected-template policy, PDF/realtime failures and P0.7 owner review remain open. Do not claim full-site zero English or start P0.8/Phase 1.

### Phase boundary directive — 2026-10-03

The project owner has reset the delivery boundary:

- **Phase 0 is the complete development and release-candidate preparation phase.** All functionality, native configuration, approved customization, deployment-required integration, migration tooling, automated validation, and release-readiness work for the first deployable ERP release must be completed and accepted here.
- **Phase 1 is the deployment and rollout phase.** It may provision environments, apply the accepted release, migrate approved data, execute deployment/UAT/cutover procedures, and stabilize operations. It must not be used to finish planned product development.
- P0.7 is only the first remaining Phase 0 gate. Passing P0.7 authorizes scope freeze and implementation planning, not progression to Phase 1.
- A Phase 1 deployment defect that requires a business-logic, schema, custom-app, report, integration-contract, or migration-code change must return to Phase 0, produce a new release candidate, and repeat the affected acceptance gates.
- Future Agent, MCP, and multi-Agent work is not silently pulled into the first ERP release. It remains deferred unless the project owner explicitly adds it to the Phase 0 release scope.

`docs/ROADMAP.md` and `docs/DECISIONS.md` now record this phase boundary at milestone level. This handoff remains the source for the ordered daily execution plan; P0.8 must refine the approved first-release scope without moving development into Phase 1.

Simplified Chinese is the native site default, with a proven English per-user override. Native role separation and configurable approval/audit workflows passed. `AR-004`, `AP-004`, and `REP-001` through `REP-010` have executed report evidence. Bilingual HTML print previews passed; LANG-003 remains `Configurable` because Chinese output is partly English and native PDF download failed. The Gap Analysis is complete. P0.8–P0.12, Phase 1, `hardware_erp`, Business API, MCP, Agent, and multi-Agent implementation remain uncompleted or deferred as scoped.

## P0.7 Technical Closeout — 2026-10-06

Implementation and local technical verification are complete. Two final full reporting runs exited `0` with identical stdout; JSON parsing, Python compilation, pre/post health checks, and diff review passed. This does not record owner acceptance or an independent Web GPT review. The remaining P0.7.8 item is the explicit progression review decision.

Smallest next action: review `docs/PHASE0_VALIDATION.md` and `docs/PHASE0_GAP_ANALYSIS.md`, accept or request changes to the synthetic native-discovery evidence and classified limitations, then record that decision here before changing the task to P0.8. First-release business scope and deployment readiness are separate later approvals.

P0.7 per-package trace (all listed commits pushed to `main`):

| Package | Commit | Evidence/change |
|---|---|---|
| P0.7.1 | `fb64159` | Revalidated transaction/runtime baseline |
| P0.7.2 | `e5b389c` | Native report scenarios and validator |
| P0.7.3 | `30fb27d` | Stock Balance / Stock Ledger |
| P0.7.4 | `5c96aad` | Purchase / Sales Analytics |
| P0.7.5 | `f1a17eb` | AR / AP / General Ledger |
| P0.7.6 | `95ef5bc` | Bilingual HTML previews and rendered screenshots |
| P0.7.7 | `34ded94` | Gap Analysis and purchase-return account assertions |

P0.7.8 changes reconcile this handoff and README with actual implementation, record the final command outcomes in the validation ledger, and leave the progression-review checkbox open. No roadmap phase boundary or durable architecture decision changed in this closeout.

## Review Decision — 2026-10-03

P0.5 sales, customer-return, and transaction-level Accounts Receivable evidence is accepted for progression to P0.6.

The acceptance is based on a fresh local runtime revalidation: ERPNext 16.33.0 and Frappe 16.31.0 passed the health check; the idempotent seed found all expected synthetic master data and opening stock; and two consecutive sales-validator executions exited `0`, reused every transaction document, and reproduced identical stock, outstanding-balance, payment-allocation, return, and party-GL evidence.

The first two health-check attempts returned HTTP 502 after Docker startup because the frontend retained a stale backend address. Restarting only the disposable `frontend` container refreshed its upstream address and the full health check passed. This recovery is recorded in `docs/PHASE0_VALIDATION.md`.

## Review Decision — 2026-09-05

Web GPT reviewed the latest `main` repository state after commit:

`af6b1db8a15c0278ce08888d6709a3d77d82107f` — `test: validate phase 0 purchase and stock flows`

The review found sufficient repository and recorded runtime evidence to accept the completed purchase and stock validation work and authorize progression to native sales validation.

This review did **not** independently re-run the user's local Docker/ERPNext environment. It accepts the committed implementation, validation logic, document IDs, REST/GL readback evidence, and recorded command results as sufficient handoff evidence for progression.

Repository implementation and future observed runtime behaviour continue to outrank this review if a conflict is discovered.

## Verified Current State

### Repository and collaboration state

- Repository: `kekepepe/erpnext-agent`.
- Branch: `main`.
- November features and evidence were captured in eight checkpoints from `f4ad41f` to `995da6f`. The subsequent pilot commit includes this handoff. The owner authorized pushing the batch to `origin/main`.
- Repository visibility is intentionally **public** for the current Web GPT → GitHub → Codex collaboration workflow.
- Public visibility is a collaboration requirement only. It is not permission to commit real company data.
- Only code, synthetic data, sanitized examples, non-sensitive documentation, and validation evidence may be committed.
- No independent hosted CI runtime evidence is recorded for these P0.7 checks; the prior Web GPT review recorded no Actions run or combined status for its then-reviewed commit.
- Current transaction-validation evidence therefore comes from the recorded local Phase 0 runtime execution, not an independent hosted CI ERPNext environment.

### Phase 0 environment

The repository contains a disposable ERPNext/Frappe v16 Phase 0 environment.

Configured baseline:

- ERPNext image: `frappe/erpnext:v16.33.0`
- MariaDB: `11.8`
- Redis: `6.2-alpine`
- Site: `frontend`
- Local endpoint: `http://localhost:8080`

`scripts/phase0-check.sh` validates:

- Docker availability
- Compose configuration
- `create-site` completion
- required running services
- ERPNext/Frappe 16.x versions
- HTTP ping response

Latest evidence recorded in `docs/PHASE0_VALIDATION.md`:

- runtime validation date: `2026-10-06 +0800`
- ERPNext: `16.33.0`
- Frappe: `16.31.0`
- `create-site`: exited successfully with exit code `0`
- nine required long-running services running
- HTTP ping returned `{"message":"pong"}`
- `./scripts/phase0-check.sh` exited `0`

The environment remains disposable. Every future transaction-validation task must rerun the health check rather than assume this runtime remains healthy.

### Reproducible synthetic dataset

The Phase 0 dataset is source-controlled in:

- `phase0/synthetic-data.json`

It is applied through:

- `scripts/phase0-seed.py`

The seed uses authenticated ERPNext REST APIs rather than direct database access.

Verified dataset:

- company:
  - `Phase Zero Hardware Trading Demo`
  - abbreviation `PZH`
  - China
  - CNY
- 2 P0 warehouses
- 4 P0 item groups
- Piece, Box, and Carton UOM coverage
- 3 P0 suppliers
- 3 P0 customers
- 20 P0 stock items
- 40 Item Price records
  - one Standard Buying price per item
  - one Standard Selling price per item
- 18 non-zero opening-stock item rows
- 2 intentionally zero-stock items
- submitted Opening Stock Stock Reconciliation:
  - `MAT-RECO-2026-00001`
- multi-level UOM example:
  - `P0-CO-SCREW`
  - Piece = `1`
  - Box = `50`
  - Carton = `500`

A final recorded rerun of:

    python3 scripts/phase0-seed.py

exited `0`, found all expected entities as existing, and did not create duplicate opening-stock transactions.

### Native purchase validation

Native purchase-flow validation passed on 2026-09-05 through:

- `phase0/purchase-validation.json`
- `scripts/phase0-validate-purchase.py`

Recorded supported cases:

- `PUR-001` through `PUR-010`
- `RET-002`
- `RET-004`
- `AP-001`
- `AP-002`
- `AP-003`
- `AP-005`

Recorded execution evidence includes:

- Purchase Orders:
  - `PUR-ORD-2026-00001`
  - `PUR-ORD-2026-00002`
  - `PUR-ORD-2026-00003`
- Purchase Receipts:
  - `MAT-PRE-2026-00001` through `MAT-PRE-2026-00004`
- Purchase Return:
  - `MAT-PRE-2026-00005`
  - linked to `MAT-PRE-2026-00004`
- Purchase Invoices:
  - `ACC-PINV-2026-00001` — CNY 152
  - `ACC-PINV-2026-00002` — CNY 120
- Payment Entries:
  - `ACC-PAY-2026-00001` — fully allocated CNY 152
  - `ACC-PAY-2026-00002` — partially allocated CNY 60
- final invoice outstanding balances:
  - CNY 0
  - CNY 60
- final tested main-warehouse balances:
  - hammer: 28
  - screwdriver: 58
  - screw: 650 Piece
- GL evidence proved:
  - supplier payable creation
  - full settlement
  - partial settlement
  - corresponding cash entries
- alternate-UOM purchase:
  - 2 Box of screws converted to 100 Piece
- purchase return:
  - 1 Box converted to -50 Piece

Preserve the existing CNY 60 open supplier payable. It is useful later for `AP-004` and reporting validation.

### Native stock validation

Native stock validation passed on 2026-09-05 through:

- `phase0/stock-validation.json`
- `scripts/phase0-validate-stock.py`

All `STK-001` through `STK-010` are recorded as `Supported`.

Recorded evidence includes:

- Opening Stock:
  - `MAT-RECO-2026-00001`
  - 18 document rows
  - 18 matching Stock Ledger Entry resulting balances
- Delivery Note:
  - `MAT-DN-2026-00001`
  - reduced `P0-AC-BITSET` from 20 to 18 Piece
- Material Transfer:
  - `MAT-STE-2026-00001`
  - moved 3 `P0-AC-GOGGLES`
  - main warehouse final quantity 12
  - secondary warehouse final quantity 3
- Stock Reconciliation:
  - `MAT-RECO-2026-00002`
  - adjusted `P0-AC-TOOLBOX` from 6 to 5 Piece
  - valuation rate CNY 95
- zero-stock / insufficient-stock evidence:
  - ERPNext rejected submission of `MAT-DN-2026-00002`
  - tested item: `P0-PT-SAW`
  - quantity remained zero
- item-level balances matched source-controlled expectations
- warehouse-level query returned:
  - 18 non-zero items in main warehouse
  - 3 goggles in secondary warehouse
- a second complete validator run reused existing documents and reproduced the same balances without duplicate stock movements

### Native sales, customer-return, and Accounts Receivable validation

Native sales validation passed on 2026-09-06 through:

- `phase0/sales-validation.json`
- `scripts/phase0-validate-sales.py`

Recorded supported cases:

- `SAL-001` through `SAL-010`
- `RET-001`
- `RET-003`
- `RET-005`
- `AR-001`
- `AR-002`
- `AR-003`
- `AR-005`

Recorded execution evidence includes:

- Quotation `SAL-QTN-2026-00001`
- Sales Orders `SAL-ORD-2026-00001` through `SAL-ORD-2026-00003`
- outbound Delivery Notes `MAT-DN-2026-00003` through `MAT-DN-2026-00006`
- customer return Delivery Note `MAT-DN-2026-00007`, linked to `MAT-DN-2026-00006`
- Sales Invoices `ACC-SINV-2026-00001` through `ACC-SINV-2026-00003`
- credit note `ACC-SINV-2026-00004`, linked to `ACC-SINV-2026-00003`
- customer Payment Entries `ACC-PAY-2026-00003` and `ACC-PAY-2026-00004`
- full-payment invoice total CNY 84 and final outstanding CNY 0
- partial-payment invoice total CNY 125, payment CNY 50, and preserved outstanding CNY 75
- alternate-UOM delivery of 1 Box converted to 50 Piece
- return of -1 Box / -50 Piece restored the screw balance to 650 Piece
- party-specific receivable GL debits of CNY 84, 125, and 32.5
- payment receivable GL credits of CNY 84 and 50
- credit-note receivable GL credit of CNY 32.5
- final main-warehouse quantities: pliers 16, measuring tape 25, screws 650 Piece

The first transaction-producing run created all documents but failed its final assertion because it expected a fully returned Sales Order to remain 100% delivered. Observed ERPNext v16 behaviour correctly represents the returned order as net `per_delivered = 0`, `status = To Deliver`. The assertion was corrected, and two following complete runs exited `0`, reused every document, and reproduced identical final evidence without duplicate effects.

`AR-004` remains `Not Tested`: the open CNY 75 receivable was preserved for the later reporting task, but no Accounts Receivable report was executed here.

### API boundary already demonstrated during Phase 0

The reusable client:

- `scripts/phase0_api.py`

uses ERPNext HTTP REST resources and explicitly called whitelisted ERPNext methods.

Current Phase 0 scripts do **not** require direct MariaDB access to perform tested transactions.

This is consistent with the architectural constraint that future automation must operate through reviewed ERP service/API boundaries.

Do not interpret the current Phase 0 REST client as the final Business API layer. The governed Business API remains a later phase.

### Areas still not proven

No valid execution evidence currently proves completion of:

- fully localized formal customer/supplier-facing output and downloadable PDF output
- explicit P0.7 progression review acceptance
- approved first-release scope and Phase 0 development plan
- production-ready native configuration and any approved `hardware_erp` customization
- migration rehearsal, release candidate, and deployment-readiness acceptance
- Phase 1 deployment and rollout
- `hardware_erp` Custom App
- governed Business API
- MCP Server
- Agent implementation
- multi-Agent orchestration

These must remain incomplete until actual evidence exists.

`ERP与AI智能体设计笔记.md` remains architectural intent and product direction only. It is not implementation evidence.

## Completed

- [x] Selected ERPNext/Frappe v16 as the ERP Core direction.
- [x] Initially defined native-capability discovery; expanded Phase 0 to complete first-release development and release preparation under DEC-008.
- [x] Bootstrapped a disposable local ERPNext v16 validation environment.
- [x] Pinned Phase 0 container images.
- [x] Added startup and teardown instructions.
- [x] Added `scripts/phase0-check.sh`.
- [x] Recorded historical successful runtime baseline on 2026-08-30.
- [x] Revalidated the Phase 0 runtime.
- [x] Established GitHub as the daily Web GPT ↔ GitHub ↔ Codex coordination channel.
- [x] Established `AGENTS.md`, `docs/AI_HANDOFF.md`, `docs/ROADMAP.md`, and `docs/DECISIONS.md`.
- [x] Established Obsidian as milestone knowledge storage rather than per-task coordination.
- [x] Confirmed public repository visibility is intentional for the current collaboration workflow.
- [x] Added a reproducible REST API seed.
- [x] Initialized the synthetic Phase 0 company and representative master data.
- [x] Initialized 20 items.
- [x] Initialized 3 suppliers.
- [x] Initialized 3 customers.
- [x] Initialized 2 warehouses.
- [x] Initialized 40 buying/selling Item Price records.
- [x] Initialized meaningful Piece / Box / Carton UOM scenarios.
- [x] Submitted reproducible opening stock.
- [x] Established `docs/PHASE0_VALIDATION.md`.
- [x] Executed native purchase validation `PUR-001` through `PUR-010`.
- [x] Verified full receipt.
- [x] Verified multiple partial receipts.
- [x] Verified alternate-UOM purchasing.
- [x] Verified Purchase Invoice and supplier payable creation.
- [x] Verified full supplier payment.
- [x] Verified partial supplier payment.
- [x] Verified purchase return.
- [x] Executed native stock validation `STK-001` through `STK-010`.
- [x] Verified opening-stock ledger evidence.
- [x] Verified delivery stock reduction.
- [x] Verified warehouse transfer.
- [x] Verified stock reconciliation.
- [x] Verified zero-stock query behaviour.
- [x] Verified native insufficient-stock rejection.
- [x] Verified item-level and warehouse-level stock queries.
- [x] Verified purchase and stock validators can be rerun without duplicating their tested stock movements.
- [x] Web GPT reviewed the committed purchase/stock evidence on 2026-09-05 and accepted progression to the sales-validation task.
- [x] Added reproducible source-controlled sales-validation scenarios.
- [x] Executed native sales validation `SAL-001` through `SAL-010`.
- [x] Verified Quotation to Sales Order mapping, full delivery, and multiple partial deliveries.
- [x] Verified alternate-UOM selling and the 1 Box to 50 Piece stock effect.
- [x] Verified Sales Invoice receivable creation and full/partial customer settlement.
- [x] Executed and traced customer stock return and Sales Invoice credit-note accounting.
- [x] Executed and recorded `RET-001`, `RET-003`, `RET-005`, `AR-001`, `AR-002`, `AR-003`, and `AR-005`.
- [x] Verified two complete post-correction sales-validator runs reused all documents without duplicate stock or accounting movement.
- [x] Configured Simplified Chinese as the native site default and verified a persistent per-user English override.
- [x] Added five synthetic System Users for purchase, sales, stock, finance, and approval validation.
- [x] Executed `PER-001` through `PER-006` with positive and denied authenticated REST checks.
- [x] Configured and executed native Purchase Order, Sales Order, and Payment Entry Workflows.
- [x] Verified creator/manager separation, submit/cancel transitions, owner/modified-by attribution, and Version audit evidence.
- [x] Re-ran the P0.6 validator idempotently and re-ran P0.5 sales/AR regression successfully.
- [x] Executed native stock, purchase, sales, AR/AP, and General Ledger reports with source-voucher/REST traceability.
- [x] Verified bilingual HTML print previews and recorded localization/PDF limitations.
- [x] Completed evidence-based Gap Analysis and two identical final reporting regression runs.

## In Progress

- [x] P0.7.8 progression and P0.8 scope freeze recorded on 2026-10-09.
- [x] P0.9.1 / N1 synthetic native configuration baseline completed.
- [x] Execute P0.9.2 / N2 native role/approval package; real mapping and release UAT remain pending.

### P0.7.7 execution record — 2026-10-06

Completed the evidence-based `docs/PHASE0_GAP_ANALYSIS.md`: six configuration/process/operational items, each with impact, evidence, implementation path, owner role, and P0.8/P0.9/P0.12 disposition. No executed case currently justifies `hardware_erp` or ERPNext Core modification.

Extended `phase0/reporting-validation.json` and `scripts/phase0-validate-reporting.py` to assert the purchase return's submitted status, `is_return`, original receipt linkage, exact GL accounts, and CNY 17.5 debit/credit reversal. Updated `docs/PHASE0_VALIDATION.md` with that evidence and the native-discovery conclusion.

JSON parsing and Python compilation passed. Two complete reporting-validator runs exited `0` and their full outputs were identical, including all four print-preview hashes. Health checks before and after those runs exited `0`. P0.7.8 documentation reconciliation and review-gate closeout follow this work package.

## Problems / Risks

### Runtime lifecycle

The Phase 0 environment is disposable.

A previous Docker Desktop stopped-state blocker was resolved, but that does not prove Docker is running for the next task.

For any future transaction validation:

- check Docker
- start/reuse the Phase 0 stack
- run `./scripts/phase0-check.sh`
- stop if runtime health cannot be re-established

Do not claim current runtime health from an old timestamp.

### Shared mutable Phase 0 dataset

Purchase and stock validation intentionally changed synthetic inventory and accounting state.

The sales validator uses the **current validated state** and scenarios whose final state can be deterministically read back after execution.

Do not assume original opening quantities still exist.

Prefer dedicated scenario customers/items or explicit baseline reads so that one validator does not make another validator's expected state ambiguous.

### Idempotency

Submitted ERPNext transactions are not disposable individual API calls.

A rerun must:

- detect already-created scenario documents
- verify their contents
- reuse them when they match
- avoid submitting duplicate Sales Orders, Deliveries, Invoices, Payments, or Returns
- fail visibly when an existing document conflicts with source-controlled expectations

Do not obtain apparent idempotency by silently skipping validation.

### Accounts Receivable evidence

A submitted Sales Invoice alone is not sufficient proof of AR behaviour.

The validator should verify, where ERPNext exposes appropriate native evidence:

- submitted Sales Invoice
- customer
- grand total
- outstanding amount
- receivable GL posting
- full-payment settlement
- partial-payment settlement
- Payment Entry references
- traceability back to the source sales document

Do not infer accounting correctness from document status alone.

### Sales return evidence

A sales return must not be treated as proven merely because ERPNext exposes a return button or method.

Execution evidence should verify:

- returned quantity
- source-document linkage
- negative/return quantity semantics
- restored inventory where applicable
- accounting reversal/credit effect where applicable
- resulting outstanding balance or credit behaviour if an invoice return is used

Use native whitelisted ERPNext operations where possible.

Preserve any failed method/API attempt in the evidence ledger.

### UOM conversion

At least one sales scenario must exercise an alternate UOM against a Piece stock UOM.

A suitable existing dataset example is:

- `P0-CO-SCREW`
- 1 Box = 50 Piece
- 1 Carton = 500 Piece

The validator must compare sales UOM quantity with resulting stock quantity rather than only checking the displayed order UOM.

### Public repository boundary

Never commit:

- production passwords
- API tokens
- reusable credentials
- real customer data
- real supplier data
- real internal prices
- confidential contracts
- personal information
- non-public financial data
- production exports

Only synthetic/sanitized Phase 0 evidence may be recorded.

### No independent CI ERPNext execution

The latest reviewed commit has no recorded GitHub Actions execution or combined commit status.

This is not a blocker for the current local Phase 0 validation workflow.

Do not describe the local ERPNext transaction evidence as independently reproduced by hosted CI.

Static CI may be added later if useful, but do not let CI infrastructure work displace the current Phase 0 evidence task.

### Premature customization

Do not create:

- Custom Fields
- Custom DocTypes
- Server Scripts
- Frappe Custom App
- custom reports
- ERPNext Core modifications

unless a later evidence-based Gap Analysis establishes that native configuration/process behaviour is insufficient.

### Premature Agent/API work

Do not start:

- `hardware_erp`
- production/staging architecture
- Business API design implementation
- MCP Server
- Agent
- multi-Agent orchestration

during the current task.

## Next Actions

### 当前 P0 执行队列（下方 P0.5 等为历史检查表）

- [x] Git 检查点：归档 105 个既有文件，完成敏感信息复核及基线验证。
- [x] W6 Business API v1 契约、本机合成接口与两张录单表单；桌面和窄屏浏览器联调通过。
- [ ] W6 ERPNext 适配：在隔离站验证真实用户会话和原生草稿，检查仓库权限、草稿更新与过账边界；真实岗位和首发范围待确认。
- [x] W0/W1/W2：环境、权限后端、导航框架及基础浏览器验证。
- [x] C0：全新隔离安装、双次迁移、实际停写后卸载重装、双轮回归及脱敏证据归档。
- [x] W3/W5 技术复验：两种尺寸各 38 项、详情语义和岗位权限通过。
- [ ] W4：岗位确认术语、真实异常流程与使用反馈。
- [ ] M1：受控组织/身份/会计映射、完整主数据与期初导入、两次独立演练和失败恢复；合成六单两站/四表七行及中断续跑已通过；完整真实期初和岗位确认仍待输入。
- [ ] A1/W6：合成批次已异站恢复并回读，合成匹配版本回退与十类正式 PDF 已复验；待真实环境容量、实际岗位 UAT、不可变RC与发布准入。Phase 1仍未开始。


## P0 — Current Phase

### P0.5 — Native Sales + Accounts Receivable Validation

This Codex task is complete, revalidated, and accepted as of 2026-10-03.

Execute in this order.

#### P0.5.1 — Inspect and re-establish runtime

- [x] Read:
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/AI_HANDOFF.md`
  4. `docs/ROADMAP.md`
  5. `docs/DECISIONS.md`
  6. `docs/PHASE0_VALIDATION.md`
- [x] Inspect actual Git state.
- [x] Preserve unrelated user changes if the worktree is dirty.
- [x] Confirm the current branch and relationship to `origin/main`.
- [x] Inspect the existing seed, purchase validator, stock validator, REST client, and validation JSON files before designing the sales validator.
- [x] Check Docker availability.
- [x] Start/reuse the Phase 0 stack if necessary:

    docker compose -f phase0/compose.yaml up -d

- [x] Run:

    ./scripts/phase0-check.sh

- [x] Record actual command outcome and runtime evidence.
- [x] If runtime validation fails, preserve the failure and stop transaction work until the smallest concrete blocker is resolved.
- [x] Do not mark runtime validation successful unless the command actually passes.

#### P0.5.2 — Revalidate required synthetic master data

- [x] Run the existing seed idempotently:

    python3 scripts/phase0-seed.py

- [x] Confirm required customers, items, warehouses, selling prices, and UOM conversions still exist.
- [x] Do not reset the database merely to simplify the sales test.
- [x] Do not destroy existing purchase/stock evidence with `down -v`.
- [x] Preserve the CNY 60 open payable unless there is a documented reason the current task requires otherwise.

#### P0.5.3 — Define reproducible sales scenarios

Add the smallest coherent source-controlled sales scenario definition, expected to be similar in role to:

- `phase0/purchase-validation.json`
- `phase0/stock-validation.json`

A likely new file is:

- `phase0/sales-validation.json`

Use only synthetic existing P0 entities.

The scenario set should cover at minimum:

- one standard full-delivery/full-payment sale
- one partial/multiple-delivery and partial-payment sale
- one alternate-UOM sale
- one customer return tied to a previously executed sale

Do not invent extra business requirements merely to increase test count.

The scenario file must define expected quantities, UOMs, rates, customers, warehouses, and payment expectations clearly enough for deterministic validation.

#### P0.5.4 — Implement native sales validator

Add the smallest coherent validator, expected to be similar in role to:

- `scripts/phase0-validate-purchase.py`
- `scripts/phase0-validate-stock.py`

A likely new file is:

- `scripts/phase0-validate-sales.py`

Reuse `scripts/phase0_api.py` where practical.

Extend shared API helpers only when required by an actual sales-validation need.

Use:

- authenticated ERPNext REST resources
- whitelisted native ERPNext mapping/action methods where required

Do not:

- access MariaDB directly
- patch ERPNext Core
- bypass ERPNext validation/business rules
- create custom DocTypes/fields to make a test pass

#### P0.5.5 — Execute `SAL-001` through `SAL-010`

Validate the existing ledger cases exactly rather than replacing them with a new numbering scheme.

Required coverage:

- [x] `SAL-001` — Create Quotation
- [x] `SAL-002` — Create and submit Sales Order
- [x] `SAL-003` — Deliver full Sales Order quantity
- [x] `SAL-004` — Deliver one Sales Order through multiple partial deliveries
- [x] `SAL-005` — Sell an item using an alternate UOM with conversion
- [x] `SAL-006` — Delivery correctly reduces stock
- [x] `SAL-007` — Create Sales Invoice
- [x] `SAL-008` — Sales Invoice creates Accounts Receivable
- [x] `SAL-009` — Record full customer payment
- [x] `SAL-010` — Record partial customer payment

For each case, record:

- prerequisites
- execution steps
- expected result
- actual result
- relevant document IDs
- REST readback
- stock balance evidence where relevant
- GL/outstanding-balance evidence where relevant
- result state:
  - `Supported`
  - `Configurable`
  - `Gap`
  - `Not Tested`
- notes/failures

Do not force all cases to become `Supported`. The purpose is capability discovery.

#### P0.5.6 — Execute customer sales-return evidence

Validate:

- [x] `RET-001` — Customer returns previously sold goods
- [x] `RET-003` — Sales return reverses stock effects correctly
- [x] `RET-005` — Return-related accounting effects are traceable

Where native ERPNext behaviour separates stock return and invoice/credit accounting behaviour, record that distinction rather than merging different native concepts into a false single workflow.

Document the exact native return path used.

#### P0.5.7 — Execute Accounts Receivable evidence

Validate transaction-level AR cases:

- [x] `AR-001` — Sales Invoice creates customer receivable
- [x] `AR-002` — Full payment clears customer outstanding balance
- [x] `AR-003` — Partial payment reduces outstanding balance correctly

If the current transaction execution also directly proves `AR-005`, record the evidence and result.

Do **not** mark:

- `AR-004` — Outstanding receivables can be reported

as complete unless a real reporting query/report is executed and its output is checked. Reporting is otherwise reserved for the later reporting task.

#### P0.5.8 — Prove idempotency

After the first complete successful execution, run the complete sales validator again.

The second run must:

- reuse matching existing transaction documents
- not duplicate stock movement
- not duplicate accounting movement
- return the same expected final state
- fail if existing documents conflict with the source-controlled scenario

Record the second-run result explicitly.

#### P0.5.9 — Update Phase 0 evidence

Update `docs/PHASE0_VALIDATION.md` in the same implementation change.

For each executed case:

- replace `Not Tested` only when valid execution evidence exists
- preserve failed attempts
- preserve blocked attempts
- preserve unexpected native behaviour
- record document IDs
- record actual balances
- record accounting evidence
- record idempotent rerun evidence

Do not rewrite failed exploration attempts as if they never happened.

#### P0.5.10 — Close out the Codex task

Before handoff:

- [x] Run appropriate JSON validation.
- [x] Run Python compilation/static syntax validation for changed scripts.
- [x] Run `./scripts/phase0-check.sh`.
- [x] Run the seed.
- [x] Run the complete sales validator.
- [x] Run the complete sales validator a second time.
- [x] Review `git diff`.
- [x] Review `git status`.
- [x] Update this `docs/AI_HANDOFF.md` with actual results.
- [x] Record exact changed files.
- [x] Record all relevant document IDs.
- [x] Record outstanding balances.
- [x] Record final affected stock balances.
- [x] Record GL evidence where applicable.
- [x] Record failures and corrections.
- [x] Recommend the next Phase 0 task based on evidence.
- [x] Do not start permissions/reporting work unless this handoff has first been completed.
- [x] Do not start Phase 1+ work.

### P0.6 — Permissions, Roles, Approval and Audit Validation

P0.6 is complete as of 2026-10-03.

Planned next scope:

- [x] Set native System Settings language to Simplified Chinese.
- [x] Validate a representative user's native language override to English and persistence after a new login.
- [x] Record untranslated UI, data, and print-output boundaries without adding a custom language switcher.
- [x] Define representative synthetic Phase 0 roles/users if required.
- [x] Validate relevant purchase permissions.
- [x] Validate relevant sales permissions.
- [x] Validate stock-operation permissions.
- [x] Validate accounting/payment permissions.
- [x] Verify create/read/write/submit/cancel boundaries relevant to the MVP.
- [x] Validate native ERPNext approval/workflow options where relevant.
- [x] Validate approval history / Version / audit trace where applicable.
- [x] Classify results as `Supported`, `Configurable`, `Gap`, or `Not Tested`.
- [x] Avoid customization before the result is known.

### P0.7 — Reporting Validation and Gap Analysis

P0.7 implementation and technical closeout are complete. Its explicit progression review remains the first unchecked P0 item.

Execute the following work packages in order. Do not begin implementation of confirmed gaps or Phase 1 deployment while any P0.7 package remains incomplete.

#### P0.7.1 — Re-establish the evidence baseline

- [x] Run `./scripts/phase0-check.sh` and record the current runtime result.
- [x] Run `scripts/phase0-seed.py` idempotently.
- [x] Re-run purchase, stock, sales, and access validators when required to prove that the reporting source transactions and configuration still match their recorded state.
- [x] Confirm the preserved CNY 60 supplier payable and CNY 75 customer receivable still exist.
- [x] Preserve cancelled P0.6 approval fixtures as audit evidence; do not include their reversed amounts in open-balance expectations.

#### P0.7.2 — Define reproducible reporting scenarios

- [x] Add the smallest source-controlled reporting expectation file, `phase0/reporting-validation.json`.
- [x] Add an idempotent native-report validator, `scripts/phase0-validate-reporting.py`.
- [x] Use ERPNext report/query APIs and reviewed REST boundaries; do not query MariaDB directly.
- [x] Define expected rows, quantities, parties, vouchers, and balances before marking a report supported.
- [x] Treat a report name or visible menu item as insufficient evidence without executing and checking its output.

#### P0.7.3 — Validate stock reporting

- [x] `REP-001` — Stock Balance reports current quantity by item.
- [x] `REP-002` — Stock Balance or equivalent native output separates warehouse quantities correctly.
- [x] Validate Stock Ledger movement history for opening stock, receipt, delivery, transfer, reconciliation, and return documents.
- [x] Trace selected report quantities back to their Stock Ledger Entry and source voucher identifiers.

#### P0.7.4 — Validate purchase and sales reporting

- [x] `REP-003` — Purchase history/status can be reported by supplier.
- [x] `REP-004` — Purchase history/status can be reported by item.
- [x] `REP-005` — Sales history/status can be reported by customer.
- [x] `REP-006` — Sales history/status can be reported by item.
- [x] Verify report totals and quantities against the already validated Purchase Orders and Sales Orders; preserve receipt, delivery, and return traceability under Stock Ledger evidence.
- [x] Record how cancelled P0.6 fixtures appear or are excluded.

#### P0.7.5 — Validate AR, AP, and General Ledger reporting

- [x] `AR-004` / `REP-007` — Accounts Receivable reports the preserved CNY 75 customer balance against the correct invoice and customer.
- [x] `AP-004` / `REP-008` — Accounts Payable reports the preserved CNY 60 supplier balance against the correct invoice and supplier.
- [x] `REP-009` — General Ledger reports the expected invoice, payment, credit-note, and cancellation postings.
- [x] `REP-010` — Selected report balances trace back to native source vouchers without manual database lookup.
- [x] Confirm the cancelled CNY 1 P0.6 Payment Entry has no net open-balance effect while its audit/accounting reversal remains traceable.

#### P0.7.6 — Close the remaining language/output boundary

- [x] `LANG-003` — Execute Chinese and English print/preview output for representative purchase and sales documents.
- [x] Distinguish interface translation, saved master/transaction data, standard print labels, and custom translated content.
- [x] Classify bilingual output as `Configurable` from actual rendered evidence; record the mixed-language standard format and failed PDF generation separately.
- [x] Do not build custom print formats merely to force a passing Phase 0 result.

#### P0.7.7 — Produce the evidence-based Gap Analysis

- [x] Review every `Not Tested`, `Configurable`, failed, or unexpected case in `docs/PHASE0_VALIDATION.md`.
- [x] Create `docs/PHASE0_GAP_ANALYSIS.md` only after the report and bilingual-output evidence above exists.
- [x] Classify each confirmed issue as native configuration, acceptable process adjustment, integration, customization, deferment, or unresolved investigation.
- [x] Record business impact, evidence, workaround, recommended owner, and Phase 0 implementation or explicit post-release deferral for each item.
- [x] Do not classify a preference as a technical gap without execution evidence.

#### P0.7.8 — P0.7 closeout and review gate

- [x] Run JSON validation and Python compilation for every new or changed scenario/validator.
- [x] Run the complete reporting validator twice and prove idempotent read-only results.
- [x] Re-run `./scripts/phase0-check.sh`.
- [x] Review `git diff`, `git diff --check`, and `git status`.
- [x] Update `docs/PHASE0_VALIDATION.md`, this handoff, and the Gap Analysis with actual results and failures.
- [x] Confirm the native-discovery subset of Phase 0 exit criteria in `docs/ROADMAP.md` has evidence; the complete development/release criteria remain pending P0.8–P0.12.
- [x] Owner-directed P0.7 progression and local evidence review recorded 2026-10-09; Phase remains 0.

Expected P0.7 deliverables:

- `phase0/reporting-validation.json`
- `scripts/phase0-validate-reporting.py`
- updated `docs/PHASE0_VALIDATION.md`
- `docs/PHASE0_GAP_ANALYSIS.md` after evidence is sufficient
- updated `docs/AI_HANDOFF.md`

P0.7 must remain read-only with respect to validated business transactions wherever possible. It may create only narrowly scoped report/print evidence when native execution requires it, and must preserve all existing P0 balances and audit fixtures.

### P0.8 — First-release scope freeze and phase-document alignment

Begin only after P0.7 evidence and the Gap Analysis are reviewed. This gate turns evidence into an approved, testable first-release scope.

- [x] Build a requirement-to-evidence matrix for purchase, stock, sales, returns, AR, AP, reporting, language/print, permissions, approvals, audit, and required operating controls.
- [x] For every confirmed requirement, record one disposition: native configuration, process/SOP, `hardware_erp` customization, deployment-required integration, or explicit post-release deferral.
- [x] Label each item `Must`, `Should`, or `Deferred`; no `Must` item may have an unresolved owner, acceptance criterion, or implementation path.
- [x] Define measurable acceptance criteria and the validation layer for every `Must` and accepted `Should` item.
- [x] Freeze the first-release functional scope, supported organization structure, roles, approval matrix, language/print boundary, reports, and data-migration scope.
- [x] Decide whether `hardware_erp` is required. If no confirmed gap requires it, record that the first release remains native/configuration-only.
- [x] Explicitly decide whether any external integration or governed Business API is required for the first deployment. Keep MCP and Agent work deferred unless separately approved by the project owner.
- [x] Verify that the approved first-release scope remains consistent with the Phase 0 development / Phase 1 deployment boundary in `docs/ROADMAP.md`.
- [x] Refine `docs/DECISIONS.md` only if P0.8 introduces another durable architecture, security, or workflow decision beyond the recorded phase boundary.
- [x] Update this handoff so the first unchecked P0 item is the first approved implementation package.

P0.8 deliverables:

- approved requirement-to-evidence and scope matrix
- updated `docs/PHASE0_GAP_ANALYSIS.md`
- confirmed phase alignment across `docs/ROADMAP.md`, `docs/DECISIONS.md`, and this handoff
- ordered Phase 0 implementation backlog with owners and acceptance evidence

P0.8 completed 2026-10-09 under explicit delegated scope authority. Deliverable: `docs/FIRST_RELEASE_SCOPE.md` (R1-scope-v1). Implementation and production UAT are not completed by this scope freeze. First package is N1 / P0.9.1; all real data stays outside the public repository.

### P0.9 — Complete native ERP configuration and operating model

Implement and source-control every approved native/configuration-first requirement before writing custom code for the same need. N1–N4 technical packages completed 2026-10-12. Real-business mapping/acceptance remains a release gate, not a claimed N1 production deployment.

- [x] P0.9.1 / N1: implement and twice verify the isolated native organization/fiscal/account/tax/master/UOM/pricing/terms/credit technical baseline; real mapping and UAT remain explicitly pending in `docs/NATIVE_CONFIGURATION.md`.
- [x] Finalize least-privilege roles, User Permissions, approval thresholds, Workflows, segregation of duties, and audit retention settings. **Complete 2026-10-12:** native controls plus the approved guard dependency (DEC-012) verified; real UAT remains A1.
- [x] Finalize required native reports, dashboards, print formats, language settings, and customer/supplier-facing output.
- [x] Store reproducible fixtures, exports, scripts, or documented configuration steps without committing secrets or real business records.
- [x] Write operator SOPs for master data, purchase, receiving, stock, sales, returns, AR/AP, approval, reconciliation, period operations, and exception handling.
- [x] Add automated or repeatable acceptance checks and rerun affected regression validators twice where idempotency applies.
- [x] Update validation evidence and close each native/configuration item against its requirement ID.

### P0.10 — Implement only approved customization gaps

This package is conditional. Skip it with an explicit evidence-backed decision if P0.8 finds no required customization.

- [x] Create `hardware_erp` only for approved `Must`/accepted `Should` gaps that native configuration or an acceptable process cannot satisfy.
- [x] Trace every custom field, DocType, validation, report, hook, permission rule, and integration point to a frozen requirement and confirmed gap.
- [ ] Preserve ERPNext Core; do not patch core files.
- [x] Add unit/integration/permission tests, fixtures and lifecycle/rollback/upgrade notes for the approved guard; no app schema migration patch required.
- [ ] Verify fresh installation and migration on a clean environment, not only the long-lived disposable Phase 0 site.
- [ ] Run full affected workflow, accounting, stock, access, approval, audit, reporting, and print regressions.
- [ ] Resolve all release-blocking defects in Phase 0 and record remaining non-blockers as explicitly accepted deferrals.

### P0.11 — Complete deployment-required data and integration development

This package includes only capabilities required by the frozen first-release scope.

- [ ] Define source-to-target mappings, ownership, cleansing rules, reconciliation totals, rejection handling, and rollback for opening master and transaction data.
- [ ] Build and version sanitized import templates and migration tooling; never commit production exports, credentials, or private business data.
- [ ] Execute at least one representative migration rehearsal in an isolated environment and reconcile record counts, stock, AR, AP, and accounting balances.
- [ ] Implement only approved deployment-required integrations or Business API operations, with authentication, authorization, least privilege, idempotency, audit logging, error contracts, and retry/reconciliation behaviour.
- [ ] Add contract, negative-permission, failure-recovery, and replay tests for each included integration.
- [ ] Keep direct database access, MCP, Agent, and multi-Agent implementation out of the release unless separately approved in P0.8.

### P0.12 — Build and accept the deployable release candidate

P0.12 is the final Phase 0 gate. Phase 1 remains blocked until every applicable item passes or has explicit owner-approved risk acceptance.

- [ ] Rebuild the candidate from source on a clean, production-like staging environment using documented, repeatable steps.
- [ ] Pin and inventory ERPNext/Frappe, custom app, OS/container, database, queue, and other dependency versions.
- [ ] Run the complete functional regression suite covering purchase, stock, sales, returns, AR/AP, reporting, print, permissions, approvals, audit, customization, integration, and migration scope.
- [ ] Execute security and operational checks for secrets, least privilege, TLS assumptions, session/authentication settings, auditability, logging, monitoring, capacity, and failure recovery.
- [ ] Prove backup and restore on an isolated environment and reconcile critical business balances after restore.
- [ ] Rehearse deployment, migration, smoke test, rollback, and disaster-recovery procedures with measured timings and named owners.
- [ ] Run business UAT against the frozen acceptance matrix and obtain owner sign-off for all release-blocking workflows.
- [ ] Produce a versioned release candidate, immutable manifest/checksums, configuration inventory, migration package, known-issues list, deployment runbook, cutover checklist, rollback plan, and support/escalation plan.
- [ ] Review `git diff`, repository status, validation evidence, open risks, and all deferred items.
- [ ] Obtain explicit deployment-readiness approval before changing `current_phase` to Phase 1.

Phase 0 is complete only when the accepted first-release scope is implemented, reproducible, regression-tested, migration-tested, recoverable, documented, and packaged as a deployable release candidate. Completion of analysis alone is not Phase 0 completion.

## P1 — Deployment and Rollout Only

Phase 1 remains blocked until P0.7 through P0.12 are complete and the deployment-readiness gate is explicitly approved.

Phase 1 may execute only the accepted release candidate and its approved runbooks:

- [ ] Provision and verify staging/production infrastructure, environment separation, domains/TLS, secret management, backups, logging, monitoring, and access ownership.
- [ ] Install the exact accepted ERPNext/Frappe and `hardware_erp` release versions from the Phase 0 manifest.
- [ ] Apply the approved configuration and execute the rehearsed migration/import process.
- [ ] Reconcile master-data counts, stock, AR, AP, accounting balances, permissions, workflows, reports, and integrations.
- [ ] Run deployment smoke tests and the approved production UAT subset; obtain business and technical go/no-go approval.
- [ ] Execute cutover, communication, rollback checkpoints, and support escalation according to the runbook.
- [ ] Monitor the stabilization window and close deployment incidents with evidence.
- [ ] Hand over operating procedures, credentials ownership, backup/restore responsibility, monitoring, known issues, and support ownership.

Phase 1 must not add planned features, new schema, new custom business rules, new reports, or new integration contracts. A purely environmental or configuration deployment correction may be handled in Phase 1 only when it does not change the frozen product behaviour and is recorded. Any product/code/migration change returns the work to Phase 0, creates a new release candidate, and repeats affected P0.12 checks before redeployment.

Do not treat the disposable Phase 0 Compose topology as approved production architecture or as P0.12 production-like evidence.

## Deferred work after the first deployment

Unapproved customization, optional integrations, Business API expansion, MCP, Agent pilots, and multi-Agent orchestration are outside the first-release plan. They require an explicit new scope decision and a new development/validation cycle; they must not be inserted into Phase 1 deployment work.

## Completed P0.5 Acceptance Criteria

The criteria below are retained as completed historical evidence for P0.5. Current P0.7 acceptance and closeout requirements are defined under `P0.7.8` above.

### Repository state

- Codex inspected current Git/GitHub state before changing files.
- Unrelated user changes were preserved.
- Actual implementation was inspected before trusting documentation.
- No unrelated roadmap-phase implementation was added.

### Runtime

- `docker compose -f phase0/compose.yaml config --quiet` succeeds directly or as part of the existing health check.
- `create-site` remains successfully completed.
- required Phase 0 services are running.
- ERPNext reports 16.x.
- Frappe reports 16.x.
- ping returns `pong`.
- `./scripts/phase0-check.sh` exits `0`.
- the current execution date and outcome are recorded.
- any failure remains visible.

### Dataset

- existing synthetic company is used or explicitly revalidated.
- required customers exist.
- required selling prices exist.
- required warehouse exists.
- alternate-UOM test item exists.
- existing purchase/stock evidence is not destroyed.
- real/private business data is not introduced.

### Sales scenario definition

- reproducible source-controlled sales scenarios exist.
- scenarios cover full sale, partial delivery/payment, alternate UOM, and customer return.
- expected quantities and monetary values are defined before validation.
- scenarios are synthetic.
- scenario design avoids accidental duplication with previous stock-test Delivery Notes.

### Sales flow

Actual execution evidence exists for every case marked complete among:

- `SAL-001`
- `SAL-002`
- `SAL-003`
- `SAL-004`
- `SAL-005`
- `SAL-006`
- `SAL-007`
- `SAL-008`
- `SAL-009`
- `SAL-010`

Evidence must include appropriate combinations of:

- submitted/native document status
- customer
- source-document links
- quantities
- UOM
- conversion factor / stock quantity
- delivery percentages/status
- invoice totals
- outstanding amounts
- stock balances
- Payment Entry allocations
- GL rows

### Accounts Receivable

For cases marked complete:

- Sales Invoice creates a traceable customer receivable.
- full payment reduces the tested invoice outstanding balance to zero.
- partial payment leaves exactly the expected outstanding amount.
- Payment Entry references the correct invoice.
- receivable/payment GL effects are checked rather than inferred solely from UI/document status.

### Customer return

For cases marked complete:

- the return references the original sale/delivery/invoice as appropriate.
- returned quantity is verified.
- stock effect is verified.
- accounting effect is verified where applicable.
- resulting source/return relationship is traceable.
- any limitation in native ERPNext return handling is documented rather than hidden.

### Alternate UOM

For the alternate-UOM case:

- sales document UOM is verified.
- conversion factor is verified.
- stock quantity is verified in Piece.
- resulting stock balance matches the converted quantity.

### Idempotency

- the complete sales validator succeeds once.
- the complete sales validator is run again.
- the second run does not create duplicate transactional effects.
- matching existing documents are validated before reuse.
- final balances after rerun equal the expected balances.

### Validation evidence

`docs/PHASE0_VALIDATION.md`:

- records actual execution results
- retains the four allowed result states
- preserves failed attempts
- contains relevant document IDs
- contains actual expected-vs-observed evidence
- does not mark unexecuted cases as complete

### Handoff closeout

Before Codex hands the task back:

- changed JSON files parse successfully
- changed Python scripts compile successfully
- runtime health validation was executed
- sales validator was executed
- idempotent rerun was executed
- `git diff` was reviewed
- `git status` was reviewed
- this `docs/AI_HANDOFF.md` was updated in the same implementation change
- completed and incomplete work are clearly separated
- blockers remain visible
- recommended next action is evidence-based
- no Phase 1, Custom App, API, MCP, Agent, or multi-Agent implementation was started opportunistically

## Existing Execution Records to Preserve

### Synthetic Dataset / Runtime

Previously recorded commands include:

    git pull --ff-only origin main
    docker info
    docker compose -f phase0/compose.yaml up -d
    docker compose -f phase0/compose.yaml ps -a
    ./scripts/phase0-check.sh
    python3 -m json.tool phase0/synthetic-data.json
    python3 -m py_compile scripts/phase0-seed.py
    python3 scripts/phase0-seed.py

Previously recorded results:

- runtime health passed
- JSON parse passed
- Python compilation passed
- final seed exited `0`
- company count `1`
- warehouses `2`
- suppliers `3`
- customers `3`
- items `20`
- Item Prices `40`
- Opening Stock `MAT-RECO-2026-00001`
- 18 non-zero opening-stock rows
- `P0-CO-SCREW` UOM conversions Piece `1`, Box `50`, Carton `500`

Preserved historical seed/runtime failures:

- initial unprivileged Docker access was denied
- Docker Desktop was found stopped and subsequently started
- first opening-stock seed attempt failed because Stock Reconciliation `remarks` cannot be used in the attempted list filter
- second attempt failed because Opening Stock requires an Asset/Liability difference account
- submitted Stock Reconciliation did not retain the expected `remarks`
- final idempotency logic was changed to compare company, purpose, submitted status, and complete item/warehouse/quantity content

Do not remove these records merely because the corrected path now passes.

### Purchase Flow — 2026-09-05

Previously recorded commands include:

    git fetch --prune origin
    ./scripts/phase0-check.sh
    python3 scripts/phase0-seed.py
    python3 scripts/phase0-validate-purchase.py

Recorded evidence:

- Purchase Orders:
  - `PUR-ORD-2026-00001`
  - `PUR-ORD-2026-00002`
  - `PUR-ORD-2026-00003`
- Purchase Receipts:
  - `MAT-PRE-2026-00001` through `MAT-PRE-2026-00004`
- Purchase Return:
  - `MAT-PRE-2026-00005`
- Purchase Invoices:
  - `ACC-PINV-2026-00001`
  - `ACC-PINV-2026-00002`
- Payment Entries:
  - `ACC-PAY-2026-00001`
  - `ACC-PAY-2026-00002`
- invoice totals:
  - CNY 152
  - CNY 120
- outstanding after payment:
  - CNY 0
  - CNY 60
- final tested main-warehouse quantities:
  - hammer 28
  - screwdriver 58
  - screw 650 Piece

Preserved failure:

The first purchase-return attempt used:

`erpnext.controllers.sales_and_purchase_return.make_return_doc`

and received HTTP 403 because that lower-level path was not whitelisted.

The validated implementation uses the whitelisted native wrapper:

`erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_return`

Do not remove the failed attempt from project evidence.

### Stock Flow — 2026-09-05

Previously recorded commands:

    ./scripts/phase0-check.sh
    python3 scripts/phase0-validate-stock.py
    python3 scripts/phase0-validate-stock.py

Recorded evidence:

- `MAT-RECO-2026-00001` — Opening Stock
- `MAT-DN-2026-00001` — stock-reduction Delivery Note
- `MAT-STE-2026-00001` — Material Transfer
- `MAT-RECO-2026-00002` — Stock Reconciliation
- `MAT-DN-2026-00002` — zero-stock Delivery Note draft rejected at submission
- 18 matching Opening Stock ledger balances
- 18 non-zero main-warehouse items
- 3 `P0-AC-GOGGLES` in secondary warehouse
- second complete validator run reused existing documents and reproduced expected balances

Preserved failure:

The first Opening Stock ledger assertion incorrectly treated Stock Reconciliation `actual_qty` as the final opening quantity.

Observed ERPNext v16 behaviour showed:

- `actual_qty = 0` on the tested opening Stock Ledger Entry rows
- resulting opening balance in `qty_after_transaction`

The validator was corrected to verify:

- `qty_after_transaction`
- warehouse
- valuation rate

Preserve this behaviour as observed native evidence.

### Sales, Customer Return, and Accounts Receivable — 2026-09-06

Commands actually run included:

    git fetch --prune origin
    git pull --ff-only origin main
    docker info
    docker compose -f phase0/compose.yaml up -d
    ./scripts/phase0-check.sh
    python3 scripts/phase0-seed.py
    python3 -m json.tool phase0/sales-validation.json
    env PYTHONPYCACHEPREFIX=/tmp/erpnext-phase0-pyc python3 -m py_compile scripts/phase0-validate-sales.py
    python3 scripts/phase0-validate-sales.py
    python3 scripts/phase0-validate-sales.py
    python3 scripts/phase0-validate-sales.py

Actual runtime and master-data results:

- Docker Desktop was running with all nine Phase 0 long-running services.
- `./scripts/phase0-check.sh` exited `0` with ERPNext 16.33.0, Frappe 16.31.0, and a healthy ping response.
- The seed exited `0`; every required company, customer, item, warehouse, price, UOM, and Opening Stock document was reported as existing.
- The existing CNY 60 supplier payable and all purchase/stock evidence were preserved.

Actual sales and accounting evidence:

- Quotation: `SAL-QTN-2026-00001`.
- Sales Orders: `SAL-ORD-2026-00001` through `SAL-ORD-2026-00003`.
- Outbound Delivery Notes: `MAT-DN-2026-00003` through `MAT-DN-2026-00006`.
- Customer return: `MAT-DN-2026-00007`, linked to `MAT-DN-2026-00006`, quantity -1 Box / -50 Piece.
- Sales Invoices: `ACC-SINV-2026-00001` CNY 84, `ACC-SINV-2026-00002` CNY 125, and `ACC-SINV-2026-00003` CNY 32.5.
- Credit note: `ACC-SINV-2026-00004`, linked to `ACC-SINV-2026-00003`, grand total and outstanding both -CNY 32.5.
- Customer payments: `ACC-PAY-2026-00003` fully allocated CNY 84 and `ACC-PAY-2026-00004` partially allocated CNY 50.
- Final tested invoice outstanding amounts: CNY 0 and CNY 75 for the full and partial scenarios.
- Party receivable GL debits: CNY 84, CNY 125, and CNY 32.5.
- Party receivable GL credits from payments: CNY 84 and CNY 50.
- Party receivable GL credit from the credit note: CNY 32.5.
- Final main-warehouse stock: pliers 16, measuring tape 25, screws 650 Piece.
- `AR-004` remains `Not Tested`; the CNY 75 receivable is intentionally preserved for reporting validation.

Idempotency and failure evidence:

- The first transaction-producing execution created all required documents, then failed the validator's final assertion because it expected the fully returned Sales Order to retain `per_delivered = 100`.
- ERPNext v16 instead reports the returned order's net state as `per_delivered = 0`, `status = To Deliver`; the assertion was corrected to distinguish historical delivery evidence from the post-return net order state.
- Two complete executions after the correction exited `0`, reported all transaction documents as `EXISTS`, and returned identical stock, invoice, payment, return, and GL evidence without duplicate effects.

Changed files:

- `README.md`
- `phase0/sales-validation.json`
- `scripts/phase0-validate-sales.py`
- `docs/PHASE0_VALIDATION.md`
- `docs/AI_HANDOFF.md`

Historical recommendation at the 2026-09-06 handoff: review the completed P0.5 evidence before authorizing P0.6. This recommendation was satisfied by the 2026-10-03 closeout revalidation and acceptance below.

### P0.5 Closeout Revalidation — 2026-10-03

Commands actually run included:

    docker info --format '{{.ServerVersion}}'
    docker compose -f phase0/compose.yaml up -d
    docker compose -f phase0/compose.yaml ps -a
    docker compose -f phase0/compose.yaml restart frontend
    ./scripts/phase0-check.sh
    python3 -m json.tool phase0/synthetic-data.json
    python3 -m json.tool phase0/sales-validation.json
    env PYTHONPYCACHEPREFIX=/tmp/erpnext-p05-pyc python3 -m py_compile scripts/phase0_api.py scripts/phase0-seed.py scripts/phase0-validate-purchase.py scripts/phase0-validate-stock.py scripts/phase0-validate-sales.py
    python3 scripts/phase0-seed.py
    python3 scripts/phase0-validate-sales.py
    python3 scripts/phase0-validate-sales.py

Actual results:

- Docker Engine `29.5.2` was started; all nine required long-running Phase 0 services were running and `create-site` remained exited `0`.
- The first two health-check attempts returned HTTP 502. Logs showed the already-running frontend still referenced the backend's previous container address. Restarting only `frontend` restored the upstream connection; the next complete health check exited `0` with ERPNext `16.33.0`, Frappe `16.31.0`, and a healthy ping.
- Compose configuration, both relevant JSON files, and all five Python scripts passed static validation.
- The seed exited `0`, reported all synthetic entities and `MAT-RECO-2026-00001` as existing, and summarized company `1`, warehouses `2`, suppliers `3`, customers `3`, and items `20`.
- Two consecutive sales-validator executions exited `0`. Both reported the existing Quotation, three Sales Orders, four outbound Delivery Notes, three Sales Invoices, two customer payments, customer return, and credit note without creating duplicates.
- Both runs reproduced final stock of pliers `16`, measuring tape `25`, and screws `650`; invoice outstanding balances `0`, `75`, and `32.5`; payment receivable credits `84` and `50`; and credit-note receivable credit `32.5`.
- P0.5 was accepted and authorized progression to P0.6.

### Language, Permissions, Approval, and Audit — 2026-10-03

Implemented through:

- `phase0/access-validation.json`
- `scripts/phase0-validate-access.py`
- the shared `scripts/phase0_api.py` REST client

Actual results:

- Native System Settings persisted `language = zh`.
- Five synthetic System Users were created for purchase, sales, stock, finance, and approval roles. Authenticated Desk boot pages resolved `zh` for four Chinese users and `en` for the sales user's explicit English override.
- Positive and negative REST checks passed: purchase could access Purchase Order but not Payment Entry/Stock Entry; sales could access Sales Order but not Purchase Order/Payment Entry/Stock Entry; stock could access Stock Entry but not Payment Entry; finance could access Payment Entry/Purchase Invoice/Sales Invoice but not Stock Entry.
- `P0 Purchase Order Approval`, `P0 Sales Order Approval`, and `P0 Payment Entry Approval` were configured as active native Workflows.
- Business creators could create Pending documents but could not execute the manager-only Approve transition. The synthetic approval manager submitted and then cancelled the validation documents through Workflow transitions.
- Final evidence included cancelled Purchase Orders `PUR-ORD-2026-00004` and `PUR-ORD-2026-00005`, cancelled Sales Order `SAL-ORD-2026-00004`, and cancelled CNY 1 Payment Entry `ACC-PAY-2026-00005`.
- Each selected approval fixture had two Version records; `owner` remained the business creator and `modified_by` identified the approval manager.
- A complete rerun reused the five users, three Workflows, and cancelled validation documents without new transaction effects.
- P0.5 sales/AR regression passed afterward with stock `16`, `25`, and `650`, and outstanding balances `0`, `75`, and `32.5` unchanged.

Preserved failures and corrections:

- filtering Purchase Order by `supplier_order_info` was rejected as a non-permitted REST list filter; the validator now queries by allowed party fields and inspects candidate documents
- the first manager-only approver lacked base Item/document access; the synthetic approval identity now combines the relevant User and Manager roles
- the failed approval left `PUR-ORD-2026-00004` Pending; the corrected run recovered, approved, and cancelled it instead of deleting it
- direct API invocation of non-whitelisted `frappe.boot.get_bootinfo` was rejected; resolved language is verified from the authenticated Desk `/app` HTML

Historical P0.6 recommendation: continue to P0.7 reporting and output validation. Those checks are now implemented; see the 2026-10-06 P0.7 closeout above.

## Notes for Next Agent

Before making any change:

1. Read `AGENTS.md`.
2. Read `README.md`.
3. Read this `docs/AI_HANDOFF.md`.
4. Read `docs/ROADMAP.md`.
5. Read `docs/DECISIONS.md`.
6. Read `docs/PHASE0_VALIDATION.md`.
7. Inspect the actual repository.
8. Inspect current Git status.
9. Inspect existing Phase 0 scripts and JSON scenario files.
10. Revalidate the runtime.

Important constraints:

- Actual code, configuration, tests, Git state, and observed runtime behaviour outrank this document.
- The Web GPT review has accepted purchase/stock evidence for progression; it has not independently rerun the user's Docker environment.
- P0.5 sales, return, and transaction-level AR evidence was revalidated and accepted on 2026-10-03.
- P0.6 language, permissions, roles, approval, and audit validation completed on 2026-10-03. Use native ERPNext language settings; do not add a custom language switcher without evidence that native behaviour is insufficient.
- Current task is P0.10 / C0; P0.9 closeout and R1-scope-v1.1 supersede historical tasks.
- Do not renumber or silently replace the existing Phase 0 validation cases.
- Do not mark a test complete without actual execution evidence.
- Use synthetic/sanitized data only.
- Preserve existing purchase/stock evidence.
- Preserve the CNY 60 open payable for later AP/reporting validation.
- Prefer deterministic, source-controlled scenarios.
- Keep validation scripts idempotent.
- Use ERPNext REST/native whitelisted methods rather than direct DB access.
- Preserve ERPNext Core.
- Do not add customization to force a native validation case to pass.
- Record native limitations as `Configurable`, `Gap`, or `Not Tested` according to evidence.
- P0.7/P0.8 and N1 technical baseline are closed for progression; execute N2 first. Phase 1 remains blocked until P0.12 deployment-readiness acceptance.
- Do not begin `hardware_erp` or deployment-required integration development during P0.7. They may begin only if P0.8 approves them and orders them into P0.10/P0.11.
- Do not begin Phase 1 until P0.7 through P0.12 are complete and deployment readiness is explicitly approved.
- Keep MCP, Agent, and multi-Agent work deferred unless the project owner explicitly adds it to a future Phase 0 release scope.
- Treat `ERP与AI智能体设计笔记.md` as direction, not implementation proof.
- Update this handoff in the same change as the implementation/evidence it describes.
- The owner-approved Phase 0 development / Phase 1 deployment boundary is recorded in `docs/ROADMAP.md` and `docs/DECISIONS.md`; keep them aligned if P0.8 changes milestones or introduces another durable decision.
- Do not modify Obsidian during this routine Phase 0 task.
