# Project Decisions

## DEC-014 — 商品核对字段及客户报价档位（2026-11-22）

用户要求按旧系统的业务词条补齐商品与交易明细，并由客户档位推荐价格。验证中的 ERPNext v16 已有品牌、计量单位及换算、订单折扣、逐行税额、价目表、商品价格和客户默认价目表。原生商品缺少独立简称、规格、型号、英文商品名称及要求，且新建商品不能一次保存多档价格。交易行增加业务资料快照与逐行金额显示。首次保存商品和原生商品价格使用同一请求事务及原生新增权限，客户选择一个默认档位，档位数量通过原生价目表扩展。

界面固定词条使用简体中文，商品与交易行保留英文商品名称和英文要求字段。核对视图中的含税行金额依据 ERPNext 逐行计入总额的税费，折算税费率允许包含原生应计费用，原生税费模板、审批、库存估值和总账规则仍由各自控制器管理。参考成本价与最低售价是商品资料。真实价格和财务口径属于岗位验收输入。

## DEC-013 — Native Chinese workbench integration (2026-10-28)

Owner requested full first-release frontend/backend completion after the U2 prototype. The confirmed presentation gap is persistent business-category navigation and consistent Chinese task entry points across native modules. Implement a separately switchable workbench module within erpnext_zh, with permission-aware read-only server data and native list/form/report routing. Reuse native write APIs and hardware_erp guard; do not create a parallel business backend, new business schema, iframe shell or additional Core patch. Current scope is the approved trading modules only. W0–W6 in WORKBENCH_IMPLEMENTATION_PLAN.md define implementation and regression, not production acceptance; U1 finance/semantic review and C0/M1/A1 remain required.

This file records durable decisions, not routine implementation notes. New entries should include the decision, rationale, consequences, and evidence that would justify revisiting it.

## DEC-001 — Repository implementation is the highest source of truth

- **Status:** Accepted
- **Date:** 2026-09-01
- **Decision:** Resolve project-state conflicts in this order: code/tests/configuration and observed behaviour; current Git/GitHub state; `AI_HANDOFF.md`; roadmap and decisions; Obsidian; historical conversations.
- **Rationale:** AI-authored status can drift. Requiring implementation evidence prevents a document from declaring unfinished work complete.
- **Consequence:** Any agent that finds a conflict must trust the code or runtime evidence and correct the documentation.

## DEC-002 — Use GitHub handoff documents as the daily AI coordination channel

- **Status:** Accepted
- **Date:** 2026-09-01
- **Decision:** Web GPT plans and reviews through `docs/AI_HANDOFF.md`; Codex executes the highest-priority P0 task, validates it, and updates the same handoff alongside code.
- **Rationale:** Versioning execution state with the implementation gives both AI endpoints a shared, auditable context.
- **Consequence:** `AI_HANDOFF.md` contains current status and next actions. `ROADMAP.md` contains milestones. This file contains only durable decisions.

## DEC-003 — Use Obsidian for milestone knowledge, not commit-by-commit state

- **Status:** Accepted
- **Date:** 2026-09-01
- **Decision:** Distil project knowledge to Obsidian after an accepted phase or explicit milestone rather than after every commit.
- **Rationale:** GitHub is better suited to volatile execution state; Obsidian should retain durable context, architecture, decisions, lessons, and resolved problems.
- **Consequence:** The existing Obsidian MCP remains available, but routine development must not depend on synchronizing every change to it.

## DEC-004 — Validate ERPNext native capability before customization

- **Status:** Accepted
- **Date:** 2026-09-01
- **Decision:** Complete Phase 0 native-workflow validation and Gap Analysis before defining the `hardware_erp` Custom App scope. Do not modify ERPNext core.
- **Rationale:** Native configuration or a process adjustment may satisfy requirements more safely and cheaply than customization.
- **Consequence:** A proposed custom field, DocType, validation, or report must trace to a confirmed gap and include upgrade and testing implications.

## DEC-005 — Keep Phase 0 disposable and separate from production design

