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

## Open Decisions

The following are intentionally undecided pending evidence:

- Exact ERP MVP scope and rollout environment
- Which Phase 0 gaps require `hardware_erp` customization
- Business API surface and authentication model
- First Agent pilot, model/provider, orchestration framework, and success metrics
