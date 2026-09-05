# Phase 0 Validation

## Purpose

This document is the evidence ledger for ERPNext v16 native-capability validation.

It must record what was actually tested, what was expected, what happened, and what evidence exists.

Do not mark a capability as supported merely because ERPNext appears to contain a related screen, DocType, menu item, or configuration option.

Unexecuted tests remain `Not Tested`.

## Public Repository Data Rule

This repository is intentionally public for the Web GPT → GitHub → Codex collaboration workflow.

Only synthetic or safely sanitized data may be recorded here.

Do not include:

- production secrets
- reusable credentials
- API tokens
- real customer records
- real supplier records
- real internal pricing
- confidential contracts
- personal information
- production financial data
- production database exports

## Result Vocabulary

Every validation case must use exactly one of the following result states.

### Supported

ERPNext natively supports the requirement with acceptable default behaviour.

### Configurable

ERPNext can support the requirement through normal configuration without custom code.

### Gap

Current execution evidence shows that the requirement cannot be acceptably satisfied through native functionality, normal configuration, or an acceptable process adjustment.

A `Gap` must be evidence-based.

### Not Tested

No valid execution evidence exists yet.

## Environment

| Field | Value |
|---|---|
| Latest runtime validation date | 2026-09-05 15:28:51 +0800 |
| ERPNext version | 16.33.0 |
| Frappe version | 16.31.0 |
| Compose file | `phase0/compose.yaml` |
| Site | `frontend` |
| Runtime status | Healthy; current health check passed |
| Last historical successful baseline | 2026-08-30 |
| Historical ERPNext version | 16.33.0 |
| Historical Frappe version | 16.31.0 |

## Current Runtime Validation

### ENV-001 — Phase 0 runtime health

- **Requirement:** The disposable ERPNext Phase 0 stack must start reproducibly and pass the existing health-check script.
- **Preconditions:** Docker daemon available.
- **Steps:**
  1. Run `docker compose -f phase0/compose.yaml up -d`.
  2. Wait for Site creation/readiness.
  3. Run `./scripts/phase0-check.sh`.
- **Expected Result:**
  - Compose validation passes.
  - `create-site` exits with code 0.
  - required services are running.
  - ERPNext is 16.x.
  - Frappe is 16.x.
  - HTTP ping returns `pong`.
- **Actual Result:** `docker compose up -d` completed; `create-site` was `exited` with exit code `0`; the nine required services (`backend`, `db`, `frontend`, `queue-long`, `queue-short`, `redis-cache`, `redis-queue`, `scheduler`, and `websocket`) were running; ERPNext reported `16.33.0`; Frappe reported `16.31.0`; ping returned `{"message":"pong"}`; `./scripts/phase0-check.sh` exited `0`. The same health-check script passed again before purchase-flow testing on 2026-09-05.
- **Evidence:** Commands run on 2026-09-01: `docker compose -f phase0/compose.yaml up -d`, `docker compose -f phase0/compose.yaml ps -a`, and `./scripts/phase0-check.sh`; latest `./scripts/phase0-check.sh` pass: 2026-09-05 15:28:51 +0800.
- **Result:** Supported
- **Notes:** Docker Desktop was initially stopped. After it was started, current runtime revalidation passed. Historical success was not used as a substitute for this check.

## Test Company Assumptions

Use a clearly synthetic hardware-trading company.

| Field | Value |
|---|---|
| Company name | Phase Zero Hardware Trading Demo |
| Abbreviation | PZH |
| Country | China |
| Default currency | CNY |
| Fiscal year | ERPNext default fiscal-year setup for the validation date; no custom fiscal-year rule added |
| Tax assumptions | Prices exclude tax; no production tax identifiers or rates are used in Phase 0 master data |

The source-controlled dataset is `phase0/synthetic-data.json`. It is applied through `scripts/phase0-seed.py`, which authenticates to the disposable site and uses ERPNext REST APIs rather than direct database access.

## Dataset Target

Minimum representative dataset:

- approximately 20 SKUs
- 3 suppliers
- 3 customers
- at least 2 warehouses
- multiple item groups/categories
- multiple UOMs
- meaningful UOM conversions
- synthetic purchase prices
- synthetic selling prices
- opening stock
- zero-stock and low-stock scenarios
- opening receivable/payable assumptions only when required for later tests

## Warehouse Inventory

| Warehouse | Purpose | Status |
|---|---|---|
| P0 Main Warehouse - PZH | Primary synthetic inventory and opening stock | Initialized |
| P0 Secondary Warehouse - PZH | Transfer and secondary-stock scenarios | Initialized |

## Supplier Inventory