- **Status:** Accepted
- **Date:** 2026-09-01
- **Decision:** The current Docker Compose stack is only a local, disposable ERPNext v16 validation environment.
- **Rationale:** It is based on a quick-demo topology and includes local-only credentials and assumptions.
- **Consequence:** Passing Phase 0 does not approve this Compose file, credentials, persistence model, or topology for staging or production.

## DEC-006 — Future Agents use governed business APIs, never direct ERP database access

- **Status:** Accepted as an architectural constraint; implementation deferred
- **Date:** 2026-09-01
- **Decision:** Future Agents and MCP tools must call reviewed ERP service/API operations. Consequential writes require permission checks, audit logs, and explicit human approval.
- **Rationale:** Direct database access bypasses ERP business rules and makes authorization, validation, and traceability unreliable.
- **Consequence:** Agent, MCP, and multi-Agent implementation is out of scope until the ERP workflow and API boundaries are stable.

## DEC-007 — Keep the repository public for Web GPT → GitHub → Codex coordination

- **Status:** Accepted
- **Date:** 2026-09-01
- **Decision:** Keep `kekepepe/erpnext-agent` public during the current collaboration workflow so Web GPT can directly read GitHub project state and write task handoffs that Codex can consume from the same repository.
- **Rationale:** GitHub is now the shared operational bridge between Web GPT and Codex. This removes the need for Obsidian to carry volatile per-task execution state and allows task plans, implementation evidence, and handoffs to remain version-controlled alongside the project.
- **Consequence:** The public repository must contain only code, synthetic test data, sanitized examples, non-sensitive architecture notes, validation evidence, and project coordination documents. Production secrets, reusable credentials, real customer/supplier records, confidential pricing, contracts, personal information, production exports, and other non-public business data must never be committed.
- **Revisit when:** Both Web GPT and Codex can reliably access an appropriately permissioned private repository, or the project reaches a stage where required implementation information cannot be safely represented with synthetic/sanitized artifacts.

## DEC-008 — Complete first-release development in Phase 0 and reserve Phase 1 for deployment

- **Status:** Accepted
- **Date:** 2026-10-03
- **Decision:** Phase 0 now includes all functionality, native configuration, approved customization, deployment-required integration, migration tooling, testing, UAT, recovery rehearsal, and release-candidate preparation required for the first deployable ERP release. Phase 1 begins only after deployment-readiness approval and is limited to environment provisioning, applying the accepted release, approved data migration, cutover, operational handover, and stabilization.
- **Rationale:** Entering deployment with planned development unfinished mixes product change with rollout risk, weakens acceptance evidence, and makes migration and rollback results unreliable.
- **Consequence:** Passing native-capability validation or Gap Analysis does not end Phase 0. The project must freeze scope, complete approved implementation, build and validate a reproducible release candidate, and obtain explicit deployment-readiness approval. A Phase 1 finding that requires business-logic, schema, custom-app, report, integration-contract, or migration-code changes returns to Phase 0 and triggers a new candidate plus affected revalidation. Optional MCP, Agent, and multi-Agent work remains outside the first release unless explicitly approved into a future development cycle.
- **Revisit when:** The first deployment has stabilized and the owner explicitly approves a new release lifecycle or changes the project phase model.

## DEC-009 — Chinese presentation without renaming business identifiers

- **Status:** Accepted for the owner's 2026-10-06 language request only.
- **Decision:** All active test users and site language use Simplified Chinese. Translate system display names, fixed UI chrome and controlled print formats; preserve API/schema identifiers, document/item codes, addresses, email and personal input.
- **Rationale:** Official dictionaries plus native configuration cover metadata, but the installed v16 application-title and autocomplete code bypasses gettext. A narrowly scoped presentation app closes those demonstrated gaps without patching Core.
- **Consequences:** A versioned custom image and Chinese Compose overlay are now required. Historical English override/standard-print tests remain compatibility evidence, not the active UI policy. This does not approve P0.8 scope or production deployment.
- **Revisit when:** ERPNext upgrades or owner-approved release language requirements change. Re-run source inventory, actual-session coverage, print and permission/business regressions.

