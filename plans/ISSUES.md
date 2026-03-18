# Inter-Agent Issue Queue

When an agent discovers a problem in the OTHER agent's code — or in a shared file — log it here. The other agent checks this file at the start of every day.

**Rules:**
- Check this file BEFORE starting each new day
- Fix any issues assigned to you BEFORE starting new day work
- Mark issues as resolved when fixed (don't delete — strikethrough)
- If you find a bug but can work around it, still log it — the owning agent needs to know
- If you fix something in the other agent's file as an emergency, log it here AND in HANDOFF.md

---

## Format

```
### ISSUE-XXX | [SEVERITY] [TITLE]
**Filed by:** Agent A | Agent B
**Assigned to:** Agent A | Agent B
**Found on:** Day XX
**Status:** open | in_progress | resolved
**File(s):** [paths]

**Problem:** [what's wrong]
**Impact:** [what breaks if not fixed]
**Suggested fix:** [optional — how to fix it]

**Resolution:** [filled in by the fixer]
```

Severity levels:
- **BLOCKER** — I cannot continue my work until this is fixed
- **BUG** — Something is wrong but I can work around it
- **WARN** — Potential problem I noticed, not blocking yet
- **REQUEST** — I need a change to a file you own

---

<!-- Issues below this line. Number sequentially: ISSUE-001, ISSUE-002, etc. -->
