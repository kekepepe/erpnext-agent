# ERPNext-agent Roadmap

## Roadmap Rules

This file describes phase goals and exit criteria, not daily task status. Daily priorities belong in `AI_HANDOFF.md`. A phase advances only when its exit criteria are supported by repository or validation evidence.

## Phase 0 — Development and Deployable Release Preparation (Current)

2026-11-23：交付路线由所有者确定（DEC-015）——为一家指定的五金工具公司按其需求自建，后期部署到 Web 域名供其使用。项目性质因此从一次性技术验证转为面向真实客户的定制系统，Phase 1 的门槛内容随之扩大：公网域名与 TLS、真实并发账号与岗位 UAT、生产备份与故障处置、终端用户手册与培训、客户数据导出与退出条款、ERPNext 升级与维护责任策略，全部成为需交付的工作项而非环境准备。同时新增两项 Phase 0 工作内容：前端形态按国内进销存习惯重做（DEC-016，含核心单据自定义高密度录入表单），以及财务口径待客户财务部确认后实施（DEC-017）。服务器选型仍未确定，不阻塞 Phase 0，但阻塞 Phase 1 启动。方向整理见 `docs/OWNER_DIRECTION_20261123.md`。

2026-11-13：W3/W5 技术回归、M1 两轮基础与扩展合成期初、A1 合成异站恢复与双构建切回均取得实测记录。正式开账、岗位 UAT、类生产容量及 RC 准入仍为 Phase 1 前置条件，见 WORKBENCH_RELEASE_PLAN。

2026-11-06：P0.10/C0 固定版本合成生命周期技术验证完成（11月4日执行，见 C0_ACCEPTANCE）。中文工作台仍在 W3–W5 语义与操作验收；M1 已启动但全量迁移、A1全站恢复/UAT/RC仍阻断发布。后续展示改动须运行受影响回归，不能沿用 C0 快照推定已通过。

2026-10-28: owner authorized W0–W6 full native workbench implementation beyond U2 (DEC-013, WORKBENCH_IMPLEMENTATION_PLAN.md). Frontend shell and permission-aware read-only backend extend the existing presentation app; native transactions remain unchanged. C0/M1/A1 still block release.

Planning addition (2026-10-27): the owner requested a plan for a fixed left-category/right-content workbench and Chinese ERP business terminology based on 管家婆/金蝶 usage. See `UI_CHINESE_WORKBENCH_PLAN.md` and `PRE_PHASE1_PLAN.md`. Research, glossary and prototype precede UI implementation; affected lifecycle checks and final UAT must precede Phase 1. This records planned work, not completed UI delivery or a replacement for the open C0/M1/A1 gates. Register the presentation scope amendment before implementation.

**Goal:** complete, validate, and package the full approved first ERP release before deployment begins.

Language scope directive (2026-10-06): the owner now requires Simplified Chinese system display names and active-user language. Technical identifiers and externally entered identity/content remain unchanged. This approves the bounded presentation package only; it does not accept P0.7 progression or freeze all P0.8 release requirements. See DEC-009.

First-release scope frozen 2026-10-09 under owner-delegated authority: R1-scope-v1.1 in `docs/FIRST_RELEASE_SCOPE.md`. One company, two warehouses, CNY, Chinese UI and ten business PDFs, core trading and seven native reports. Existing bounded Chinese presentation app/patches remain included; The owner-approved hardware_erp approval guard is an N2 dependency (DEC-012). The November 22 scope adds trade-line reconciliation and customer price tiers (DEC-014). External integrations, independent Business API/MCP/Agent, and other business customization remain deferred. P0.7 discovery and P0.8 scope gates are closed; P0.9 native configuration/SOP and bounded guard technical implementation closed 2026-10-12; P0.10 fixed-version synthetic lifecycle verification is complete as recorded above; P0.11 migration and P0.12 real UAT/recovery/RC gates remain open. See DEC-011.

Scope:

- Disposable local ERPNext validation environment
- Representative, non-sensitive master data
- Purchase, receipt, stock, delivery, sales, returns, and receivable/payable flows
- Permission, approval, auditability, and reporting checks relevant to the workflow
- Evidence-based Gap Analysis
- First-release scope freeze and requirement-to-evidence mapping
- Required native ERPNext configuration and operating procedures
- Only approved `hardware_erp` customization gaps
- Deployment-required integrations and migration tooling
- Full regression, UAT, backup/restore, rollback, and deployment rehearsal
- Versioned, documented, deployable release candidate

