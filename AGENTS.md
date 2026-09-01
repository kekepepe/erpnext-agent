# Repository Instructions for AI Agents

These instructions apply to the entire repository.

## Required startup sequence

Before changing code or project documents, read in this order:

1. `AGENTS.md`
2. `README.md`
3. `docs/AI_HANDOFF.md`
4. `docs/ROADMAP.md`
5. `docs/DECISIONS.md`

Then inspect the actual repository, relevant source code, configuration, Git status, and available tests or validation scripts.

## Source-of-truth order

Resolve conflicts using this priority:

1. Actual code, tests, configuration, and observed runtime behaviour
2. Current Git and GitHub state
3. `docs/AI_HANDOFF.md`
4. `docs/ROADMAP.md` and `docs/DECISIONS.md`
5. Obsidian milestone knowledge
6. Historical conversations

Code may invalidate documentation. When it does, trust the implementation evidence and correct the affected project document in the same change.

## Task control

- Execute the `current_task` in `docs/AI_HANDOFF.md`.
- Within `Next Actions`, work on the first unchecked P0 item unless the handoff explicitly groups several items into one task.
- Do not start P1 or P2 work while a P0 item remains, unless that lower-priority work is a necessary dependency of the current P0 item.
- Do not implement later roadmap phases opportunistically.
- If the current task is blocked, record the blocker and the smallest concrete unblocking action in `docs/AI_HANDOFF.md`; do not silently switch scope.

## Implementation and validation

- Make the smallest coherent change that completes the current task.
- Preserve ERPNext core. Add custom fields, DocTypes, or a custom app only after Phase 0 evidence shows a real gap.
- Keep the Phase 0 environment disposable and separate from staging or production assumptions.
- Do not let an Agent access the ERP database directly. Future automation must use reviewed ERP service/API boundaries and human approval for consequential actions.
- Never commit secrets, reusable credentials, tokens, production data, or private business records.
- Run the validation appropriate to the changed area. Report commands and actual results; never describe an unrun test as passing.
- Review `git diff` and `git status` before handing work back.

## Documentation closeout

After implementation:

1. Update `docs/AI_HANDOFF.md` with what was actually completed, files or modules changed, validation results, unresolved issues, and the recommended next action.
2. Update `docs/DECISIONS.md` only when an important architectural, technical, security, or workflow decision was made.
3. Update `docs/ROADMAP.md` only when a milestone, phase boundary, dependency, or project scope changed.
4. Do not put routine implementation details into `docs/DECISIONS.md` or `docs/ROADMAP.md`.

Obsidian is a milestone knowledge archive, not the per-commit coordination channel. Keep daily execution state in GitHub through code, tests, commits, and `docs/AI_HANDOFF.md`. Distil knowledge to Obsidian at an accepted phase or other explicit milestone.

## Git discipline

- Preserve unrelated user changes in a dirty worktree.
- Keep `docs/AI_HANDOFF.md` in the same commit as the implementation whose state it describes.
- Use focused commit messages such as `feat:`, `fix:`, `test:`, or `docs:`.
- Do not commit or push unless the user explicitly asks for it.
