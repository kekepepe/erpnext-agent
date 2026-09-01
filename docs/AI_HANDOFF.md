---
project: ERPNext-agent
status: active
current_phase: Phase 0
current_task: Revalidate the Phase 0 runtime, initialize a representative synthetic validation dataset, and establish the Phase 0 evidence ledger
last_updated: 2026-09-01
updated_by: Web GPT
---

# AI Project Handoff

## Current Objective

Complete the first evidence-producing Phase 0 cycle for ERPNext v16 native-capability validation.

The current task has three ordered parts:

1. Re-establish and revalidate the disposable local ERPNext runtime.
2. Initialize a representative, fully synthetic hardware-trading test company and master dataset.
3. Establish a structured Phase 0 validation ledger for later purchase, stock, sales, returns, receivable/payable, permissions/approval, and reporting tests.

Do not begin Custom App, Business API, MCP, Agent, or multi-Agent implementation in this task.

## Verified Current State

- GitHub repository: `kekepepe/erpnext-agent`.
- Default branch: `main`.
- Repository visibility is intentionally **public** for the current Web GPT → GitHub → Codex collaboration workflow.
- Public visibility is a collaboration requirement, not permission to store real business data. Only code, sanitized documentation, and synthetic test data may be committed.
- The repository contains a disposable ERPNext/Frappe v16 Phase 0 environment.
- The Compose configuration uses:
  - ERPNext image: `frappe/erpnext:v16.33.0`
  - MariaDB: `11.8`
  - Redis: `6.2-alpine`
- `scripts/phase0-check.sh` validates:
  - Docker availability
  - Compose configuration
  - `create-site` completion
  - required running services
  - ERPNext/Frappe 16.x versions
  - HTTP ping response
- `docker compose -f phase0/compose.yaml config --quiet` was reported passing on 2026-09-01.
- Historical evidence records a successful runtime baseline on 2026-08-30:
  - ERPNext 16.33.0
  - Frappe 16.31.0
  - `create-site` exit code 0
  - nine required services running
  - HTTP ping returning `pong`
- The above historical runtime evidence is not a substitute for current revalidation.
- On the latest 2026-09-01 runtime attempt, the Docker daemon was not running, so the current runtime state remains **not verified**.
- No current repository evidence proves that the following have been completed:
  - Phase 0 test company initialization
  - approximately 20 representative SKUs
  - 3 suppliers
  - 3 customers
  - representative warehouse/UOM setup
  - native purchase-flow validation
  - native stock-flow validation
  - native sales-flow validation
  - returns validation
  - accounts receivable/payable validation
  - permissions/approval validation
  - reporting validation
- No `hardware_erp` Custom App implementation is currently proven.
- No Business API layer is currently proven.
- No MCP Server implementation is currently proven.
- No Agent implementation is currently proven.
- `ERP与AI智能体设计笔记.md` remains project intent and architectural background, not implementation evidence.
- The project strategy remains:
  - validate ERPNext native capability first
  - identify evidence-based gaps
  - customize only confirmed gaps
  - stabilize Business APIs
  - add MCP
  - add bounded Agent capabilities later

## Completed

- [x] Selected ERPNext/Frappe v16 as the ERP Core direction.
- [x] Defined Phase 0 as ERPNext native-capability validation.
- [x] Bootstrapped a disposable local ERPNext v16 validation environment.
- [x] Pinned Phase 0 container images.
- [x] Added startup and teardown instructions.
- [x] Added `scripts/phase0-check.sh` for baseline runtime validation.
- [x] Recorded a successful historical Phase 0 runtime baseline on 2026-08-30.
- [x] Verified Compose static configuration on 2026-09-01.
- [x] Established `AGENTS.md`, `docs/AI_HANDOFF.md`, `docs/ROADMAP.md`, and `docs/DECISIONS.md` for GitHub-based AI collaboration.
- [x] Established GitHub as the daily Web GPT ↔ Codex coordination channel.
- [x] Established Obsidian as milestone knowledge storage rather than per-task coordination.
- [x] Confirmed that repository public visibility is intentional for the current Web GPT → GitHub → Codex workflow.

## In Progress

- [ ] Revalidate the disposable Phase 0 runtime.
- [ ] Initialize a representative synthetic hardware-trading validation company.
- [ ] Initialize representative master data.
- [ ] Establish `docs/PHASE0_VALIDATION.md` as the evidence ledger for Phase 0.

## Problems / Risks

### Runtime blocker

- The Docker daemon was not running during the latest 2026-09-01 check.
- Until Docker is running and `./scripts/phase0-check.sh` passes again, current runtime health must remain marked as unverified.
- If Docker cannot be started without user interaction, record that exact blocker and stop. Do not switch to unrelated implementation work.

### Public repository boundary

