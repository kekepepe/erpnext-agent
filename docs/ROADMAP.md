# ERPNext-agent Roadmap

## Roadmap Rules

This file describes phase goals and exit criteria, not daily task status. Daily priorities belong in `AI_HANDOFF.md`. A phase advances only when its exit criteria are supported by repository or validation evidence.

## Phase 0 — ERPNext Native Capability Validation (Current)

**Goal:** determine how much of the hardware-trading workflow ERPNext v16 supports through native configuration.

Scope:

- Disposable local ERPNext validation environment
- Representative, non-sensitive master data
- Purchase, receipt, stock, delivery, sales, returns, and receivable/payable flows
- Permission, approval, auditability, and reporting checks relevant to the workflow
- Evidence-based Gap Analysis

Exit criteria:

- Baseline environment health check passes reproducibly.
- Representative master data and test assumptions are documented.
- Critical end-to-end workflows have recorded expected and actual results.
- Each gap is classified as configuration, process change, integration, customization, or unresolved.
- Phase 1 scope is approved from the evidence.

## Phase 1 — ERP MVP

**Goal:** deliver the minimum usable ERP workflow using native ERPNext first.

Planned scope, subject to Phase 0 evidence:

- Core purchase, inventory, sales, and basic receivable/payable operations
- Required organization, roles, permissions, and approval workflows
- Minimum customer, supplier, item, pricing, and reporting setup
- Operating procedures, acceptance tests, backup, and environment separation

Exit criteria:

- Agreed MVP workflows pass user acceptance testing.
- Roles and approvals are enforced and auditable.
- Deployment, backup, restore, and operating procedures are documented.
- Remaining gaps are explicitly deferred or approved for Phase 2.

## Phase 2 — `hardware_erp` Customization

**Goal:** implement only the business gaps that cannot be acceptably handled by native configuration or process changes.

Potential scope:

- A version-controlled Frappe Custom App named `hardware_erp`
- Approved custom fields, DocTypes, validations, reports, and integrations
- Automated tests and migration/rollback notes for each customization

Exit criteria:

- Every customization traces to an approved Phase 0/1 gap.
- Core ERPNext is not modified directly.
- Custom behaviour has tests and upgrade-impact documentation.
- ERP MVP plus approved custom workflows pass acceptance testing.

## Phase 3 — Business API and MCP Foundation

**Goal:** expose reviewed, permission-aware business operations for AI-assisted use without direct database access.

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

Candidate pilots:

- Enterprise data question answering through approved read APIs
- Inventory risk monitoring and draft purchase recommendations

Exit criteria:

- Each pilot has a human owner, success metrics, failure handling, and an off switch.
- Agent actions are observable, permission-scoped, and auditable.
- Business benefit and operational risk are reviewed before expansion.

## Deferred Direction

Broader CRM/OA coverage, multi-Agent orchestration, predictive workflows, and additional channels remain long-term possibilities. They are not current commitments and must not pre-empt Phase 0 evidence or the approved MVP.
