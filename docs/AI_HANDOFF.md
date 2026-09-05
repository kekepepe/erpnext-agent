---
project: ERPNext-agent
status: active
current_phase: Phase 0
current_task: Execute native sales and accounts-receivable validation for SAL-001 through SAL-010, including customer sales-return evidence, while keeping later Phase 0 areas and all Phase 1+ implementation out of scope
last_updated: 2026-09-05
updated_by: Web GPT
---

# AI Project Handoff

## Current Objective

The completed native purchase and stock evidence has been reviewed and accepted as sufficient to advance to the next Phase 0 validation task.

The current implementation task is now:

**Validate ERPNext v16 native Quote-to-Cash behaviour using reproducible synthetic scenarios, beginning with `SAL-001`, and record actual execution evidence for sales, customer payment, Accounts Receivable, alternate-UOM sales, and customer sales returns.**

Target transaction path:

Quotation → Sales Order → Delivery Note → Sales Invoice → Accounts Receivable → Customer Payment → Sales Return

Primary validation IDs already defined in `docs/PHASE0_VALIDATION.md`:

- `SAL-001` — Create Quotation
- `SAL-002` — Create and submit Sales Order
- `SAL-003` — Deliver full Sales Order quantity
- `SAL-004` — Deliver one Sales Order through multiple partial deliveries
- `SAL-005` — Sell an item using an alternate UOM with conversion
- `SAL-006` — Delivery correctly reduces stock
- `SAL-007` — Create Sales Invoice
- `SAL-008` — Sales Invoice creates Accounts Receivable
- `SAL-009` — Record full customer payment
- `SAL-010` — Record partial customer payment

Related return cases:

- `RET-001` — Customer returns previously sold goods
- `RET-003` — Sales return reverses stock effects correctly
- `RET-005` — Return-related accounting effects are traceable

Related receivable cases:

- `AR-001` — Sales Invoice creates customer receivable
- `AR-002` — Full payment clears customer outstanding balance
- `AR-003` — Partial payment reduces outstanding balance correctly
- `AR-004` — Outstanding receivables can be reported
- `AR-005` — Receivable history is traceable to source documents

The current task must execute the sales transaction-flow evidence first. `AR-004` reporting remains part of the later reporting task unless it is explicitly and independently tested here. Do not mark any case `Supported` merely because transaction data created during this task could theoretically support it.

Do not begin permissions, approval workflow, Phase 1, `hardware_erp`, Business API, MCP, Agent, or multi-Agent implementation during this task.

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
- Latest verified main commit during this handoff review:
  - `af6b1db8a15c0278ce08888d6709a3d77d82107f`
  - `test: validate phase 0 purchase and stock flows`
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

- runtime validation date: `2026-09-05 15:28:51 +0800`
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

### API boundary already demonstrated during Phase 0

The reusable client:

- `scripts/phase0_api.py`

uses ERPNext HTTP REST resources and explicitly called whitelisted ERPNext methods.

Current Phase 0 scripts do **not** require direct MariaDB access to perform tested transactions.

This is consistent with the architectural constraint that future automation must operate through reviewed ERP service/API boundaries.

Do not interpret the current Phase 0 REST client as the final Business API layer. The governed Business API remains a later phase.

### Areas still not proven

No valid execution evidence currently proves completion of:

- `SAL-001` through `SAL-010`
- `RET-001`
- `RET-003`
- `RET-005`
- `AR-001` through `AR-005`
- remaining Accounts Payable reporting case(s)
- permissions and role separation
- native approval workflow behaviour
- approval/audit history requirements
- stock/purchase/sales/AR/AP reporting coverage
- final evidence-based Phase 0 Gap Analysis
- Phase 1 ERP MVP
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

## In Progress

- [ ] Execute native Quote-to-Cash sales validation beginning with `SAL-001`.
- [ ] Establish reproducible source-controlled sales-validation scenarios.
- [ ] Record transaction, stock, Accounts Receivable, payment, and sales-return evidence.
- [ ] Preserve all execution failures and corrections.
- [ ] Prove validator idempotency through a second complete run.

## Problems / Risks

### Runtime lifecycle

The Phase 0 environment is disposable.

A previous Docker Desktop stopped-state blocker was resolved, but that does not prove Docker is running for the next task.

Before sales validation:

- check Docker
- start/reuse the Phase 0 stack
- run `./scripts/phase0-check.sh`
- stop if runtime health cannot be re-established

