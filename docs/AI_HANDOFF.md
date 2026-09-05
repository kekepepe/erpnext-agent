---
project: ERPNext-agent
status: active
current_phase: Phase 0
current_task: Review the completed native stock-flow evidence before beginning sales validation
last_updated: 2026-09-05
updated_by: Codex
---

# AI Project Handoff

## Current Objective

Review the completed native stock-flow evidence. After review, the next implementation task is native sales validation beginning with `SAL-001`; later phases remain out of scope.

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
- `docker compose -f phase0/compose.yaml config --quiet` passed on 2026-09-01.
- Current runtime revalidation passed on 2026-09-01 23:39:52 +0800:
  - `create-site` status `exited`, exit code `0`
  - all nine required long-running services were running
  - ERPNext 16.33.0
  - Frappe 16.31.0
  - HTTP ping `{"message":"pong"}`
  - `./scripts/phase0-check.sh` exit code `0`
- Historical evidence records a successful runtime baseline on 2026-08-30:
  - ERPNext 16.33.0
  - Frappe 16.31.0
  - `create-site` exit code 0
  - nine required services running
  - HTTP ping returning `pong`
- The reproducible dataset is defined in `phase0/synthetic-data.json` and applied through `scripts/phase0-seed.py` using authenticated ERPNext REST APIs, not direct database access.
- Current API readback proves the following synthetic dataset exists:
  - company `Phase Zero Hardware Trading Demo` (`PZH`, China, CNY)
  - two P0 warehouses
  - four P0 item groups
  - Piece, Box, and Carton UOM coverage
  - three P0 suppliers
  - three P0 customers
  - 20 P0 stock items covering hand tools, power tools, consumables, accessories, zero stock, low stock, normal stock, and packaged items
  - 40 Item Price records: one Standard Buying and one Standard Selling price per item
  - submitted Opening Stock reconciliation `MAT-RECO-2026-00001` with 18 non-zero item rows; two items intentionally start at zero
  - `P0-CO-SCREW` conversions Piece `1`, Box `50`, Carton `500`
- A final rerun of `python3 scripts/phase0-seed.py` exited `0` and identified every entity plus the submitted opening-stock document as existing, without creating duplicates.
- `docs/PHASE0_VALIDATION.md` now records runtime evidence, dataset assumptions and inventory, initialization failures and corrections, evidence rules, and seeded validation cases.
- Native purchase-flow validation passed on 2026-09-05 through `scripts/phase0-validate-purchase.py`:
  - three submitted Purchase Orders
  - one full receipt and one order received through two partial receipts
  - one 2-Box receipt converted to 100 Piece
  - two submitted Purchase Invoices
  - one full and one partial supplier Payment Entry
  - one 1-Box purchase return converted to -50 Piece
  - REST readback of document statuses, links, quantities, invoice outstanding amounts, and Bin balances
  - GL readback proving supplier payable creation and full/partial settlement
- Purchase cases `PUR-001` through `PUR-010`, stock cases `STK-001` through `STK-010`, return cases `RET-002` and `RET-004`, and payable cases `AP-001`, `AP-002`, `AP-003`, and `AP-005` are recorded as `Supported`.
- Native stock validation passed on 2026-09-05 through `scripts/phase0-validate-stock.py`: all cases `STK-001` through `STK-010` are now recorded as `Supported`.
- Stock evidence includes 18 matching opening balances, delivery quantity reduction, a main-to-secondary warehouse transfer, stock reconciliation, a zero-stock query, native insufficient-stock rejection, item-level queries, warehouse-level queries, and an idempotent rerun.
- No execution evidence yet proves the sales, customer return, receivable, permissions/approval, or reporting cases; those remain `Not Tested`.
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
- [x] Revalidated the current Phase 0 runtime on 2026-09-01.
- [x] Added and executed a reproducible REST API seed for a fully synthetic validation company and representative master data.
- [x] Initialized and read back 20 items, 3 suppliers, 3 customers, 2 warehouses, 40 prices, UOM conversions, and submitted opening stock.
- [x] Established `docs/PHASE0_VALIDATION.md` as the Phase 0 evidence ledger.
- [x] Executed and recorded native purchase validation `PUR-001` through `PUR-010`.
- [x] Verified full and partial receipt, alternate-UOM stock conversion, Purchase Invoice payable posting, full and partial supplier payment, and purchase return stock reversal.
- [x] Executed and recorded native stock validation `STK-001` through `STK-010`.
- [x] Verified opening balances, delivery reduction, warehouse transfer, reconciliation, zero/insufficient-stock behaviour, item queries, and warehouse queries.

## In Progress

- [ ] Review the completed stock-flow evidence before starting sales validation.

## Problems / Risks

### Runtime lifecycle

