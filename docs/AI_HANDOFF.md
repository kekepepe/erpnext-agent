---
project: ERPNext-agent
status: active
current_phase: Phase 0
current_task: Start the Phase 0 environment and verify baseline health
last_updated: 2026-09-01
updated_by: Codex
---

# AI Project Handoff

## Current Objective

Verify how far ERPNext v16 native capabilities can support the hardware-trading workflow before approving any custom development. The immediate task is limited to starting the disposable Phase 0 stack and obtaining a passing baseline health check.

## Verified Current State

- GitHub repository: `kekepepe/erpnext-agent`; default branch: `main`.
- Local `main` is at commit `1548cba` (`chore: bootstrap ERPNext phase 0 environment`) and showed no pre-existing working-tree changes before these collaboration documents were added.
- The tracked local blobs for `README.md`, `ERP与AI智能体设计笔记.md`, `phase0/compose.yaml`, and `scripts/phase0-check.sh` match the files read from the GitHub default branch on 2026-09-01.
- The repository contains a disposable ERPNext/Frappe v16.33.0 Docker Compose environment with MariaDB 11.8 and Redis 6.2.
- `scripts/phase0-check.sh` checks Compose validity, Site creation, required running services, ERPNext/Frappe major versions, and the HTTP ping endpoint.
- `docker compose -f phase0/compose.yaml config --quiet` passed on 2026-09-01.
- Runtime health is **not verified**. `./scripts/phase0-check.sh` could not connect because the local Docker daemon was not running.
- No evidence currently proves that a test company, sample master data, native purchase/sales transactions, stock flows, or accounting flows have been completed.
- No Custom App, MCP server, or Agent implementation exists in the repository.

## Completed

- [x] Bootstrapped a disposable Phase 0 ERPNext environment.
- [x] Pinned the Phase 0 container images and documented local startup and teardown commands.
- [x] Added an automated baseline health-check script.
- [x] Established the GitHub-based Web GPT ↔ Codex collaboration documents.

## In Progress

- [ ] Establish a verified, running Phase 0 baseline.

## Problems / Risks

- Docker daemon was not running during the 2026-09-01 check, so runtime validation remains blocked.
- The repository contains infrastructure for validation but not the validation evidence itself. Documentation must not infer native workflow completion from the existence of Compose files.
- The README contains a local disposable-demo password. It must never be reused for staging or production.
- Business requirements are still high-level. Premature customization could duplicate ERPNext native capabilities or lock in an unsupported workflow.

## Next Actions

### P0 — Must Do

- [ ] Start Docker, run `docker compose -f phase0/compose.yaml up -d`, wait for Site creation, then run `./scripts/phase0-check.sh`. Record the exact result in this handoff.
- [ ] After the health check passes, initialize a clearly named test company and define the validation dataset: approximately 20 representative SKUs, 3 suppliers, 3 customers, warehouses, units of measure, opening stock, tax assumptions, and opening balances. Do not use production-sensitive data.
- [ ] Define and execute an evidence checklist for native purchase, stock, sales, returns, and accounts receivable/payable flows. Record each result as supported, configurable, gap, or not tested.

### P1 — Should Do

- [ ] Convert confirmed gaps into a Gap Analysis with business impact, native workaround, configuration option, and customization recommendation.
- [ ] Decide the minimum `hardware_erp` custom-app scope only after the Phase 0 evidence is reviewed.

### P2 — Later

- [ ] Design stable ERP business APIs for approved workflows.
- [ ] Add an MCP layer and the first narrow Agent use case only after API boundaries, permissions, audit logging, and human approval rules are defined.

## Validation Requirements

For the current task, all of the following must be true before marking it complete:

- `docker compose -f phase0/compose.yaml config --quiet` exits successfully.
- `create-site` exits with code 0.
- All services required by `scripts/phase0-check.sh` are running.
- The script reports ERPNext and Frappe 16.x.
- `http://localhost:8080/api/method/ping` returns `pong` through the script.
- The exact command, date, and result are recorded here; failures remain visible rather than being rewritten as success.

Later native-workflow validation must include reproducible test data, document identifiers or screenshots where appropriate, expected versus actual behaviour, and a consolidated Gap Analysis.

## Notes for Next Agent

- Read all repository instructions and project documents before acting.
- Work only on the first unchecked P0 item: obtain a passing runtime baseline. Do not begin Custom App, API, MCP, or Agent work.
- The Docker daemon must be started by the user or through an explicitly authorized local action before the current health check can pass.
- Treat `ERP与AI智能体设计笔记.md` as project intent, not proof of implementation.
- Update this file in the same change as any implementation or validation evidence.
