# ERPNext-agent Roadmap

## Roadmap Rules

This file describes phase goals and exit criteria, not daily task status. Daily priorities belong in `AI_HANDOFF.md`. A phase advances only when its exit criteria are supported by repository or validation evidence.

## Phase 0 — Development and Deployable Release Preparation (Current)

**Goal:** complete, validate, and package the full approved first ERP release before deployment begins.

Language scope directive (2026-10-06): the owner now requires Simplified Chinese system display names and active-user language. Technical identifiers and externally entered identity/content remain unchanged. This approves the bounded presentation package only; it does not accept P0.7 progression or freeze all P0.8 release requirements. See DEC-009.

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
- ERPNext Core remains unmodified.

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