## DEC-010 — Owner-authorized presentation-only source patches

- **Status:** Accepted for the owner's explicit 2026-10-06 patch request; limited exception to DEC-004/DEC-009 and the Core-preservation rule.
- **Decision:** Keep upstream ERPNext/Frappe fixed and unchanged as a baseline; a derived Phase 0 image may apply reviewed source patches exclusively to proven UI translation omissions. Do not edit live containers, remove standard-template protection, change internal names, write transactions, alter permissions, or modify business/accounting validation.
- **Evidence:** Rendered native workflow help exposes its English composite title, state, role and action despite a Chinese session/dictionary. Select-state version history and icon-only tag accessible names also bypass translation. Dictionary-only fixes cannot intercept those call sites.
- **Controls:** Versioned exact replacements, before/after SHA-256 per file, no fuzzy application, whole-batch prevalidation, rebuilt frontend assets, original immutable source inventory, explicit patched-file audit, offline drift/reversal tests, rendered checks and full affected business/access regression. Upgrades must fail closed until the patch set is reviewed.
- **Recovery:** Build with `APPLY_ZH_SOURCE_PATCHES=0` to retain the same Chinese app/configuration while restoring upstream source; this is a source rollback, not deletion/uninstallation or a promised database rollback. Verify the recovery image separately before using it.
- **Consequence:** The previous claim that all Core hashes are unchanged is historical only once a patched image is activated. Record the exact approved changed files and leave broad language coverage open until verified. P0.8 scope approval and Phase 1 readiness are not inferred.
- **Revisit when:** Native fixes land, hooks cover the demonstrated gaps, dependency versions change, or a patch touches anything beyond presentation.

## DEC-011 — Freeze R1 core-trading scope under delegated owner authority

- **Status:** Accepted scope design; implementation and deployment acceptance pending.
- **Date:** 2026-10-09
- **Authority:** Owner explicitly requested P0.7→P0.8 progression, confirmed the proposed functional boundary, and delegated organization/approval/accounting/migration parameters to Codex.
- **Decision:** `docs/FIRST_RELEASE_SCOPE.md` R1-scope-v1 fixes one company/two warehouses/CNY/Chinese UI and business PDFs/core trading/seven native reports. Use native configuration/SOP first, retain the approved `erpnext_zh` presentation extension, and do not create `hardware_erp` business customization or external integrations/independent Business API/MCP/Agent. Migrate master data, opening inventory, unresolved AR/AP and reconciled opening GL; keep completed historical transactions in a controlled read-only archive.
- **Consequences:** Scope authority is not evidence of real-company configuration, tax rates, production UAT or deployability. Finance-owned native tax/account mapping and actual data are controlled implementation inputs. PDF, realtime, full scoped-language/mobile UAT, migration and complete recovery remain release-blocking Must acceptance conditions. Standard-template protections and user-authored business content stay intact. P0.9–P0.12 implement in the frozen package order before Phase 1.
- **Revisit when:** A tested Must cannot be satisfied natively, organization/currency/required integration scope changes, or UAT identifies a necessary release requirement. Version the scope change and revalidate affected gates.

## Open Decisions (remaining)

The following are intentionally undecided pending evidence:

- Exact staging/production rollout environment — delivery shape is now Web-domain deployment for one named client (DEC-015), but no server has been selected yet
- Cost algorithm, gross-margin basis, discount allocation, freight treatment and rounding rules — pending the finance department's confirmation, not a developer decision (see DEC-017)
- Any additional proven Must gap beyond the approved bounded approval guard
- Production rollout of the internal W6 Business API adapter and its authorization, pending isolated-site and role acceptance (see DEC-023)
- First Agent pilot, model/provider, orchestration framework, and success metrics


## DEC-012 — Bounded server-side approval guard as an N2 dependency (2026-10-12)

Status: owner approved 2026-10-12; implemented and synthetically validated during N2. Scope version R1-scope-v1.1.