| Supplier | Scenario | Status |
|---|---|---|
| P0 General Hardware Supply | Primary general supplier | Initialized |
| P0 Alternate Tool Supply | Alternate supplier and price comparison | Initialized |
| P0 Specialty Consumables Supply | Specialty consumables supplier | Initialized |

## Customer Inventory

| Customer | Scenario | Status |
|---|---|---|
| P0 Standard Retail Customer | Standard customer | Initialized |
| P0 Repeat Trade Customer | Repeat-order and pricing scenario | Initialized |
| P0 Credit Trade Customer | Receivable and partial-payment scenario | Initialized |

## Item Dataset

The final item set should intentionally cover different ERP behaviours.

Suggested coverage:

- hand tools
- power tools
- consumables
- accessories
- normally stocked items
- zero-stock items
- low-stock items
- packaged items
- UOM conversion items

At least one packaged item should support a scenario such as:

    1 Carton = N Boxes
    1 Box = M Pieces

| SKU | Item Name | Category | Stock UOM | Alternate UOM | Conversion | Opening Stock | Purchase Price | Selling Price | Scenario |
|---|---|---|---|---|---|---:|---:|---:|---|
| P0-HT-HAMMER | P0 Claw Hammer | P0 Hand Tools | Piece | — | — | 24 | 38.00 | 58.00 | Normally stocked hand tool |
| P0-HT-SCREWDRIVER | P0 Phillips Screwdriver | P0 Hand Tools | Piece | — | — | 48 | 12.00 | 20.00 | Normally stocked hand tool |
| P0-HT-PLIERS | P0 Combination Pliers | P0 Hand Tools | Piece | — | — | 18 | 26.00 | 42.00 | Low-stock hand tool |
| P0-HT-WRENCH | P0 Adjustable Wrench | P0 Hand Tools | Piece | — | — | 16 | 32.00 | 49.00 | Low-stock hand tool |
| P0-HT-TAPE | P0 Measuring Tape | P0 Hand Tools | Piece | — | — | 30 | 15.00 | 25.00 | Normally stocked hand tool |
| P0-PT-DRILL | P0 Cordless Drill | P0 Power Tools | Piece | — | — | 8 | 420.00 | 599.00 | Low-stock power tool |
| P0-PT-GRINDER | P0 Angle Grinder | P0 Power Tools | Piece | — | — | 5 | 310.00 | 459.00 | Low-stock power tool |
| P0-PT-SAW | P0 Circular Saw | P0 Power Tools | Piece | — | — | 0 | 530.00 | 749.00 | Zero-stock power tool |
| P0-PT-HEATGUN | P0 Heat Gun | P0 Power Tools | Piece | — | — | 3 | 185.00 | 279.00 | Very-low-stock power tool |
| P0-PT-DRIVER | P0 Electric Screwdriver | P0 Power Tools | Piece | — | — | 10 | 160.00 | 239.00 | Normally stocked power tool |
| P0-CO-SCREW | P0 M4 Screw | P0 Consumables | Piece | Box, Carton | 1 Box = 50 Piece; 1 Carton = 500 Piece | 600 | 0.35 | 0.65 | Multi-level packaged consumable |
| P0-CO-CABLETIE | P0 Cable Tie | P0 Consumables | Piece | Box | 1 Box = 100 Piece | 240 | 0.18 | 0.40 | Packaged consumable |
| P0-CO-GLOVE | P0 Work Glove Pair | P0 Consumables | Piece | — | — | 40 | 8.00 | 14.00 | Consumable safety item |
| P0-CO-SEALANT | P0 Multi-purpose Sealant | P0 Consumables | Piece | — | — | 12 | 16.00 | 28.00 | Low-stock consumable |
| P0-CO-DISC | P0 Grinding Disc | P0 Consumables | Piece | Box | 1 Box = 20 Piece | 100 | 4.00 | 7.00 | Box purchase and piece issue |
| P0-AC-BITSET | P0 Drill Bit Set | P0 Accessories | Piece | — | — | 20 | 45.00 | 72.00 | Power-tool accessory |
| P0-AC-GOGGLES | P0 Safety Goggles | P0 Accessories | Piece | — | — | 15 | 18.00 | 32.00 | Low-stock safety accessory |
| P0-AC-TOOLBOX | P0 Portable Toolbox | P0 Accessories | Piece | — | — | 6 | 95.00 | 148.00 | Low-stock accessory |
| P0-AC-EXTENSION | P0 Extension Cable | P0 Accessories | Piece | — | — | 9 | 68.00 | 105.00 | Low-stock electrical accessory |
| P0-AC-BLADE | P0 Replacement Saw Blade | P0 Accessories | Piece | — | — | 0 | 55.00 | 88.00 | Zero-stock accessory |

## Dataset Initialization Evidence

