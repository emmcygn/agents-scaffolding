# Pre-Flight Checklist

Run this checklist **before Day 1** to ensure the environment is ready. Both agents should verify these items at the start of their first session.

> This file is referenced by the session recovery protocol. If an agent crashes and restarts, it re-runs this checklist before resuming work.

---

## 1. Environment

- [ ] Runtime/language installed at required version: `{{VERSION_CHECK_COMMAND}}`
- [ ] Package manager working: `{{PACKAGE_MANAGER_CHECK}}`
- [ ] Git initialized and on the correct branch: `git branch --show-current`
- [ ] All dependencies installed: `{{INSTALL_COMMAND}}`

## 2. Directory Structure

- [ ] Source directory exists: `ls {{src_directory}}`
- [ ] Plans directory exists: `ls plans/agent-a/ plans/agent-b/`
- [ ] Tasks directory exists: `ls tasks/`
- [ ] Output directory exists (or will be created): `{{OUTPUT_DIR}}`

## 3. Tool Verification

- [ ] Linter runs without crashing: `{{LINT_COMMAND}}`
- [ ] Type checker runs: `{{TYPECHECK_COMMAND}}`
- [ ] Test runner works (0 tests collected is fine on Day 1): `{{TEST_COMMAND}}`
- [ ] Build/compile succeeds: `{{BUILD_COMMAND}}`

## 4. Permissions (Claude Code)

Set permissions so agents don't block on every tool call:

```
/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)
```

Or configure in `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Edit(*)",
      "Write(*)",
      "Read(*)",
      "Glob(*)",
      "Grep(*)"
    ]
  }
}
```

> **Why this matters:** Without pre-approved permissions, agents stop at the first tool call and wait for user approval. If you walk away expecting autonomous execution, nothing happens.

## 5. Shared Contracts

- [ ] Shared interface/contract file exists (or will be created by Agent A on Day 1): `{{SHARED_CONTRACT_FILE}}`
- [ ] Config file exists (or will be created by Agent B on Day 1): `{{SHARED_CONFIG_FILE}}`
- [ ] Both agents agree on the interface boundary

## 6. Communication Files

- [ ] `plans/STATE.md` — has your agent sections with `not_started` rows
- [ ] `plans/HANDOFF.md` — exists and is empty (ready for entries)
- [ ] `plans/ISSUES.md` — exists and is empty
- [ ] `tasks/lessons.md` — exists and is empty

## 7. Smoke Test

Run the full verification command to establish a passing baseline:
```bash
{{VERIFY_COMMAND}}
```

If this fails on Day 1, that's expected (no code yet). But it should not crash — the tooling itself must work.

---

## Recovery Mode

If you're resuming after a crash (not starting fresh):

1. Run this checklist to verify environment
2. `cat plans/STATE.md` — find your last completed day
3. `cat plans/ISSUES.md` — check for issues assigned to you
4. `cat plans/HANDOFF.md` — catch up on deliverables
5. `cat tasks/lessons.md` — load corrections
6. `git log --oneline -10` — verify recent commits
7. Resume from the next `not_started` day