- The repository is intentionally public so Web GPT can read the repository directly and coordinate tasks with Codex.
- Never commit:
  - production secrets
  - reusable credentials
  - API tokens
  - real customer records
  - real supplier records
  - real internal pricing
  - confidential contracts
  - personal information
  - non-public company financial data
  - production database exports
- Phase 0 test data must be synthetic or safely sanitized.

### Validation-evidence gap

- Existing Compose/configuration proves that a validation environment has been prepared.
- It does not prove that ERPNext satisfies the target hardware-trading workflows.
- Native workflow capability must be determined through recorded tests with expected versus actual behaviour.

### Premature customization risk

- Business requirements remain high-level.
- Do not create Custom Fields, Custom DocTypes, Server Scripts, reports, or a Custom App merely because they seem useful.
- Every future customization must trace to a confirmed Phase 0/Phase 1 gap.

### Production-assumption risk

- The Phase 0 Compose environment is disposable.
- Local demo credentials and topology must not be treated as staging or production design.

## Next Actions

### P0 — Current Task

Execute these items in order.

#### P0.1 — Revalidate the runtime

- [ ] Inspect the actual repository and Git state before making changes.
- [ ] Check whether Docker daemon is running.
- [ ] Run:

    docker compose -f phase0/compose.yaml up -d

- [ ] Wait for Site initialization/readiness.
- [ ] If necessary, inspect:

    docker compose -f phase0/compose.yaml logs -f create-site

- [ ] Run:

    ./scripts/phase0-check.sh

- [ ] Record the exact observed result, including:
  - Compose validation
  - `create-site` status and exit code
  - required running services
  - ERPNext version
  - Frappe version
  - ping response
- [ ] If the check fails, preserve the failure evidence and record the smallest concrete unblocking action.
- [ ] Do not mark runtime revalidation complete unless the current check actually passes.

#### P0.2 — Initialize the synthetic test company and representative master data

Proceed only after P0.1 succeeds.

Create or reproducibly define a clearly synthetic hardware-trading test company.

The dataset should be designed to exercise different ERPNext behaviours rather than merely reach a target count.

Minimum target:

- [ ] 1 synthetic hardware-trading company
- [ ] approximately 20 representative SKUs
- [ ] 3 synthetic suppliers
- [ ] 3 synthetic customers
- [ ] at least 2 warehouses
- [ ] representative item groups/categories
- [ ] representative Units of Measure
- [ ] opening stock
- [ ] synthetic purchase prices
- [ ] synthetic selling prices
- [ ] basic tax assumptions
- [ ] opening receivable/payable assumptions only where required for later tests

Representative SKU coverage should include examples such as:

- hand tools
- power tools
- consumables
- accessories
- zero-stock items
- low-stock items
- normally stocked items
- packaged items

Include multiple UOM scenarios, for example:

- Piece
- Box
- Carton

At least one item should validate multi-level packaging conversion, for example:

- 1 Carton = multiple Boxes
- 1 Box = multiple Pieces

Use synthetic names, prices, quantities, company details, customer details, and supplier details.

Prefer reproducible initialization where practical. If data is initialized manually through ERPNext Desk, document enough detail to reproduce it.

#### P0.3 — Establish the Phase 0 validation evidence ledger

- [ ] Create `docs/PHASE0_VALIDATION.md`.
- [ ] Record environment/version evidence.
- [ ] Record test-company assumptions.
- [ ] Record dataset inventory.
- [ ] Define evidence rules.
- [ ] Use only these result states:
  - `Supported`
  - `Configurable`
  - `Gap`
  - `Not Tested`
- [ ] Add structured validation sections for:
  - Purchase
  - Stock
  - Sales
  - Returns
  - Accounts Receivable
  - Accounts Payable
  - Permissions / Approval
  - Reporting

Each test case must support:

- Test ID
- Requirement
- Preconditions
- Steps
- Expected Result
- Actual Result
- Evidence
- Result
- Notes

Seed the checklist for future execution, but leave unexecuted tests as `Not Tested`.

Do not claim workflow success based only on setup, screenshots of configuration, or assumptions.

#### P0.4 — Close out this Codex task

Before handoff:

- [ ] Review actual changed files.
- [ ] Run appropriate validation.
- [ ] Review `git diff`.
- [ ] Review `git status`.
- [ ] Update this `docs/AI_HANDOFF.md` with:
  - what was actually completed
  - actual commands run
  - actual validation results
  - created/initialized master data
  - changed files
  - unresolved failures
  - blockers
  - recommended next action
- [ ] Do not change `docs/ROADMAP.md` unless phase scope, dependency, milestone, or exit criteria actually changed.
- [ ] Do not change `docs/DECISIONS.md` unless a durable architecture/security/workflow decision actually changed.
- [ ] Do not modify Obsidian during this routine development task.
- [ ] Do not start transaction-flow validation unless the current task has been completed and handed back for review.
- [ ] Do not start Phase 1, Custom App, API, MCP, or Agent work.

