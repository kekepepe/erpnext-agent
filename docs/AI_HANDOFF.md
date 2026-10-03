---
project: ERPNext-agent
status: active
current_phase: Phase 0
current_task: Execute P0.7 reporting validation and Gap Analysis as the first gate in the Phase 0 development-closeout plan
last_updated: 2026-10-03
updated_by: Codex
---

# AI Project Handoff

## Current Objective

Native Quote-to-Cash validation is complete for `SAL-001` through `SAL-010`, including customer stock return, Sales Invoice credit-note evidence, full and partial customer payments, and transaction-level Accounts Receivable evidence.

The implementation used source-controlled synthetic scenarios and an idempotent REST validator. Two complete post-correction runs reused every matching document and reproduced identical stock, outstanding-balance, payment-allocation, and party-GL results.

P0.5 and P0.6 were revalidated and completed on 2026-10-03. The current implementation task is now:

**Execute P0.7 native stock, purchase, sales, Accounts Payable, Accounts Receivable, and General Ledger reporting validation, then build the evidence-based Phase 0 Gap Analysis.**

### Phase boundary directive — 2026-10-03

The project owner has reset the delivery boundary:

- **Phase 0 is the complete development and release-candidate preparation phase.** All functionality, native configuration, approved customization, deployment-required integration, migration tooling, automated validation, and release-readiness work for the first deployable ERP release must be completed and accepted here.
- **Phase 1 is the deployment and rollout phase.** It may provision environments, apply the accepted release, migrate approved data, execute deployment/UAT/cutover procedures, and stabilize operations. It must not be used to finish planned product development.
- P0.7 is only the first remaining Phase 0 gate. Passing P0.7 authorizes scope freeze and implementation planning, not progression to Phase 1.
- A Phase 1 deployment defect that requires a business-logic, schema, custom-app, report, integration-contract, or migration-code change must return to Phase 0, produce a new release candidate, and repeat the affected acceptance gates.
- Future Agent, MCP, and multi-Agent work is not silently pulled into the first ERP release. It remains deferred unless the project owner explicitly adds it to the Phase 0 release scope.

`docs/ROADMAP.md` and `docs/DECISIONS.md` now record this phase boundary at milestone level. This handoff remains the source for the ordered daily execution plan; P0.8 must refine the approved first-release scope without moving development into Phase 1.

Simplified Chinese is now the native site default, with an English per-user override proven through authenticated Desk boot sessions. Native role separation and configurable approval/audit workflows passed for Purchase Order, Sales Order, and Payment Entry. `AR-004`, `AP-004`, reporting, bilingual print output, Gap Analysis, Phase 1, `hardware_erp`, Business API, MCP, Agent, and multi-Agent work remain incomplete.

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
- Latest verified and pushed main commit:
  - `5a39923`
  - `test: complete phase 0 sales and access validation`
- Repository visibility is intentionally **public** for the current Web GPT → GitHub → Codex collaboration workflow.
- Public visibility is a collaboration requirement only. It is not permission to commit real company data.
- Only code, synthetic data, sanitized examples, non-sensitive documentation, and validation evidence may be committed.
- No GitHub Actions workflow run or combined commit status was found for the latest validated commit during Web GPT review.
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

- runtime validation date: `2026-10-03 +0800`
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

- `AR-004`
- remaining Accounts Payable reporting case(s)
- stock/purchase/sales/AR/AP reporting coverage
- bilingual customer/supplier-facing print output
- final evidence-based Phase 0 Gap Analysis
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
- [x] Defined Phase 0 as ERPNext native-capability validation.
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

## In Progress

- [ ] Execute P0.7 native reporting validation and the evidence-based Phase 0 Gap Analysis.

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

Transaction and permissions/approval validation are sufficiently complete. P0.7 is now the current task.

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

- [ ] `LANG-003` — Execute Chinese and English print/preview output for representative purchase and sales documents.
- [ ] Distinguish interface translation, saved master/transaction data, standard print labels, and custom translated content.
- [ ] Classify bilingual output as `Supported`, `Configurable`, `Gap`, or `Not Tested` from actual rendered evidence.
- [ ] Do not build custom print formats merely to force a passing Phase 0 result.

#### P0.7.7 — Produce the evidence-based Gap Analysis

- [ ] Review every `Not Tested`, `Configurable`, failed, or unexpected case in `docs/PHASE0_VALIDATION.md`.
- [ ] Create `docs/PHASE0_GAP_ANALYSIS.md` only after the report and bilingual-output evidence above exists.
- [ ] Classify each confirmed issue as native configuration, acceptable process adjustment, integration, customization, deferment, or unresolved investigation.
- [ ] Record business impact, evidence, workaround, recommended owner, and Phase 0 implementation or explicit post-release deferral for each item.
- [ ] Do not classify a preference as a technical gap without execution evidence.

#### P0.7.8 — P0.7 closeout and review gate

- [ ] Run JSON validation and Python compilation for every new or changed scenario/validator.
- [ ] Run the complete reporting validator twice and prove idempotent read-only results.
- [ ] Re-run `./scripts/phase0-check.sh`.
- [ ] Review `git diff`, `git diff --check`, and `git status`.
- [ ] Update `docs/PHASE0_VALIDATION.md`, this handoff, and the Gap Analysis with actual results and failures.
- [ ] Confirm the native-capability validation exit criteria currently recorded in `docs/ROADMAP.md` have evidence.
- [ ] Obtain an explicit P0.7 review decision before advancing the handoff to P0.8 scope freeze; do not change the current phase to Phase 1.

