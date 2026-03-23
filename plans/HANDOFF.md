# Inter-Agent Handoff Log

When an agent completes work that the other agent depends on, log it here. The other agent checks this file before starting any day with dependencies.

**Rules:**
- Write an entry when you complete something the other agent needs
- Write an entry when you need something from the other agent
- Write an entry if you modified a shared file
- Include the exact import path or file path so the other agent can find it immediately

---

## Format

```
### [AGENT] → [OTHER AGENT] | Day XX Complete
**Timestamp:** [ISO 8601, e.g. 2026-03-23T14:30:00]
**Duration:** [how long this day took, e.g. ~25 min]
**What's ready:** [description]
**Files:** [list of files created/modified]
**Import paths:** [how to use it]
**Breaking changes:** [any interface changes]
**Verification:** [result of running {{VERIFY_COMMAND}} — e.g. "lint clean, 42 tests pass"]
**Notes:** [coordination details]
```

> **Why provenance matters:** Timestamps and verification results let you audit progress, estimate throughput, and catch regressions. If a day's handoff says "42 tests pass" but the next day sees 38, something broke.

---

<!-- Entries below this line -->