- The REST API returned one matching company, two matching warehouses, three matching suppliers, three matching customers, 20 matching items, and 40 matching Item Price records.
- Submitted Stock Reconciliation `MAT-RECO-2026-00001` has purpose `Opening Stock`, `docstatus = 1`, and 18 item rows. The other two items intentionally start at zero stock.
- REST readback for `P0-CO-SCREW` returned UOM conversions `Piece:1`, `Box:50`, and `Carton:500`.
- A final rerun of `python3 scripts/phase0-seed.py` exited `0`, reported all entities and the submitted opening-stock document as `EXISTS`, and created no duplicate opening-stock document.
- Master-data initialization is not treated as proof of purchase, stock-movement, sales, returns, receivable/payable, permissions, approval, or reporting behaviour. Those cases remain `Not Tested`.

### Failed Initialization Attempts Preserved

1. The first run created the company and master data but stopped before opening stock because ERPNext does not permit list filtering on Stock Reconciliation `remarks`.
2. The second run proved that company/master-data creation was idempotent, then stopped because Opening Stock requires an Asset/Liability difference account.
3. The script was corrected to inspect candidate documents individually and to use the generated Asset account `Temporary Opening - PZH`. The next run submitted `MAT-RECO-2026-00001` successfully.
4. ERPNext does not retain the submitted Stock Reconciliation `remarks` value. Final idempotency therefore matches the submitted document by company, purpose, status, and the complete item/warehouse/quantity set.

## Evidence Requirements

For every executed validation case:

- record prerequisites
- record reproducible execution steps
- record expected behaviour before assigning the result
- record actual behaviour
- record relevant document IDs where available
- include command output, screenshots, logs, or other reproducible evidence where appropriate
- preserve failed results
- preserve blocked results
- do not infer success from configuration alone

## Validation Case Template

### TEST-ID — Test Name

- **Area:** Purchase / Stock / Sales / Returns / Accounts Receivable / Accounts Payable / Permissions / Approval / Reporting
- **Requirement:**
- **Preconditions:**
- **Steps:**
  1.
  2.
  3.
- **Expected Result:**
- **Actual Result:**
- **Evidence:**
- **Result:** Not Tested
- **Notes:**

## Purchase Validation

| Test ID | Requirement | Result |
|---|---|---|
| PUR-001 | Create and submit a Purchase Order | Supported |
| PUR-002 | Receive the full ordered quantity | Supported |
| PUR-003 | Receive one Purchase Order through multiple partial receipts | Supported |
| PUR-004 | Purchase an item using an alternate UOM with conversion | Supported |
| PUR-005 | Purchase Receipt correctly updates stock | Supported |
| PUR-006 | Create Purchase Invoice against the purchase flow | Supported |
| PUR-007 | Purchase Invoice creates Accounts Payable | Supported |
| PUR-008 | Record full supplier payment | Supported |
| PUR-009 | Record partial supplier payment | Supported |
| PUR-010 | Return purchased goods to supplier | Supported |

### Purchase Execution — 2026-09-05

The source-controlled scenarios are in `phase0/purchase-validation.json`; `scripts/phase0-validate-purchase.py` executes them only through authenticated ERPNext REST resources and whitelisted document-mapping methods.

#### PUR-001 — Create and submit Purchase Orders

- **Requirement:** Create and submit native Purchase Orders for representative synthetic suppliers and items.
- **Preconditions:** ENV-001 passed; P0 company, suppliers, items, prices, UOMs, and warehouse existed.
- **Steps:** Create one order for 4 hammers, one for 10 screwdrivers, and one for 2 boxes of screws; submit each order; read each back through REST.
- **Expected Result:** Each order has `docstatus = 1`, retains its supplier/item/quantity/UOM, and is available for receiving.
- **Actual Result:** `PUR-ORD-2026-00001`, `PUR-ORD-2026-00002`, and `PUR-ORD-2026-00003` were submitted. REST readback returned the expected suppliers, quantities, UOMs, and totals CNY 152, 120, and 35.
- **Evidence:** The three Purchase Order IDs above; final script output `OK: Phase 0 purchase-flow validation passed`.
- **Result:** Supported
- **Notes:** No custom DocType, field, or ERPNext Core change was used.

#### PUR-002 — Full receipt

- **Requirement:** Receive a complete Purchase Order in one receipt.
- **Preconditions:** `PUR-ORD-2026-00001` submitted for 4 hammers.
- **Steps:** Map the order to a Purchase Receipt, submit it, and read back the order and receipt.
- **Expected Result:** The receipt records 4 pieces and the order reaches 100% received.
- **Actual Result:** `MAT-PRE-2026-00001` was submitted with quantity/stock quantity 4; the order reported `per_received = 100` and status `Completed` after billing.
- **Evidence:** `PUR-ORD-2026-00001`; `MAT-PRE-2026-00001`.
- **Result:** Supported
- **Notes:** This scenario was subsequently invoiced and fully paid.