### P0 — Next After Current Task

These are the next Phase 0 activities, but they are not part of the current Codex task unless the handoff is explicitly updated after review.

- [ ] Execute Purchase validation:
  - Purchase Order
  - full receipt
  - partial/multiple receipts
  - Purchase Invoice
  - Accounts Payable
  - supplier payment
  - alternate UOM
  - purchase return
- [ ] Execute Stock validation:
  - opening stock
  - stock increase from receipt
  - stock decrease from delivery
  - warehouse transfer
  - stock reconciliation
  - insufficient-stock behaviour
  - UOM conversion effects
- [ ] Execute Sales validation:
  - Quotation
  - Sales Order
  - full delivery
  - partial/multiple deliveries
  - Sales Invoice
  - Accounts Receivable
  - customer payment
  - alternate UOM
  - sales return
- [ ] Validate relevant permissions and role separation.
- [ ] Validate native approval/workflow options.
- [ ] Validate approval/audit history.
- [ ] Validate stock, purchase, sales, receivable, and payable reporting.
- [ ] Record every tested requirement as `Supported`, `Configurable`, `Gap`, or `Not Tested`.
- [ ] Build the evidence-based Gap Analysis.

### P1 — After Phase 0 Evidence Review

- [ ] Review all confirmed gaps with business impact.
- [ ] For every gap, determine whether it should be solved by:
  - native configuration
  - process adjustment
  - integration
  - customization
  - deferment
  - unresolved investigation
- [ ] Define the minimum ERP MVP scope.
- [ ] Decide the minimum `hardware_erp` Custom App scope only from confirmed evidence.
- [ ] Do not modify ERPNext Core.

### P2 — Later

- [ ] Design stable Business API boundaries around approved ERP workflows.
- [ ] Define authentication and authorization.
- [ ] Define idempotency/error contracts for write operations.
- [ ] Define audit logging.
- [ ] Define approval gates for consequential actions.
- [ ] Expose approved ERP operations through MCP.
- [ ] Implement the first bounded Agent pilot only after API/MCP governance is ready.
- [ ] Keep Agents away from direct database access.

## Acceptance Criteria

The current task is complete only when all applicable criteria below are satisfied with actual evidence.

### Runtime

- `docker compose -f phase0/compose.yaml config --quiet` exits successfully.
- `create-site` is complete with exit code 0.
- All services required by `scripts/phase0-check.sh` are running.
- ERPNext reports version 16.x.
- Frappe reports version 16.x.
- `http://localhost:8080/api/method/ping` returns `pong` through the validation script.
- Current command output/date/result is recorded.
- Any failure remains visible rather than being rewritten as success.

### Validation dataset

- A clearly synthetic test company exists or is reproducibly defined.
- Approximately 20 representative SKUs exist or are reproducibly defined.
- 3 synthetic suppliers exist or are reproducibly defined.
- 3 synthetic customers exist or are reproducibly defined.
- At least 2 warehouses exist or are reproducibly defined.
- UOM scenarios include meaningful conversions.
- Opening stock is defined.
- Synthetic purchase/sales prices are defined.
- No non-public real business data has been committed.

### Validation framework

- `docs/PHASE0_VALIDATION.md` exists.
- It records environment and dataset assumptions.
- It defines the four allowed result states.
- It includes all required validation areas.
- It provides the required per-test evidence fields.
- Unexecuted tests remain `Not Tested`.

### Handoff quality

- `docs/AI_HANDOFF.md` reflects actual repository/runtime state after execution.
- Completed and incomplete work are clearly separated.
- Blockers and unresolved issues remain visible.
- `git diff` and `git status` have been reviewed.
- No later-phase implementation was started opportunistically.

## Notes for Next Agent

- Read in this order before acting:
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/AI_HANDOFF.md`
  4. `docs/ROADMAP.md`
  5. `docs/DECISIONS.md`
  6. `docs/PHASE0_VALIDATION.md` if present
- Then inspect actual code, configuration, Git state, available tests, and runtime state.
- Actual implementation and observed runtime evidence outrank documentation.
- The current repository is intentionally public for Web GPT → GitHub → Codex coordination.
- Use synthetic/sanitized data only.
- Never commit secrets or private business information.
- The current task ends after:
  - runtime revalidation
  - representative synthetic master-data initialization
  - Phase 0 evidence-ledger creation
- Do not begin transaction-flow testing until this task is completed and the handoff is reviewed.
- Do not begin Custom App, API, MCP, Agent, or multi-Agent work.
- Preserve ERPNext Core.
- Treat `ERP与AI智能体设计笔记.md` as project direction, not proof that any component exists.
- Update this handoff in the same change as implementation or validation evidence.
