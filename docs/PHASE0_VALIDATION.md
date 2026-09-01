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
| Validation date | Not yet recorded |
| ERPNext version | Not yet revalidated |
| Frappe version | Not yet revalidated |
| Compose file | `phase0/compose.yaml` |
| Site | `frontend` |
| Runtime status | Not yet revalidated |
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
- **Actual Result:** Not yet recorded.
- **Evidence:** Not yet recorded.
- **Result:** Not Tested
- **Notes:** Historical success on 2026-08-30 does not replace current revalidation.

## Test Company Assumptions

Use a clearly synthetic hardware-trading company.

| Field | Value |
|---|---|
| Company name | Not yet initialized |
| Abbreviation | Not yet recorded |
| Country | Not yet recorded |
| Default currency | Not yet recorded |
| Fiscal year | Not yet recorded |
| Tax assumptions | Not yet recorded |

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
| TBD | Main inventory | Not initialized |
| TBD | Secondary inventory / transfer scenario | Not initialized |

## Supplier Inventory

| Supplier | Scenario | Status |
|---|---|---|
| TBD | Primary/general supplier | Not initialized |
| TBD | Alternate supplier | Not initialized |
| TBD | Specialty supplier | Not initialized |

## Customer Inventory

| Customer | Scenario | Status |
|---|---|---|
| TBD | Standard customer | Not initialized |
| TBD | Repeat / pricing scenario customer | Not initialized |
| TBD | Credit / receivable scenario customer | Not initialized |

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

Populate this table after initialization.

| SKU | Item Name | Category | Stock UOM | Alternate UOM | Conversion | Opening Stock | Purchase Price | Selling Price | Scenario |
|---|---|---|---|---|---|---:|---:|---:|---|
| TBD | TBD | TBD | TBD | TBD | TBD | 0 | TBD | TBD | TBD |

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
| PUR-001 | Create and submit a Purchase Order | Not Tested |
| PUR-002 | Receive the full ordered quantity | Not Tested |
| PUR-003 | Receive one Purchase Order through multiple partial receipts | Not Tested |
| PUR-004 | Purchase an item using an alternate UOM with conversion | Not Tested |
| PUR-005 | Purchase Receipt correctly updates stock | Not Tested |
| PUR-006 | Create Purchase Invoice against the purchase flow | Not Tested |
| PUR-007 | Purchase Invoice creates Accounts Payable | Not Tested |
| PUR-008 | Record full supplier payment | Not Tested |
| PUR-009 | Record partial supplier payment | Not Tested |
| PUR-010 | Return purchased goods to supplier | Not Tested |

## Stock Validation

| Test ID | Requirement | Result |
|---|---|---|
| STK-001 | Opening stock is correctly recorded | Not Tested |
| STK-002 | Purchase Receipt increases available stock | Not Tested |
| STK-003 | Delivery decreases available stock | Not Tested |
| STK-004 | Transfer stock between warehouses | Not Tested |
| STK-005 | Perform stock reconciliation / inventory adjustment | Not Tested |
| STK-006 | Validate zero-stock item behaviour | Not Tested |
| STK-007 | Validate insufficient-stock behaviour | Not Tested |
| STK-008 | Validate alternate-UOM conversion impact on stock quantity | Not Tested |
| STK-009 | Query stock balance by item | Not Tested |
| STK-010 | Query stock balance by warehouse | Not Tested |

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
| RET-002 | Supplier receives returned purchased goods | Not Tested |
| RET-003 | Sales return reverses stock effects correctly | Not Tested |
| RET-004 | Purchase return reverses stock effects correctly | Not Tested |
| RET-005 | Return-related accounting effects are traceable | Not Tested |

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
| AP-001 | Purchase Invoice creates supplier payable | Not Tested |
| AP-002 | Full payment clears supplier outstanding balance | Not Tested |
| AP-003 | Partial payment reduces outstanding balance correctly | Not Tested |
| AP-004 | Outstanding payables can be reported | Not Tested |
| AP-005 | Payable history is traceable to source documents | Not Tested |

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