Two native Purchase Order probe runs reproduced direct over-limit submit, creator self-submit, and simultaneous price mutation+approval; native field-level input protection did not force approval transitions. See `docs/NATIVE_APPROVAL_GAP.md` and the sanitized JSON evidence. These executed Must gaps supersede the earlier no-business-customization conclusion only at the approval boundary.

Keep Workflow, roles, User Permissions, transactions and accounting native. Add an isolated `hardware_erp` application containing document-event validation of state/docstatus, current threshold inputs, maker/approver identity and business-input changes during approval. Do not patch Core, add external API/MCP/Agent or put business validation into `erpnext_zh`. The guard is a necessary N2 dependency, not permission to start unrelated roadmap phases. Ordinary business and ownership parameters remain synthetic until controlled real-data mapping/UAT.

Negative tests must exercise native REST/submit/cancel and normal Workflow routes; app removal/configuration drift must block deployment. The original P0 company remains an explicit disposable discovery fixture exception, not a production bypass namespace. A production preflight must reject P0 fixtures and verify all scoped companies/roles/workflows/app presence.

## DEC-015 — ERPNext self-build route for one named hardware-tool client, delivered on a Web domain (2026-11-23)

- **Status:** Accepted by the owner on 2026-11-23 as the delivery route. Deployment environment and tenant model remain open.
- **Authority:** Owner response to the 2026-11-23 gap review against 管家婆/金蝶.
- **Decision:** Keep ERPNext as the base and build a customized system to one named hardware-tool company's requirements. Do not license and re-customize a commercial ERP product. The end state is a Web deployment on a domain, accessed by that company's staff through a browser.
- **Rationale:** The client's requirements are specific enough that generic product behavior must be replaced rather than configured. Self-build keeps the data model, the Chinese presentation layer and the workflow behavior under the project's own control, and avoids recurring license and vendor-subscription cost for a single client.
- **Consequences:** The project changes character from a disposable Phase 0 technical validation to a production system for a real business. New requirements follow from this and were not in R1 scope: a public domain with TLS, real concurrent users and roles instead of five synthetic ones, production backup/restore and incident handling, end-user operating manuals and training material for clerks, warehouse and finance staff, a documented data export and exit path for the client, and an explicit ERPNext upgrade and maintenance responsibility. The pinned `v16.33.0` image is a validation anchor, not a long-term upgrade policy; it now needs a stated upgrade path.
- **Open consequence — tenant model:** Whether this delivery stays a single-tenant customization or must remain reusable for additional clients is unresolved and changes tenant isolation, permission, and pricing design. No speculative multi-tenant design may be introduced before this is answered.
- **Scope relation:** This does not change the frozen R1 functional scope in `docs/FIRST_RELEASE_SCOPE.md`. It does change the character of the Phase 1 gate: infrastructure selection, domain, real identity mapping and real role UAT become deliverable work items rather than environment preparation.
- **Revisit when:** The client confirms single-tenant versus reusable delivery, or a second client appears.
- **Reference:** `docs/OWNER_DIRECTION_20261123.md`.

## DEC-016 — Frontend form model and business terminology move to domestic trade-ERP conventions (2026-11-23)

