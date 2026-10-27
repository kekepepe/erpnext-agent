# hardware_erp — bounded approval guard

Independent Frappe app 0.1.0. Approved N2 dependency: R1-09/R1-10 and DEC-012.
No custom endpoint, schema, SQL, direct database access or ERPNext Core change.
Nine native transaction types use document event hooks; native Workflow and
permissions remain the engine. Frozen limits: orders CNY 10,000 and payments
CNY 20,000; higher amounts require a second independent owner review. Makers
cannot approve their own documents, including accidental dual-role assignment.

`before_validate` checks current inputs/state/identity and forbids business edits
inside a transition or intermediate review. `before_submit` rechecks roles and
thresholds after native calculation. `before_cancel` rejects mutation of the
original inputs. `before_update_after_submit` protects submitted business data.
Native Workflow return-to-Pending permits correction and complete reapproval.
Negative payment values are rejected; refunds use positive amounts and native
Pay/Receive types, returns or cancellation.

The disposable P0 company is an explicit discovery compatibility exception,
not a deployment pattern. Changing a protected existing document into that
company does not bypass validation. Before release, remove P0 fixtures/accounts
and do not reuse that company name. Company-scoped permissions, native roles,
admin access, data mapping and real UAT remain required; the app does not protect
against privileged infrastructure/admin code execution.

## Install and verify

Use the repository fixed image via `scripts/phase0-start.sh`; it installs this
app through native bench and preserves existing site data. Then apply native
configuration in order: configure-release, configure-access, configure-reports;
all scripts default to read-only. Acceptance is
`phase0-validate-release-access.py --exercise` on disposable localhost only;
unit invariants are `test_hardware_approval_rules.py`. Tested ERPNext16.33.0 /
Frappe16.31.0; changing versions requires hook lifecycle and workflow revalidation.
P0.10 still requires clean-site installation/migration/uninstall/upgrade impact
review; the long-lived Phase0 rebuild is not evidence of a clean RC.

## Rollback boundary

Stop business writes before withdrawing the guard. Never uninstall it on a
running approved business site and leave native bypasses exposed. Retain prior
image/source and private native configuration backups. Restore the matching
whole-site candidate in an isolated copy and reconcile permissions, approvals,
stock, AR/AP and GL before reopening writes. Preserve Version/Workflow records;
do not delete cancelled transactions to hide tests. No destructive uninstall or
production restoration was performed during N2.