- Docker Desktop was initially stopped on 2026-09-01. It was started and the runtime check then passed; this blocker is resolved for the current session.
- The environment remains disposable. Future tasks must rerun `./scripts/phase0-check.sh` rather than infer health from this record.

### Seed behaviour learned

- ERPNext forbids list filtering on Stock Reconciliation `remarks`, and the submitted document did not retain the supplied remarks value.
- Opening Stock requires an Asset/Liability difference account; the seed uses the standard generated `Temporary Opening - PZH` Asset account.
- Idempotent opening-stock detection therefore compares company, purpose, submitted status, and the full item/warehouse/quantity set.

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

- [x] Inspect the actual repository and Git state before making changes.
- [x] Check whether Docker daemon is running.
- [x] Run:

    docker compose -f phase0/compose.yaml up -d

- [x] Wait for Site initialization/readiness.
- [x] If necessary, inspect:

    docker compose -f phase0/compose.yaml logs -f create-site

- [x] Run:

    ./scripts/phase0-check.sh

- [x] Record the exact observed result, including:
  - Compose validation
  - `create-site` status and exit code
  - required running services
  - ERPNext version
  - Frappe version
  - ping response
- [x] If the check fails, preserve the failure evidence and record the smallest concrete unblocking action.
- [x] Do not mark runtime revalidation complete unless the current check actually passes.

#### P0.2 — Initialize the synthetic test company and representative master data

Proceed only after P0.1 succeeds.

Create or reproducibly define a clearly synthetic hardware-trading test company.

The dataset should be designed to exercise different ERPNext behaviours rather than merely reach a target count.

Minimum target:

- [x] 1 synthetic hardware-trading company
- [x] approximately 20 representative SKUs
- [x] 3 synthetic suppliers
- [x] 3 synthetic customers
- [x] at least 2 warehouses
- [x] representative item groups/categories
- [x] representative Units of Measure
- [x] opening stock
- [x] synthetic purchase prices
- [x] synthetic selling prices
- [x] basic tax assumptions
- [x] Opening receivable/payable assumptions were not added because they are not required until the later AR/AP transaction tests.

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

- [x] Create `docs/PHASE0_VALIDATION.md`.
- [x] Record environment/version evidence.
- [x] Record test-company assumptions.
- [x] Record dataset inventory.
- [x] Define evidence rules.
- [x] Use only these result states:
  - `Supported`
  - `Configurable`
  - `Gap`
  - `Not Tested`
- [x] Add structured validation sections for:
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

- [x] Review actual changed files.
- [x] Run appropriate validation.
- [x] Review `git diff`.
- [x] Review `git status`.
- [x] Update this `docs/AI_HANDOFF.md` with:
  - what was actually completed
  - actual commands run
  - actual validation results
  - created/initialized master data
  - changed files
  - unresolved failures
  - blockers
  - recommended next action
- [x] Do not change `docs/ROADMAP.md` unless phase scope, dependency, milestone, or exit criteria actually changed.
- [x] Do not change `docs/DECISIONS.md` unless a durable architecture/security/workflow decision actually changed.
- [x] Do not modify Obsidian during this routine development task.
- [x] Do not start transaction-flow validation unless the current task has been completed and handed back for review.
- [x] Do not start Phase 1, Custom App, API, MCP, or Agent work.

#### Current Task Execution Record

Commands actually run included:

```bash
git pull --ff-only origin main
docker info
docker compose -f phase0/compose.yaml up -d
docker compose -f phase0/compose.yaml ps -a
./scripts/phase0-check.sh
python3 -m json.tool phase0/synthetic-data.json
python3 -m py_compile scripts/phase0-seed.py
python3 scripts/phase0-seed.py
```

Actual validation results:

- Runtime health check: passed, exit code `0`.
- Dataset validation: JSON parse passed; Python compilation passed.
- Final seed execution: passed, exit code `0`, with every expected entity reported as `EXISTS`.
- REST API readback: company `1`, warehouses `2`, suppliers `3`, customers `3`, items `20`, Item Prices `40`.
- Opening stock: `MAT-RECO-2026-00001`, `docstatus = 1`, purpose `Opening Stock`, item rows `18`.
- Multi-level UOM: `P0-CO-SCREW` returned Piece `1`, Box `50`, Carton `500`.

Changed files:

- `README.md`
- `phase0/synthetic-data.json`
- `scripts/phase0-seed.py`
- `docs/PHASE0_VALIDATION.md`
- `docs/AI_HANDOFF.md`

Failures preserved:

- Initial unprivileged Docker access was denied; authorized host access showed Docker Desktop was stopped. Docker Desktop was started, resolving the blocker.
- The first seed attempt stopped before opening stock because Stock Reconciliation `remarks` is not permitted in list filters.
- The second seed attempt stopped before opening stock because ERPNext requires an Asset/Liability difference account for Opening Stock.
- After submission, ERPNext did not retain the requested `remarks`; idempotency was corrected to match the complete submitted opening-stock content.