- **Status:** Accepted as the product direction on 2026-11-23. The owner confirmed a staged pilot, starting with purchase receipt and delivery note, subject to confirmation of actual document frequency and operator workflows.
- **Authority:** Owner response to the 2026-11-23 gap review.
- **Decision:** The current native-Desk-shaped interface does not meet the client's need and must be reworked toward the operating conventions of domestic 管家婆/金蝶-style trade ERPs: dense table-as-form entry (one row per item), barcode scanning, batch item import, configurable visible fields, document-level business defaults, and the domestic operation model of "list is the workspace" instead of multi-step English-style wizards. Interface wording must be business terminology in Chinese, aligned with `docs/UI_CHINESE_TERMS.md`, not literal translation of English labels or Western interaction patterns.
- **Rationale:** The existing workbench is a Chinese navigation layer over native Desk forms. It does not change how a clerk actually enters a purchase receipt or a sales delivery, which is where the recorded gaps against the reference product are largest. Terminology and interaction are one work item: a dense form delivered with Western labels and Western interaction is not usable.
- **Consequences:** The owner's "bulk entry and document feel" request and the "Western-style interface" request are the same work item and must be planned together to avoid duplicate effort. The scope of `docs/UI_CHINESE_WORKBENCH_PLAN.md` must be rewritten against this decision; its current U3/U4 target of "native forms plus a Chinese navigation shell" does not satisfy it. The scan, batch entry and business-default work that `docs/ERP_TRADE_GAP_COMPLETION_PLAN.md` batch 1B left open belongs to this work item rather than to a separate batch. Custom entry forms must reuse native approval, permission and tax/amount calculation chains rather than reimplementing them, and each custom form must prove parity with the native document it replaces.
- **Cost to recognize:** Custom dense entry forms for the core documents are, on current evidence, the largest single item of work in the project and may exceed all prior batches combined. The depth choice must be made explicitly before work starts.
- **Revisit when:** The client confirms the actual document frequencies and the number of entry clerks, or pilot evidence supports expanding to additional documents.

## DEC-017 — Financial calculation bases are deferred to the client's finance department (2026-11-23)

- **Status:** Accepted as a sequencing decision on 2026-11-23. The finance department's confirmation is an external input, not a development decision.
- **Authority:** Owner response to the 2026-11-23 gap review.
- **Decision:** Cost algorithm, gross-margin basis, converted tax rate, whole-order discount allocation, freight-into-cost treatment, receivable/payable recognition timing and rounding rules are not settled by the project now. They are to be agreed with the client's finance department and implemented afterwards.
- **Rationale:** These are accounting-policy choices of the client, and the synthetic 5% rate and other synthetic assumptions in the current baseline cannot stand in for them. Settling them with the finance department first avoids building reports and entry forms on assumptions that would have to be redone.
- **Consequences:** The known difference between the reference system's full-month weighted average and ERPNext's moving average remains an open migration risk and must be resolved before any real opening balances are posted; deferral changes when it is resolved, not whether. The recorded cost and margin gaps in `docs/GUANJIAPO_ERP_GAP_ANALYSIS.md` stay open. Entry-form work under DEC-016 should build field placement and interaction order first and leave calculation rules to be filled once finance confirms, rather than hard-coding synthetic tax rates. Pricing priority (batch 1A) and document source linkage (batch 2A) do not depend on these bases and may continue.
- **Required input:** `docs/OWNER_DIRECTION_20261123.md` section 4.1 holds the confirmation checklist to take to the finance department.
- **Revisit when:** The finance department confirms the bases, or a real opening-balance migration is requested.

## DEC-018 — Single-tenant delivery for one client (2026-11-23)

- **Status:** Accepted by the owner on 2026-11-23.
- **Decision:** The system is built for one named hardware-tool client only. No multi-tenant isolation, tenant routing, per-tenant pricing model or SaaS commercialization features are introduced, and no speculative design for future multi-tenancy may be added without an explicit decision.
- **Rationale:** The owner confirmed the delivery is a customization for a single company rather than a product for a market. Multi-tenant design would consume engineering capacity that the client-facing work needs, and would dilute the operating-model rework required by DEC-016.
- **Consequences:** The engineering effort released from multi-tenancy goes into the entry-form and job-view work in DEC-016 and DEC-020. If a second client appears, the reuse question reopens as its own decision, and the isolation cost is then known and priced rather than prepaid.
- **Revisit when:** A second client appears, or the owner decides to commercialize the system.

## DEC-019 — English source-order matching, bilingual order preparation and ERP entry (2026-11-23)