#### PUR-003 — Multiple partial receipts

- **Requirement:** Receive one Purchase Order through multiple partial receipts.
- **Preconditions:** `PUR-ORD-2026-00002` submitted for 10 screwdrivers.
- **Steps:** Submit one receipt for 4 pieces; map the remaining order quantity; submit a second receipt for 6 pieces; read back the order.
- **Expected Result:** Both receipts link to the same order and the cumulative received quantity becomes 10/10.
- **Actual Result:** `MAT-PRE-2026-00002` recorded 4 and `MAT-PRE-2026-00003` recorded 6; both link to `PUR-ORD-2026-00002`; the order reported `per_received = 100`.
- **Evidence:** `PUR-ORD-2026-00002`; `MAT-PRE-2026-00002`; `MAT-PRE-2026-00003`.
- **Result:** Supported
- **Notes:** The order was invoiced for the full 10 pieces after both receipts.

#### PUR-004 — Alternate UOM purchase

- **Requirement:** Purchase a stock item in Box while maintaining stock in Piece.
- **Preconditions:** `P0-CO-SCREW` had stock UOM Piece and conversion `1 Box = 50 Piece`.
- **Steps:** Submit an order for 2 Box at CNY 17.50 per Box; map and submit the receipt; read back UOM, conversion, and stock quantity.
- **Expected Result:** ERPNext records 2 Box as 100 Piece of stock quantity.
- **Actual Result:** `PUR-ORD-2026-00003` and `MAT-PRE-2026-00004` retained UOM Box, conversion factor 50, order/receipt quantity 2, and stock quantity 100.
- **Evidence:** `PUR-ORD-2026-00003`; `MAT-PRE-2026-00004`.
- **Result:** Supported
- **Notes:** One Box was later returned in PUR-010.

#### PUR-005 — Receipt updates stock

- **Requirement:** Submitted Purchase Receipts increase native stock balances by their stock quantities.
- **Preconditions:** Opening balances were hammer 24, screwdriver 48, and screw 600 Piece.
- **Steps:** Submit the receipts in PUR-002 through PUR-004; query Bin balances; submit the later screw return and query again.
- **Expected Result:** Hammers increase by 4 to 28; screwdrivers increase by 10 to 58; screws increase by 100 to 700 before the return and become 650 after returning 50.
- **Actual Result:** Final REST Bin readback returned hammer 28, screwdriver 58, and screw 650; the alternate-UOM receipt recorded `stock_qty = 100` and return recorded `stock_qty = -50`.
- **Evidence:** `MAT-PRE-2026-00001` through `MAT-PRE-2026-00005`; Bin REST readback.
- **Result:** Supported
- **Notes:** The receipt and return deltas reconcile exactly to the initialized balances.

#### PUR-006 — Purchase Invoices

- **Requirement:** Create and submit Purchase Invoices against the validated purchase flow.
- **Preconditions:** Full-receipt and full-partial-receipt scenarios were submitted.
- **Steps:** Map `MAT-PRE-2026-00001` to an invoice; map `PUR-ORD-2026-00002` to a second invoice; add synthetic supplier bill numbers; submit and read back.
- **Expected Result:** Both invoices submit and retain links to their source purchase documents.
- **Actual Result:** `ACC-PINV-2026-00001` submitted for CNY 152 and links to the full receipt/order; `ACC-PINV-2026-00002` submitted for CNY 120 and links to the partially received order.
- **Evidence:** Supplier bill references `P0-PUR-FULL-001` and `P0-PUR-PARTIAL-001`; the two Purchase Invoice IDs above.
- **Result:** Supported
- **Notes:** Both use native mapping and standard accounts.

#### PUR-007 — Accounts Payable creation

- **Requirement:** A submitted Purchase Invoice creates a supplier payable.
- **Preconditions:** PUR-006 invoices submitted.
- **Steps:** Read invoice balances and GL Entries for both invoice vouchers.
- **Expected Result:** Creditors is credited for each invoice and the supplier is attached to the payable entry.
- **Actual Result:** `ACC-PINV-2026-00001` credited `Creditors - PZH` CNY 152 for `P0 General Hardware Supply`; `ACC-PINV-2026-00002` credited it CNY 120 for `P0 Alternate Tool Supply`. Corresponding debits posted to `Stock Received But Not Billed - PZH`.
- **Evidence:** GL Entries keyed by the two Purchase Invoice voucher numbers.
- **Result:** Supported
- **Notes:** Payment effects are separated into PUR-008 and PUR-009.