Previous recommended action was to begin `PUR-001` after review. The user accepted that handoff on 2026-09-05, and the purchase sequence has now been executed.

### P0 — Next After Current Task

These are the next Phase 0 activities, but they are not part of the current Codex task unless the handoff is explicitly updated after review.

- [x] Execute Purchase validation:
  - Purchase Order
  - full receipt
  - partial/multiple receipts
  - Purchase Invoice
  - Accounts Payable
  - supplier payment
  - alternate UOM
  - purchase return
- [x] Execute Stock validation:
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

#### Purchase Flow Execution Record — 2026-09-05

Commands actually run included:

```bash
git fetch --prune origin
./scripts/phase0-check.sh
python3 scripts/phase0-seed.py
python3 scripts/phase0-validate-purchase.py
```

Actual document evidence:

- Purchase Orders: `PUR-ORD-2026-00001`, `PUR-ORD-2026-00002`, `PUR-ORD-2026-00003`.
- Purchase Receipts: `MAT-PRE-2026-00001` through `MAT-PRE-2026-00004`.
- Purchase Return: `MAT-PRE-2026-00005`, linked to `MAT-PRE-2026-00004`.
- Purchase Invoices: `ACC-PINV-2026-00001` for CNY 152 and `ACC-PINV-2026-00002` for CNY 120.
- Payment Entries: `ACC-PAY-2026-00001` fully allocated CNY 152 and `ACC-PAY-2026-00002` partially allocated CNY 60.
- Final invoice balances: CNY 0 and CNY 60.
- Final main-warehouse stock: hammer 28, screwdriver 58, screw 650 Piece.
- GL evidence: invoice credits to `Creditors - PZH` of CNY 152 and 120; payment debits of CNY 152 and 60 with equal Cash credits.

Changed files for the purchase-validation task:

- `.gitignore`
- `README.md`
- `phase0/purchase-validation.json`
- `scripts/phase0_api.py`
- `scripts/phase0-seed.py`
- `scripts/phase0-validate-purchase.py`
- `docs/PHASE0_VALIDATION.md`
- `docs/AI_HANDOFF.md`

Failure preserved:

- The first return attempt used the non-whitelisted lower-level `erpnext.controllers.sales_and_purchase_return.make_return_doc` and received HTTP 403. The validated solution uses ERPNext's whitelisted `erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_return` wrapper.

#### Stock Flow Execution Record — 2026-09-05

Commands actually run included:

```bash
./scripts/phase0-check.sh
python3 scripts/phase0-validate-stock.py
python3 scripts/phase0-validate-stock.py
```

Actual document and balance evidence:

- Opening Stock: `MAT-RECO-2026-00001`, 18 document rows and 18 matching Stock Ledger Entry balances.
- Delivery Note: `MAT-DN-2026-00001`, reducing `P0-AC-BITSET` from 20 to 18 Piece.
- Material Transfer: `MAT-STE-2026-00001`, moving 3 `P0-AC-GOGGLES` from the main warehouse to the secondary warehouse; final balances 12 and 3.
- Stock Reconciliation: `MAT-RECO-2026-00002`, setting `P0-AC-TOOLBOX` from 6 to 5 Piece at CNY 95.
- Insufficient-stock evidence: ERPNext rejected submission of draft `MAT-DN-2026-00002` for zero-stock `P0-PT-SAW`; quantity remained zero.
- Final item queries matched the source-controlled expected balances exactly; warehouse query returned 18 non-zero main-warehouse items and 3 goggles in the secondary warehouse.
- A second complete run reused the same documents and reproduced the same balances without duplicate stock movements.

Changed files for the stock-validation task:

- `README.md`
- `phase0/stock-validation.json`
- `scripts/phase0-validate-stock.py`
- `docs/PHASE0_VALIDATION.md`
- `docs/AI_HANDOFF.md`

Failure preserved:

- The first opening-ledger assertion incorrectly compared Stock Reconciliation `actual_qty` with the opening quantity. ERPNext v16 returned `actual_qty = 0` on those opening rows and stored the resulting balance in `qty_after_transaction`; the validator was corrected to use the observed native ledger field and also verify the warehouse and valuation rate.

Recommended next action: review the stock evidence, then execute sales validation beginning with `SAL-001`. Preserve the CNY 60 open payable for AP-004/report testing.

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
- The runtime, representative master data, evidence ledger, and native purchase/stock-flow validation are complete.
- Review the stock evidence before beginning sales validation.
- Do not begin Custom App, API, MCP, Agent, or multi-Agent work.
- Preserve ERPNext Core.
- Treat `ERP与AI智能体设计笔记.md` as project direction, not proof that any component exists.
- Update this handoff in the same change as implementation or validation evidence.