Do not claim current runtime health from an old timestamp.

### Shared mutable Phase 0 dataset

Purchase and stock validation intentionally changed synthetic inventory and accounting state.

The sales validator must use the **current validated state**, or use scenarios whose expected baseline can be deterministically read back before execution.

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

Static CI may be added later if useful, but do not let CI infrastructure work displace the current sales-validation task.

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

This is the current Codex task.

Execute in this order.

#### P0.5.1 — Inspect and re-establish runtime

- [ ] Read:
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/AI_HANDOFF.md`
  4. `docs/ROADMAP.md`
  5. `docs/DECISIONS.md`
  6. `docs/PHASE0_VALIDATION.md`
- [ ] Inspect actual Git state.
- [ ] Preserve unrelated user changes if the worktree is dirty.
- [ ] Confirm the current branch and relationship to `origin/main`.
- [ ] Inspect the existing seed, purchase validator, stock validator, REST client, and validation JSON files before designing the sales validator.
- [ ] Check Docker availability.
- [ ] Start/reuse the Phase 0 stack if necessary:

    docker compose -f phase0/compose.yaml up -d

- [ ] Run:

    ./scripts/phase0-check.sh

- [ ] Record actual command outcome and runtime evidence.
- [ ] If runtime validation fails, preserve the failure and stop transaction work until the smallest concrete blocker is resolved.
- [ ] Do not mark runtime validation successful unless the command actually passes.

#### P0.5.2 — Revalidate required synthetic master data

- [ ] Run the existing seed idempotently:

    python3 scripts/phase0-seed.py

- [ ] Confirm required customers, items, warehouses, selling prices, and UOM conversions still exist.
- [ ] Do not reset the database merely to simplify the sales test.
- [ ] Do not destroy existing purchase/stock evidence with `down -v`.
- [ ] Preserve the CNY 60 open payable unless there is a documented reason the current task requires otherwise.

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

- [ ] `SAL-001` — Create Quotation
- [ ] `SAL-002` — Create and submit Sales Order
- [ ] `SAL-003` — Deliver full Sales Order quantity
- [ ] `SAL-004` — Deliver one Sales Order through multiple partial deliveries
- [ ] `SAL-005` — Sell an item using an alternate UOM with conversion
- [ ] `SAL-006` — Delivery correctly reduces stock
- [ ] `SAL-007` — Create Sales Invoice
- [ ] `SAL-008` — Sales Invoice creates Accounts Receivable
- [ ] `SAL-009` — Record full customer payment
- [ ] `SAL-010` — Record partial customer payment

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

- [ ] `RET-001` — Customer returns previously sold goods
- [ ] `RET-003` — Sales return reverses stock effects correctly
- [ ] `RET-005` — Return-related accounting effects are traceable

Where native ERPNext behaviour separates stock return and invoice/credit accounting behaviour, record that distinction rather than merging different native concepts into a false single workflow.

Document the exact native return path used.

#### P0.5.7 — Execute Accounts Receivable evidence

Validate transaction-level AR cases:

- [ ] `AR-001` — Sales Invoice creates customer receivable
- [ ] `AR-002` — Full payment clears customer outstanding balance
- [ ] `AR-003` — Partial payment reduces outstanding balance correctly

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

- [ ] Run appropriate JSON validation.
- [ ] Run Python compilation/static syntax validation for changed scripts.
- [ ] Run `./scripts/phase0-check.sh`.
- [ ] Run the seed.
- [ ] Run the complete sales validator.
- [ ] Run the complete sales validator a second time.
- [ ] Review `git diff`.
- [ ] Review `git status`.
- [ ] Update this `docs/AI_HANDOFF.md` with actual results.
- [ ] Record exact changed files.
- [ ] Record all relevant document IDs.
- [ ] Record outstanding balances.
- [ ] Record final affected stock balances.
- [ ] Record GL evidence where applicable.
- [ ] Record failures and corrections.
- [ ] Recommend the next Phase 0 task based on evidence.
- [ ] Do not start permissions/reporting work unless this handoff has first been completed.
- [ ] Do not start Phase 1+ work.

### P0.6 — Permissions, Roles, Approval and Audit Validation

Do not start until P0.5 is completed and reviewed.

Planned next scope:

- [ ] Define representative synthetic Phase 0 roles/users if required.
- [ ] Validate relevant purchase permissions.
- [ ] Validate relevant sales permissions.
- [ ] Validate stock-operation permissions.
- [ ] Validate accounting/payment permissions.
- [ ] Verify create/read/write/submit/cancel boundaries relevant to the MVP.
- [ ] Validate native ERPNext approval/workflow options where relevant.
- [ ] Validate approval history / Version / audit trace where applicable.
- [ ] Classify results as `Supported`, `Configurable`, `Gap`, or `Not Tested`.
- [ ] Avoid customization before the result is known.

### P0.7 — Reporting Validation and Gap Analysis

Do not start until transaction and permissions/approval validation are sufficiently complete.

Validate relevant native reports or equivalent native query/report functions for:

- [ ] Stock Balance
- [ ] Stock Ledger
- [ ] purchase status/analytics
- [ ] sales status/analytics
- [ ] Accounts Payable
- [ ] Accounts Receivable
- [ ] General Ledger
- [ ] traceability from report balance to source transaction where required

Use deliberately preserved open balances where useful:

- supplier payable CNY 60
- partial customer receivable created during P0.5

After the required Phase 0 evidence is complete:

- [ ] Review every unresolved or failed requirement.
- [ ] Build the evidence-based Gap Analysis.
- [ ] Classify each gap as:
  - native configuration
  - acceptable process adjustment
  - integration
  - customization
  - deferment
  - unresolved investigation
- [ ] Do not classify a preference as a technical gap without evidence.
- [ ] Recommend Phase 1 MVP scope based on the completed ledger.

A dedicated document such as `docs/PHASE0_GAP_ANALYSIS.md` may be created when enough evidence exists. Do not create it prematurely with speculative gaps.

## P1 — After Phase 0 Evidence Review

Phase 1 remains blocked until the Phase 0 exit criteria are satisfied and reviewed.

Future P1 actions:

- [ ] Review all confirmed Phase 0 gaps with business impact.
- [ ] Approve the minimum usable ERP MVP workflow.
- [ ] Decide which requirements are met by native ERPNext.
- [ ] Decide which requirements require configuration.
- [ ] Decide which requirements require process changes.
- [ ] Define required organization/role/approval configuration.
- [ ] Define minimum production-relevant operational requirements:
  - environment separation
  - backup
  - restore
  - deployment
  - operating procedures
  - UAT
- [ ] Define the minimum `hardware_erp` customization scope only from confirmed evidence.
- [ ] Preserve ERPNext Core.

Do not treat the disposable Phase 0 Compose topology as approved production architecture.

## P2 — Later Customization and Integration Work

Only after Phase 0 evidence and Phase 1 scope justify it:

- [ ] Create `hardware_erp` only for approved gaps.
- [ ] Trace every customization to a confirmed requirement/gap.
- [ ] Add automated tests for custom behaviour.
- [ ] Document migration and rollback impact.
- [ ] Do not modify ERPNext Core.

After ERP workflows and customization boundaries stabilize:

- [ ] Design stable Business API boundaries.
- [ ] Define authentication.
- [ ] Define authorization.
- [ ] Define least-privilege service identities.
- [ ] Define idempotency contracts.
- [ ] Define error contracts.
- [ ] Define audit logging.
- [ ] Define approval gates for consequential writes.
- [ ] Expose reviewed business operations through MCP.

Only after those boundaries are proven:

- [ ] Implement the first bounded Agent pilot.
- [ ] Keep Agents away from direct database access.
- [ ] Require human approval for consequential operations.
- [ ] Define observable success/failure criteria and an off switch.
- [ ] Consider multi-Agent orchestration only after narrow pilots prove value.

## Acceptance Criteria

The current `P0.5` task is complete only when the applicable criteria below are supported by actual evidence.

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
- The current task is sales + AR transaction validation beginning with `SAL-001`.
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
- Do not begin permissions/reporting until the current sales handoff is complete unless a small supporting check is inseparable from proving the current transaction.
- Do not begin Phase 1, `hardware_erp`, Business API, MCP, Agent, or multi-Agent work.
- Treat `ERP与AI智能体设计笔记.md` as direction, not implementation proof.
- Update this handoff in the same change as the implementation/evidence it describes.
- Do not update `docs/ROADMAP.md` unless phase scope, milestone, dependency, or exit criteria genuinely change.
- Do not update `docs/DECISIONS.md` unless a durable architecture, security, or workflow decision genuinely changes.
- Do not modify Obsidian during this routine Phase 0 task.