Expected P0.7 deliverables:

- `phase0/reporting-validation.json`
- `scripts/phase0-validate-reporting.py`
- updated `docs/PHASE0_VALIDATION.md`
- `docs/PHASE0_GAP_ANALYSIS.md` after evidence is sufficient
- updated `docs/AI_HANDOFF.md`

P0.7 must remain read-only with respect to validated business transactions wherever possible. It may create only narrowly scoped report/print evidence when native execution requires it, and must preserve all existing P0 balances and audit fixtures.

### P0.8 — First-release scope freeze and phase-document alignment

Begin only after P0.7 evidence and the Gap Analysis are reviewed. This gate turns evidence into an approved, testable first-release scope.

- [ ] Build a requirement-to-evidence matrix for purchase, stock, sales, returns, AR, AP, reporting, language/print, permissions, approvals, audit, and required operating controls.
- [ ] For every confirmed requirement, record one disposition: native configuration, process/SOP, `hardware_erp` customization, deployment-required integration, or explicit post-release deferral.
- [ ] Label each item `Must`, `Should`, or `Deferred`; no `Must` item may have an unresolved owner, acceptance criterion, or implementation path.
- [ ] Define measurable acceptance criteria and the validation layer for every `Must` and accepted `Should` item.
- [ ] Freeze the first-release functional scope, supported organization structure, roles, approval matrix, language/print boundary, reports, and data-migration scope.
- [ ] Decide whether `hardware_erp` is required. If no confirmed gap requires it, record that the first release remains native/configuration-only.
- [ ] Explicitly decide whether any external integration or governed Business API is required for the first deployment. Keep MCP and Agent work deferred unless separately approved by the project owner.
- [ ] Verify that the approved first-release scope remains consistent with the Phase 0 development / Phase 1 deployment boundary in `docs/ROADMAP.md`.
- [ ] Refine `docs/DECISIONS.md` only if P0.8 introduces another durable architecture, security, or workflow decision beyond the recorded phase boundary.
- [ ] Update this handoff so the first unchecked P0 item is the first approved implementation package.

P0.8 deliverables:

- approved requirement-to-evidence and scope matrix
- updated `docs/PHASE0_GAP_ANALYSIS.md`
- confirmed phase alignment across `docs/ROADMAP.md`, `docs/DECISIONS.md`, and this handoff
- ordered Phase 0 implementation backlog with owners and acceptance evidence

### P0.9 — Complete native ERP configuration and operating model

Implement and source-control every approved native/configuration-first requirement before writing custom code for the same need.

- [ ] Finalize organization, company, fiscal, chart-of-accounts, tax, warehouse, item/UOM, pricing, customer, supplier, and numbering configuration required by the frozen scope.
- [ ] Finalize least-privilege roles, User Permissions, approval thresholds, Workflows, segregation of duties, and audit retention settings.
- [ ] Finalize required native reports, dashboards, print formats, language settings, and customer/supplier-facing output.
- [ ] Store reproducible fixtures, exports, scripts, or documented configuration steps without committing secrets or real business records.
- [ ] Write operator SOPs for master data, purchase, receiving, stock, sales, returns, AR/AP, approval, reconciliation, period operations, and exception handling.
- [ ] Add automated or repeatable acceptance checks and rerun affected regression validators twice where idempotency applies.
- [ ] Update validation evidence and close each native/configuration item against its requirement ID.

### P0.10 — Implement only approved customization gaps

This package is conditional. Skip it with an explicit evidence-backed decision if P0.8 finds no required customization.

- [ ] Create `hardware_erp` only for approved `Must`/accepted `Should` gaps that native configuration or an acceptable process cannot satisfy.
- [ ] Trace every custom field, DocType, validation, report, hook, permission rule, and integration point to a frozen requirement and confirmed gap.
- [ ] Preserve ERPNext Core; do not patch core files.
- [ ] Add unit/integration/permission tests, fixtures, migration patches, uninstall/rollback notes, and upgrade-impact notes for each customization.
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

P0.6 is complete. The next task is P0.7 reporting validation and Gap Analysis. Bilingual print output remains untested and must not be inferred from the successful Desk language result.

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
- The current task is P0.7 reporting validation and evidence-based Gap Analysis.
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
- P0.7 is the current task and the first gate of the remaining Phase 0 plan; proceed to P0.8 after its explicit review, not to Phase 1.
- Do not begin `hardware_erp` or deployment-required integration development during P0.7. They may begin only if P0.8 approves them and orders them into P0.10/P0.11.
- Do not begin Phase 1 until P0.7 through P0.12 are complete and deployment readiness is explicitly approved.
- Keep MCP, Agent, and multi-Agent work deferred unless the project owner explicitly adds it to a future Phase 0 release scope.
- Treat `ERP与AI智能体设计笔记.md` as direction, not implementation proof.
- Update this handoff in the same change as the implementation/evidence it describes.
- The owner-approved Phase 0 development / Phase 1 deployment boundary is recorded in `docs/ROADMAP.md` and `docs/DECISIONS.md`; keep them aligned if P0.8 changes milestones or introduces another durable decision.
- Do not modify Obsidian during this routine Phase 0 task.
