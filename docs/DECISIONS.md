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

## Open Decisions

The following are intentionally undecided pending evidence:

- Exact ERP MVP scope and rollout environment
- Whether the repository's current public visibility is intentional or should return to private
- Which Phase 0 gaps require `hardware_erp` customization
- Business API surface and authentication model
- First Agent pilot, model/provider, orchestration framework, and success metrics
