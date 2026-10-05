# Phase 0 Gap Analysis

## Purpose and evidence boundary

This document converts executed Phase 0 evidence into first-release implementation decisions. It does not infer requirements from ERPNext menus or from product preferences.

Evidence sources:

- `docs/PHASE0_VALIDATION.md`
- source-controlled JSON scenarios under `phase0/`
- validators under `scripts/`
- rendered print-preview evidence under `output/playwright/`

Current evidence covers the disposable synthetic company and the tested purchase, stock, sales, return, AR/AP, permission, approval, audit, reporting, and print-preview flows. Real production data, organization design, tax requirements, external integrations, and production topology are not inferred from synthetic tests.

## Executive conclusion

Evidence reviewed and reporting regression revalidated on 2026-10-06. Two final complete validator runs exited `0` with identical output, including purchase-return account/link assertions and four HTML preview hashes. This is local synthetic runtime evidence, not independent CI, production UAT, or owner approval of first-release scope.

ERPNext v16 natively supports the tested core hardware-trading workflows. The current evidence does not justify modifying ERPNext Core or creating a `hardware_erp` Custom App.

The first-release gaps found so far are configuration, data-governance, operational, or process issues. P0.8 must decide which bilingual output is release-blocking and freeze the production role/approval matrix. P0.9 must implement the accepted configuration and SOP work. P0.12 must revalidate native PDF output in the production-like topology.

## Confirmed items

| ID | Evidence | Issue / requirement | Business impact | Classification | Native workaround or implementation path | Recommended owner | Phase 0 disposition |
|---|---|---|---|---|---|---|---|
| CFG-001 | LANG-001, LANG-002 | Site language and per-user language are not automatic business rules; they require System Settings and User configuration | Users can receive the wrong interface language if defaults and overrides are not governed | native configuration | Set the approved site default and only approved per-user overrides through reproducible configuration | ERP administrator / business owner | P0.8 freeze language policy; P0.9 implement and acceptance-test it |
| CFG-002 | APR-001 through APR-004, PER-001 through PER-006 | Approval separation requires explicit Workflow and a role combination that grants both document access and manager transitions | Incorrect role design can block approval or permit excessive access | native configuration | Approve the organization role matrix, workflow states, thresholds, creator/approver separation, and least-privilege User Permissions | Business process owners + ERP administrator | Must be frozen in P0.8 and completed in P0.9 |
| CFG-003 | LANG-003, rendered Chinese previews | Standard Chinese print previews remain partly English; saved synthetic descriptions, UOM labels, workflow state, and amount in words are not automatically translated | Customer/supplier documents may be inconsistent or unsuitable for formal use | native configuration and governed data | Approve bilingual master-data policy and, only if required, a controlled versioned Print Format using standard ERPNext customization | Sales/purchase owners + ERP administrator | P0.8 decides Must/Should; implement in P0.9 if included |
| CFG-004 | LANG-003 `Get PDF` execution | `wkhtmltopdf` in the disposable Compose topology cannot reach print resources and returns `ConnectionRefusedError` | Users cannot download formal PDFs from the current topology | deployment/environment configuration | Correct site URL, host resolution, and container networking in the production-like environment; execute PDF text and rendered-page verification | Deployment owner | Release-blocking for P0.12 if downloadable PDFs are in scope; no product custom code justified |
| PROC-001 | SAL-003/RET-001/RET-003 observed state | A fully delivered and then fully returned Sales Order is shown as net `per_delivered = 0`, status `To Deliver` | Operators may mistake a returned order for an order that was never delivered | acceptable process adjustment | SOP and operational reporting must distinguish historical Delivery Notes/returns from the order's net state | Sales operations owner | Document and test the SOP in P0.9 |
| OPS-001 | ENV-001 recovery evidence | After Docker restart, the disposable frontend retained a stale backend address until the frontend container was restarted | A similar topology could produce temporary HTTP 502 responses during restart | deployment design / process | Do not promote the disposable Compose topology; production-like health checks, service discovery, restart ordering, and recovery runbooks are required | Deployment owner | Address and rehearse in P0.12 |

## Executed limitations that are not release gaps

These failures were resolved within native boundaries and do not justify customization:

- Stock Reconciliation cannot be reliably rediscovered by filtering on submitted `remarks`; the seed uses company, purpose, status, and the complete item/warehouse/quantity signature.
- Opening Stock requires an appropriate Asset/Liability difference account; `Temporary Opening - PZH` satisfied the synthetic case.
- The lower-level purchase-return method was not whitelisted; the native whitelisted `make_purchase_return` wrapper succeeded.
- REST list filtering is field-permission aware; the access validator queries allowed party fields and inspects candidates instead of bypassing permissions.
- `frappe.boot.get_bootinfo` is not whitelisted; language resolution was verified through authenticated Desk HTML.
- The first sales assertion assumed historical delivery percentage would survive a full return; the validator now checks historical delivery evidence separately from the net order state.

## Confirmed native support with no implementation gap

The current evidence supports native use for:

- purchase orders, full/partial receipts, invoices, full/partial payments, and purchase returns
- opening stock, delivery, warehouse transfer, reconciliation, zero-stock query, and insufficient-stock rejection
- quotation, full/partial delivery, alternate UOM, invoices, customer payments, customer returns, and credit notes
- transaction-level and report-level AR/AP traceability
- Stock Balance, Stock Ledger, Purchase Analytics, Sales Analytics, Accounts Receivable, Accounts Payable, and General Ledger
- role-based access, attribution, native Workflow approval, Version audit history, and cancelled-entry accounting traceability

These results apply only to the executed synthetic scenarios and are not proof of unrecorded production requirements.

## Customization decision

No confirmed item currently requires a Custom Field, Custom DocType, custom business validation, custom report, or `hardware_erp` app.

P0.8 may approve a versioned standard ERPNext Print Format configuration if bilingual formal output is a first-release requirement. That decision alone does not require a Frappe Custom App. Create `hardware_erp` only if a later frozen `Must` requirement cannot be met acceptably through native configuration or an approved process.

## Items requiring owner confirmation in P0.8

- Whether formal Chinese, English, or bilingual PDFs are mandatory for the first release.
- The production organization, user population, approval thresholds, and segregation-of-duties matrix.
- The production chart of accounts, tax model, numbering series, warehouses, pricing governance, and master-data ownership.
- Which real-data domains must be migrated at cutover and their reconciliation owners.
- Whether any external integration or governed Business API is required for the first deployment.

Until confirmed, these are requirements questions rather than technical gaps.

## P0.7 closeout status — 2026-10-06

The six confirmed items have evidence and an ordered Phase 0 disposition. Native capability discovery and local technical checks are complete; P0.7 progression review is awaiting an explicit recorded decision. Scope freeze, organization/tax/migration choices, PDF remediation, and release-readiness work have not been approved or completed by this analysis.

The current roadmap's first four discovery criteria are evidenced by environment checks, source-controlled synthetic assumptions, workflow/report execution, and this classification. Its remaining development and release criteria are still open. No `hardware_erp` implementation is authorized by the evidence alone.