#### PUR-008 — Full supplier payment

- **Requirement:** Record a full supplier payment and clear the invoice outstanding balance.
- **Preconditions:** `ACC-PINV-2026-00001` submitted for CNY 152.
- **Steps:** Map a Payment Entry against the invoice using `Cash - PZH`; allocate CNY 152; submit; read invoice and GL Entries.
- **Expected Result:** Payment debits Creditors and credits Cash for 152; invoice outstanding becomes zero.
- **Actual Result:** `ACC-PAY-2026-00001` was submitted for CNY 152; GL debited `Creditors - PZH` and credited `Cash - PZH` by 152; the invoice status became `Paid` with outstanding 0.
- **Evidence:** `ACC-PAY-2026-00001`; `ACC-PINV-2026-00001`; their GL Entries.
- **Result:** Supported
- **Notes:** This uses synthetic cash and supplier data only.

#### PUR-009 — Partial supplier payment

- **Requirement:** Record a partial supplier payment and preserve the remaining payable.
- **Preconditions:** `ACC-PINV-2026-00002` submitted for CNY 120.
- **Steps:** Map a Payment Entry for CNY 60; submit; read invoice and GL Entries.
- **Expected Result:** Payment reduces the payable by 60 and leaves 60 outstanding.
- **Actual Result:** `ACC-PAY-2026-00002` was submitted for CNY 60; GL debited `Creditors - PZH` by 60 and credited `Cash - PZH` by 60; the invoice status became `Partly Paid` with outstanding CNY 60.
- **Evidence:** `ACC-PAY-2026-00002`; `ACC-PINV-2026-00002`; their GL Entries.
- **Result:** Supported
- **Notes:** The remaining CNY 60 is intentionally left open for later payable-report testing.

#### PUR-010 — Purchase return

- **Requirement:** Return part of a received alternate-UOM purchase to the supplier.
- **Preconditions:** `MAT-PRE-2026-00004` submitted for 2 Box / 100 Piece of screws.
- **Steps:** Use ERPNext's whitelisted Purchase Receipt return mapper; set return quantity to 1 Box; submit; read the return, order, and Bin balance.
- **Expected Result:** Return links to the original receipt, records negative 1 Box / 50 Piece, reduces stock by 50, and reopens the unreturned order quantity.
- **Actual Result:** `MAT-PRE-2026-00005` submitted with `is_return = 1`, `return_against = MAT-PRE-2026-00004`, quantity -1 Box, conversion 50, and stock quantity -50; screw stock became 650 and the order reported 50% received with status `To Receive and Bill`.
- **Evidence:** `MAT-PRE-2026-00004`; `MAT-PRE-2026-00005`; `PUR-ORD-2026-00003`; Bin REST readback.
- **Result:** Supported
- **Notes:** An initial attempt to call the non-whitelisted lower-level return mapper failed with HTTP 403; switching to ERPNext's whitelisted `make_purchase_return` wrapper succeeded.

## Stock Validation

| Test ID | Requirement | Result |
|---|---|---|
| STK-001 | Opening stock is correctly recorded | Supported |
| STK-002 | Purchase Receipt increases available stock | Supported |
| STK-003 | Delivery decreases available stock | Supported |
| STK-004 | Transfer stock between warehouses | Supported |
| STK-005 | Perform stock reconciliation / inventory adjustment | Supported |
| STK-006 | Validate zero-stock item behaviour | Supported |
| STK-007 | Validate insufficient-stock behaviour | Supported |
| STK-008 | Validate alternate-UOM conversion impact on stock quantity | Supported |
| STK-009 | Query stock balance by item | Supported |
| STK-010 | Query stock balance by warehouse | Supported |

The source-controlled scenarios are in `phase0/stock-validation.json`; `scripts/phase0-validate-stock.py` executes and reads them only through authenticated ERPNext REST resources.

### Stock Execution Evidence

#### STK-001 — Opening stock

- **Requirement:** Submitted opening stock must match the source-controlled synthetic dataset and be visible in the stock ledger.
- **Preconditions:** `scripts/phase0-seed.py` has submitted the opening-stock reconciliation.
- **Steps:** Read `MAT-RECO-2026-00001`, compare all non-zero item rows with the dataset, then read its non-cancelled Stock Ledger Entries.
- **Expected Result:** The document and ledger contain the same 18 item balances, valuation rates, and main warehouse as the dataset.
- **Actual Result:** The submitted document contained 18 matching rows; 18 ledger rows reported the expected balances in `qty_after_transaction` and the expected valuation rates for `P0 Main Warehouse - PZH`.
- **Evidence:** `MAT-RECO-2026-00001`; Stock Reconciliation and Stock Ledger Entry REST readback; final script output `OK: Phase 0 remaining stock validation passed`.
- **Result:** Supported
- **Notes:** On ERPNext v16, opening Stock Reconciliation ledger rows can report `actual_qty = 0`; the resulting opening balance is represented by `qty_after_transaction`. The validator follows this observed native ledger semantic.