- **Status:** Accepted as a requirement on 2026-11-23. The matching algorithm, source-format handling and the alias-library schema will be validated against real orders.
- **Authority:** Owner request of 2026-11-23.
- **Problem:** Staff have weak English. Each foreign purchase order currently requires manual translation, and the translation is often inaccurate, costing time and forcing staff to hunt for the correct standard Chinese name for a hardware item.
- **Decision:** Upload the English source order, match its item descriptions against the standard Chinese item master, and generate a new bilingual order after human confirmation. Staff then use that order to enter an ERP transaction as a draft. The transaction follows the same permissions, approval, submission and fulfillment rules as an ordinary order.
- **Architectural constraints:**
  - The standard Chinese item name is the reference. Matching is an alias lookup, not machine translation, and must not produce a name outside the item master.
  - The existing `custom_trade_name_en` item field is the starting alias store and must be promoted into a searchable alias set covering supplier-specific wording, former-system names and common spelling variants.
  - Matching returns ranked candidates with a confidence level and the reason for each hit; it never silently picks one. High-confidence hits may pre-fill a row awaiting review but remain visible and editable.
  - Model numbers and dimensions are matched by rule, not by fuzzy similarity, and are resolved before free-text matching.
  - An unmatched row is never dropped. It goes to a to-be-created list for new item creation.
  - Every human confirmation writes the English string back to the alias set with its source, so accuracy compounds with use.
- **Consequences:** The value of this feature depends on the write-back loop, not on the similarity algorithm. Without it, matching accuracy stays flat. Item master data becomes a maintained asset with English aliases, and the alias set must be migrated alongside real opening balances. This is a new client-facing capability and is not covered by the frozen R1 scope.
- **Blocker:** Confirm whether customers or suppliers send the originals and which ERP order type staff must enter. Obtain sanitized samples from 3–5 corresponding sources to validate parsing, matching and the alias schema. See `docs/OWNER_DIRECTION_20261123.md` section 7.
- **Revisit when:** Source-order samples are available, or the client reports that orders also arrive as scanned images, which would add OCR to the scope.

## DEC-020 — Job-view presets: one configuration drives both the frontend and the backend (2026-11-23)

- **Status:** Accepted as a mechanism on 2026-11-23. The preset set and its granularity depend on the confirmed job list and headcount.
- **Authority:** Owner request of 2026-11-23.
- **Decision:** Different job levels see different content. The interface structure stays the same for everyone; content a role must not see is locked in place and shown as no permission. For a given role and document type, one configuration defines the visible field set, the editable field set, the permitted operations, role-specific required fields and row-visibility conditions.
- **Architectural constraints:**
  - The same configuration is consumed by the frontend for rendering and by the backend for validation. Frontend locking is a usability feature only; the backend must independently refuse the same action. The existing approval guard is the precedent for this separation.
  - Hiding a field is not data isolation. Record-level data scope must also be enforced at query level through native user permissions, otherwise a hidden value stays readable through the API.
  - Refusal messages must state what is restricted, for example a cost field a role may not view versus a record outside the role's warehouse scope, so staff escalate correctly instead of repeatedly asking an administrator.
  - Presets are data, not code. An administrator must be able to compose and adjust them in the interface; adding a job must not require a code change.
- **Consequences:** ERPNext permission granularity (doctype-level plus field permlevel) cannot express per-role field sets or row filters, so this mechanism is part of the self-owned presentation layer under DEC-016 and is an additional evidence that the frontend and interaction layer must be owned by the project. The preset store becomes a governed configuration asset and must be included in backups, migration and deployment checks.
- **Revisit when:** The client's real job list, headcount and reporting lines are confirmed.

## DEC-021 — Source-specific order profiles use configuration (2026-11-23)

- **Status:** Accepted as a mechanism on 2026-11-23. The profile schema will be validated against real source-order samples.
- **Authority:** Owner request of 2026-11-23.
- **Problem:** Order senders use different formats. Configuration allows additional formats to be supported without a separate release for each sender.
- **Decision:** Each order source gets an import profile describing file format, worksheet and header row, field mapping, the column carrying the item identifier, unit conversion, date format, tax-inclusive or tax-exclusive amounts, the item matching strategy and validation rules. Selecting the order source loads the corresponding profile for review or adjustment before parsing. Whether profiles are assigned to customers or suppliers depends on the confirmed source of the originals.
- **Architectural constraints:**
  - Profiles are configuration data. Staff onboard a new order source by adding a profile.
  - The profile schema follows the existing mapping and reconciliation structure in `phase0/migration/`, so the preflight, preview and reconciliation discipline carries over.
  - Source-file processing produces the bilingual order after human confirmation. Subsequent ERP entry starts as a draft and uses the existing approval chain.
  - Parse results are previewed with per-row errors located to row and column before anything is written.
