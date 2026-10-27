# Project Decisions

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

- Exact staging/production rollout environment (R1 functional scope is frozen)
- Any additional proven Must gap beyond the approved bounded approval guard
- Business API surface and authentication model
- First Agent pilot, model/provider, orchestration framework, and success metrics


## DEC-012 — Bounded server-side approval guard as an N2 dependency (2026-10-12)

Status: owner approved 2026-10-12; implemented and synthetically validated during N2. Scope version R1-scope-v1.1.

Two native Purchase Order probe runs reproduced direct over-limit submit, creator self-submit, and simultaneous price mutation+approval; native field-level input protection did not force approval transitions. See `docs/NATIVE_APPROVAL_GAP.md` and the sanitized JSON evidence. These executed Must gaps supersede the earlier no-business-customization conclusion only at the approval boundary.

Keep Workflow, roles, User Permissions, transactions and accounting native. Add an isolated `hardware_erp` application containing document-event validation of state/docstatus, current threshold inputs, maker/approver identity and business-input changes during approval. Do not patch Core, add external API/MCP/Agent or put business validation into `erpnext_zh`. The guard is a necessary N2 dependency, not permission to start unrelated roadmap phases. Ordinary business and ownership parameters remain synthetic until controlled real-data mapping/UAT.

Negative tests must exercise native REST/submit/cancel and normal Workflow routes; app removal/configuration drift must block deployment. The original P0 company remains an explicit disposable discovery fixture exception, not a production bypass namespace. A production preflight must reject P0 fixtures and verify all scoped companies/roles/workflows/app presence.