#### STK-002 — Purchase Receipt increases available stock

- **Requirement:** Submitted receipts increase stock by their stock quantities.
- **Preconditions:** Opening stock was initialized and PUR-002/PUR-003 receipts were ready to submit.
- **Steps:** Submit the full and partial receipts; read the linked receipt quantities and final Bin balances.
- **Expected Result:** Hammer increases 24→28 and screwdriver increases 48→58.
- **Actual Result:** Receipt stock quantities were +4 hammer and +4/+6 screwdriver; final Bin balances were 28 and 58.
- **Evidence:** `MAT-PRE-2026-00001`, `MAT-PRE-2026-00002`, `MAT-PRE-2026-00003`; Bin REST readback.
- **Result:** Supported
- **Notes:** Delivery-related stock decrease is covered separately by STK-003.

#### STK-008 — Alternate-UOM stock conversion

- **Requirement:** Alternate purchase UOM converts to the correct stock quantity.
- **Preconditions:** `P0-CO-SCREW` conversion was 1 Box = 50 Piece.
- **Steps:** Receive 2 Box and return 1 Box; read receipt/return stock quantities and final Bin balance.
- **Expected Result:** Receipt adds 100 Piece and return subtracts 50 Piece.
- **Actual Result:** ERPNext recorded `stock_qty = 100` and `stock_qty = -50`; balance moved from initialized 600 to final 650.
- **Evidence:** `MAT-PRE-2026-00004`, `MAT-PRE-2026-00005`; Bin REST readback.
- **Result:** Supported
- **Notes:** This evidence covers purchase-side UOM conversion only.

#### STK-003 — Delivery decreases stock

- **Requirement:** A submitted Delivery Note must decrease available stock by its stock quantity.
- **Preconditions:** `P0-AC-BITSET` had 20 Piece in the main warehouse.
- **Steps:** Create and submit a standalone Delivery Note for 2 Piece, then query the item/warehouse Bin.
- **Expected Result:** Main-warehouse stock decreases from 20 to 18.
- **Actual Result:** `MAT-DN-2026-00001` submitted and the Bin balance became 18.
- **Evidence:** `MAT-DN-2026-00001`; Bin REST readback.
- **Result:** Supported
- **Notes:** The standalone delivery isolates the stock effect; order-to-delivery mapping remains part of sales validation.

#### STK-004 — Warehouse transfer

- **Requirement:** A native Material Transfer must move stock between warehouses without changing the combined quantity.
- **Preconditions:** `P0-AC-GOGGLES` had 15 Piece in the main warehouse and zero in the secondary warehouse.
- **Steps:** Submit a Material Transfer for 3 Piece from the main warehouse to the secondary warehouse; query both Bins.
- **Expected Result:** Main becomes 12, secondary becomes 3, and combined stock remains 15.
- **Actual Result:** `MAT-STE-2026-00001` submitted; REST readback returned 12 and 3 respectively.
- **Evidence:** `MAT-STE-2026-00001`; main and secondary warehouse Bin readback.
- **Result:** Supported
- **Notes:** No customization or direct database access was used.

#### STK-005 — Inventory adjustment

- **Requirement:** Stock Reconciliation must set the counted quantity and valuation rate.
- **Preconditions:** `P0-AC-TOOLBOX` had 6 Piece in the main warehouse.
- **Steps:** Submit a reconciliation targeting 5 Piece at CNY 95, then query the Bin.
- **Expected Result:** Available quantity becomes 5 at the specified reconciliation valuation.
- **Actual Result:** `MAT-RECO-2026-00002` submitted and the Bin quantity became 5.
- **Evidence:** `MAT-RECO-2026-00002`; Bin REST readback.
- **Result:** Supported
- **Notes:** The standard `Stock Adjustment - PZH` account was used.

#### STK-006 / STK-007 — Zero and insufficient stock

- **Requirement:** A zero-stock item must be queryable as zero and ERPNext must reject an issue that would make stock negative.
- **Preconditions:** `P0-PT-SAW` had zero stock in the main warehouse.
- **Steps:** Query its Bin; create a draft Delivery Note for 1 Piece; attempt submission; read the draft and stock again.
- **Expected Result:** The queried quantity remains zero and submission is rejected without a stock movement.
- **Actual Result:** The initial and final quantity were both zero; ERPNext rejected submission of draft `MAT-DN-2026-00002` with its native negative-stock validation, leaving the document unsubmitted.
- **Evidence:** `MAT-DN-2026-00002`; API error response; Bin REST readback.
- **Result:** Supported
- **Notes:** The rejected draft is retained as reproducible evidence and is reused on idempotent reruns.