- **Consequences:** Onboarding cost per supplier becomes configuration work rather than a release. The profile store becomes a governed asset that must be migrated, backed up and versioned. Profiles referencing item units depend on the item master's UOM conversion and on the alias library from DEC-019.
- **Revisit when:** Source-order samples are available or the client identifies scanned orders that require an additional parser.

## DEC-022 — Base replacement proceeds as layered extraction, with explicit triggers for replacing the kernel (2026-11-23)

- **Status:** Accepted by the owner on 2026-11-23, superseding the earlier proposed entry.
- **Authority:** Owner decision recorded in the 2026-11-23 next-step card: 采用分层抽离.
- **Owner intent as stated:** After the required functions are usable, progressively replace the ERPNext base with self-developed content, in both the frontend and the operating logic, ultimately leaving that base behind.
- **Decision:** Work toward that goal by layered extraction rather than by rewriting. The project defines its own Business API contract as a thin layer (L3) between the self-owned presentation layer (L1) and business-orchestration layer (L2) and the kernel (L4). Presentation and orchestration must depend on that contract, not on ERPNext document structures. The accounting, inventory, tax, workflow, permission and reporting kernel stays on ERPNext for now.
- **Rationale:** Reimplementing an equivalent kernel is roughly 15–20 person-months for an experienced team, and the project's validation evidence (C0, M1, A1, nine evidence files, ten PDF templates, the nine-role permission matrix) is built on the current kernel and would have to be rebuilt. The concrete complaints recorded so far all sit in the presentation and interaction layers, which DEC-016 already commits to rebuilding and which do not require a new kernel. Layered extraction keeps the goal reachable while costing almost nothing now.
- **Consequences:** Defining the contract is the only low-cost action available today for this goal, and it also satisfies the standing rule that automation must go through reviewed ERP service boundaries. It fills the previously open "Business API surface and authentication model" decision. Self-owned layers include the workbench and entry forms, pricing, alias matching, import profiles and the job-view presets. Any new feature must be built against the contract rather than against ERPNext document internals.
- **Triggers for revisiting the kernel itself:** after a real-order cycle, core business remains inexpressible in the current data model; the upstream upgrade path breaks at a repair cost above reimplementation; the client requires full data autonomy and accepts kernel maintenance; or funding and staffing appear for a rewrite with full revalidation.
- **Revisit when:** A trigger above is met, a second client appears, or the owner restates the intent.
- **Reference:** `docs/OWNER_DIRECTION_20261123.md` section 4.

## DEC-023 — Same-origin Business API v1 for the W6 draft pilot (2026-11-23; ERPNext adapter validated 2026-11-24)

- **Status:** Contract defined and ERPNext adapter implemented in `hardware_erp.business_api` with hosted entry page `/w6-entry` in `erpnext_zh`; validated against local disposable R1 roles, warehouse permissions, concurrency, idempotency and zero-posting boundaries. Local synthetic demo server remains available for offline rehearsal.
- **Decision:** Antigravity owns the pilot UI and Codex owns the Business API contract, demo server, integration and GitHub delivery. Both surfaces use the versioned same-origin contract in [BUSINESS_API_W6.md](BUSINESS_API_W6.md), covering options and draft create/read/update. ERPNext mapping belongs to the server adapter.
- **ERPNext boundary:** Use the authenticated operator's native session and CSRF checks for writes. Apply native permissions and server-side role rules, enforce revisions and idempotency in the draft-save transaction, and preserve native approval and subsequent posting.
- **Release boundary:** Trial inclusion remains subject to alignment with the frozen R1 scope. External integrations and Agent/MCP remain under their existing roadmap gates.