Exit criteria:

- Baseline environment health check passes reproducibly.
- Representative master data and test assumptions are documented.
- Critical end-to-end workflows have recorded expected and actual results.
- Each gap is classified as configuration, process change, integration, customization, or unresolved.
- The first-release scope and every release-blocking acceptance criterion are approved.
- All approved functionality, configuration, customization, integration, and migration code is complete and tested.
- A clean production-like environment can be built reproducibly from source and the release manifest.
- Migration, backup/restore, deployment, smoke-test, rollback, and disaster-recovery procedures have been rehearsed.
- Business UAT and deployment-readiness review approve an immutable release candidate for Phase 1.

## Phase 1 — Deployment and Rollout

**Goal:** deploy, cut over, and stabilize the accepted Phase 0 release candidate without adding planned product development.

Scope:

- Provision and verify staging/production infrastructure and environment separation
- Configure domains/TLS, secret management, logging, monitoring, access ownership, and scheduled backups
- Install the exact accepted ERPNext/Frappe and custom-app release versions
- Apply approved configuration and execute rehearsed data migration/import
- Reconcile critical master, stock, AR, AP, accounting, permission, workflow, report, and integration results
- Execute smoke tests, production UAT subset, go/no-go, cutover, rollback checkpoints, and stabilization support
- Transfer operating, backup/restore, monitoring, and support ownership

Exit criteria:

- The accepted release candidate is deployed without unreviewed code or product-scope changes.
- Migration and financial/stock reconciliation are signed off.
- Production smoke tests and agreed UAT checks pass.
- Monitoring, backup, restore, access, operating, and support ownership are active.
- Stabilization incidents are resolved or explicitly accepted with owners and dates.

Any deployment finding that requires business-logic, schema, custom-app, report, integration-contract, or migration-code changes returns to Phase 0 for a new release candidate and affected revalidation. Phase 1 is not a development-completion phase.

## Phase 2 — Post-deployment Product Evolution (Deferred)

**Goal:** hold future release ideas without inserting them into the first deployment.

Potential scope, only after explicit owner approval:

- Enhancements explicitly deferred from the first release
- New business requirements discovered after stabilization
- Optional integrations or expansion of `hardware_erp`
- A new development, validation, release-candidate, and deployment cycle

Exit criteria:

- Scope is separately approved and prioritized.
- Work does not bypass the development and release gates established in Phase 0.
- ERPNext business Core remains unmodified; DEC-010 permits only the owner's bounded, versioned Chinese presentation patches, not business-logic changes.

## Phase 3 — Business API and MCP Foundation

**Goal:** expose reviewed, permission-aware business operations for AI-assisted use without direct database access.

This is deferred beyond the first Phase 1 deployment unless explicitly brought into a future approved release cycle.

Planned scope:

- Stable service/API boundaries for selected ERP workflows
- Authentication, authorization, idempotency, audit logging, and error contracts
- MCP tools wrapping approved business APIs
- Human approval gates for consequential actions

Exit criteria:

- API and MCP threat boundaries are reviewed.
- Tool permissions follow least privilege.
- Read and write actions are auditable and tested.
- High-impact writes require explicit human approval.

## Phase 4 — Narrow Agent Pilots

**Goal:** prove value with one or two bounded, measurable Agent use cases before considering multi-Agent orchestration.

This is deferred beyond the first Phase 1 deployment and depends on approved, proven Business API/MCP boundaries.

Candidate pilots:

- Enterprise data question answering through approved read APIs
- Inventory risk monitoring and draft purchase recommendations

Exit criteria:

- Each pilot has a human owner, success metrics, failure handling, and an off switch.
- Agent actions are observable, permission-scoped, and auditable.
- Business benefit and operational risk are reviewed before expansion.

## Deferred Direction

Broader CRM/OA coverage, multi-Agent orchestration, predictive workflows, and additional channels remain long-term possibilities. They are not current commitments and must not pre-empt Phase 0 evidence or the approved MVP.