#### STK-009 / STK-010 — Item and warehouse balance queries

- **Requirement:** Current stock must be queryable both for a specific item/warehouse pair and as warehouse-level balances.
- **Preconditions:** Delivery, transfer, reconciliation, and rejection tests completed.
- **Steps:** Query individual `Bin` records for all tracked item/warehouse pairs; list all non-zero Bins for both P0 warehouses.
- **Expected Result:** Bit set main 18; goggles main 12 and secondary 3; toolbox main 5; saw main 0; warehouse-level results agree.
- **Actual Result:** All expected item balances matched exactly; the secondary warehouse contained goggles quantity 3 and the main warehouse returned 18 non-zero items.
- **Evidence:** Bin REST readback captured in the validator's `EVIDENCE` output.
- **Result:** Supported
- **Notes:** A second complete run reused all four documents and returned identical balances, proving validation-script idempotency.

## Sales Validation

| Test ID | Requirement | Result |
|---|---|---|
| SAL-001 | Create Quotation | Not Tested |
| SAL-002 | Create and submit Sales Order | Not Tested |
| SAL-003 | Deliver full Sales Order quantity | Not Tested |
| SAL-004 | Deliver one Sales Order through multiple partial deliveries | Not Tested |
| SAL-005 | Sell an item using an alternate UOM with conversion | Not Tested |
| SAL-006 | Delivery correctly reduces stock | Not Tested |
| SAL-007 | Create Sales Invoice | Not Tested |
| SAL-008 | Sales Invoice creates Accounts Receivable | Not Tested |
| SAL-009 | Record full customer payment | Not Tested |
| SAL-010 | Record partial customer payment | Not Tested |

## Returns Validation

| Test ID | Requirement | Result |
|---|---|---|
| RET-001 | Customer returns previously sold goods | Not Tested |
| RET-002 | Supplier receives returned purchased goods | Supported |
| RET-003 | Sales return reverses stock effects correctly | Not Tested |
| RET-004 | Purchase return reverses stock effects correctly | Supported |
| RET-005 | Return-related accounting effects are traceable | Not Tested |

### Return Evidence from Purchase Execution

#### RET-002 — Return purchased goods to supplier

- **Requirement:** A submitted receipt can be partially returned to its supplier.
- **Preconditions:** `MAT-PRE-2026-00004` had received 2 Box.
- **Steps:** Map a native purchase return for 1 Box and submit it.
- **Expected Result:** A submitted return links to the original receipt and supplier.
- **Actual Result:** `MAT-PRE-2026-00005` submitted with status `Return`, `is_return = 1`, and `return_against = MAT-PRE-2026-00004`.
- **Evidence:** The original and return Purchase Receipt IDs.
- **Result:** Supported
- **Notes:** Supplier credit-note/accounting reversal was not included in this case.

#### RET-004 — Purchase return reverses stock

- **Requirement:** Purchase return reverses the corresponding received stock quantity.
- **Preconditions:** Original receipt added 100 Piece via 2 Box.
- **Steps:** Return 1 Box and query the return row and Bin balance.
- **Expected Result:** Stock decreases by 50 Piece.
- **Actual Result:** The return row recorded -1 Box, conversion 50, and stock quantity -50; final screw balance was 650.
- **Evidence:** `MAT-PRE-2026-00005`; Bin REST readback.
- **Result:** Supported
- **Notes:** Return-accounting traceability remains `Not Tested`.

## Accounts Receivable Validation

| Test ID | Requirement | Result |
|---|---|---|
| AR-001 | Sales Invoice creates customer receivable | Not Tested |
| AR-002 | Full payment clears customer outstanding balance | Not Tested |
| AR-003 | Partial payment reduces outstanding balance correctly | Not Tested |
| AR-004 | Outstanding receivables can be reported | Not Tested |
| AR-005 | Receivable history is traceable to source documents | Not Tested |

## Accounts Payable Validation

| Test ID | Requirement | Result |
|---|---|---|
| AP-001 | Purchase Invoice creates supplier payable | Supported |
| AP-002 | Full payment clears supplier outstanding balance | Supported |
| AP-003 | Partial payment reduces outstanding balance correctly | Supported |
| AP-004 | Outstanding payables can be reported | Not Tested |
| AP-005 | Payable history is traceable to source documents | Supported |

### Accounts Payable Evidence from Purchase Execution

#### AP-001 — Invoice creates supplier payable

- **Requirement:** Submitted Purchase Invoice posts a supplier payable.
- **Preconditions:** Two native Purchase Invoices were submitted.
- **Steps:** Read the invoice GL Entries and supplier parties.
- **Expected Result:** Creditors is credited for each invoice with the correct supplier.
- **Actual Result:** GL credited `Creditors - PZH` by CNY 152 and CNY 120 for the two P0 suppliers.
- **Evidence:** GL Entries for `ACC-PINV-2026-00001` and `ACC-PINV-2026-00002`.
- **Result:** Supported
- **Notes:** Both invoices debit `Stock Received But Not Billed - PZH` for the matching amount.

#### AP-002 — Full payment clears payable

- **Requirement:** Full payment clears invoice outstanding.
- **Preconditions:** Invoice total CNY 152 was outstanding.
- **Steps:** Submit payment for 152; read payment GL and invoice outstanding.
- **Expected Result:** Creditors is debited 152 and invoice outstanding becomes zero.
- **Actual Result:** `ACC-PAY-2026-00001` debited Creditors 152; invoice status became `Paid`, outstanding 0.
- **Evidence:** `ACC-PAY-2026-00001`; `ACC-PINV-2026-00001`; GL Entries.
- **Result:** Supported
- **Notes:** Cash was credited by the same amount.

#### AP-003 — Partial payment reduces payable

- **Requirement:** Partial payment reduces but does not clear invoice outstanding.
- **Preconditions:** Invoice total CNY 120 was outstanding.
- **Steps:** Submit payment for 60; read payment GL and invoice outstanding.
- **Expected Result:** Outstanding becomes CNY 60.
- **Actual Result:** `ACC-PAY-2026-00002` debited Creditors 60; invoice status became `Partly Paid`, outstanding 60.
- **Evidence:** `ACC-PAY-2026-00002`; `ACC-PINV-2026-00002`; GL Entries.
- **Result:** Supported
- **Notes:** The remaining balance is retained for later report validation.

#### AP-005 — Payable traceability

- **Requirement:** Payable and payment entries trace back to source invoices and suppliers.
- **Preconditions:** AP-001 through AP-003 completed.
- **Steps:** Read Purchase Invoice and Payment Entry references plus GL `voucher_no` and `against_voucher` fields.
- **Expected Result:** Each payment allocation and GL entry identifies its invoice and supplier.
- **Actual Result:** Both Payment Entries reference their Purchase Invoice with exact allocated amounts; Creditors GL rows identify the supplier and `against_voucher` invoice.
- **Evidence:** `ACC-PINV-2026-00001`, `ACC-PINV-2026-00002`, `ACC-PAY-2026-00001`, `ACC-PAY-2026-00002` and their GL Entries.
- **Result:** Supported
- **Notes:** The dedicated Accounts Payable report itself remains `Not Tested` under AP-004.

## Permissions Validation

| Test ID | Requirement | Result |
|---|---|---|
| PER-001 | Purchasing user can access required purchase functions | Not Tested |
| PER-002 | Purchasing user cannot access unrelated restricted functions | Not Tested |
| PER-003 | Sales user can access required sales functions | Not Tested |
| PER-004 | Sales user cannot access unrelated restricted functions | Not Tested |
| PER-005 | Finance-related access can be separated where required | Not Tested |
| PER-006 | Important actions are attributable to a user | Not Tested |

## Approval Validation

| Test ID | Requirement | Result |
|---|---|---|
| APR-001 | Determine native workflow/approval support for Purchase Orders | Not Tested |
| APR-002 | Determine native workflow/approval support for Sales Orders | Not Tested |
| APR-003 | Determine native workflow/approval support for consequential financial documents | Not Tested |
| APR-004 | Approval history is visible and auditable | Not Tested |

## Reporting Validation

| Test ID | Requirement | Result |
|---|---|---|
| REP-001 | Report current stock by item | Not Tested |
| REP-002 | Report current stock by warehouse | Not Tested |
| REP-003 | Report purchase history by supplier | Not Tested |
| REP-004 | Report purchase history by item | Not Tested |
| REP-005 | Report sales history by customer | Not Tested |
| REP-006 | Report sales history by item | Not Tested |
| REP-007 | Report outstanding Accounts Receivable | Not Tested |
| REP-008 | Report outstanding Accounts Payable | Not Tested |

## Gap Log

Only add entries after an executed test produces supporting evidence.

| Gap ID | Test ID | Requirement | Business Impact | Native Workaround / Configuration | Proposed Classification | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | No confirmed gaps yet |

Allowed proposed classifications after review:

- configuration
- process adjustment
- integration
- customization
- unresolved

## Phase 0 Summary

Not yet available.

Complete this section only after the critical native workflows have been executed, evidence has been reviewed, and confirmed gaps have been classified.
