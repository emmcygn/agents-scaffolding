# Troubleshooting

Battle-tested failure modes from production multi-agent builds. These are the issues you will hit — not might hit. Knowing them upfront saves hours.

---

## 1. Agents Keep Asking for Permission

**Symptom:** You walk away, come back an hour later, and the agent has done nothing — it's waiting for you to approve a `Read` or `Bash` call.

**Fix:** Pre-approve permissions before launching agents:
```
/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)
```

Or add to `.claude/settings.json`. See `plans/BOOTSTRAP.md` for details.

**Why:** Claude Code defaults to asking permission for most tool calls. Agents can't run autonomously without pre-approved permissions.

---

## 2. Task Plans Don't Match Real APIs

**Symptom:** The task plan specifies `library.do_thing(arg)` but the actual API is `library.thing(arg, extra=True)`.

**Fix:** This is expected and healthy. Task plans are specs, not exact code. The agent should:
1. Read the actual library docs or source
2. Adapt the implementation to the real API
3. Note the divergence in `tasks/lessons.md` if it affects future tasks
4. Update the task plan file if the divergence is significant

**Why:** Plans are written before implementation. APIs evolve, and libraries have quirks. The agent's job is to achieve the acceptance criteria, not to copy-paste the implementation details verbatim.

---

## 3. Agent Runs Ahead and Hits a Dependency Wall

**Symptom:** Agent B finishes its current task quickly, starts the next, but it depends on Agent A's output which isn't done yet.

**Fix:** The agent should:
1. Check `plans/STATE.md` for the dependency status
2. Skip to the next non-blocked task (if one exists)
3. Work on non-blocking parts of the current task (docs, tests, config)
4. Write a blocker in `plans/STATE.md` under "Current Blockers"
5. If completely blocked, inform the user

**Why:** Agent B often runs faster because UI/config work is less compute-intensive than core pipeline work. The task plans should be designed so that Agent B has independent work available when blocked.

**Prevention:** When writing task plans, front-load Agent B's independent work (config, docs, UI scaffolding, deployment) and back-load the tasks that depend on Agent A's pipeline.

---

## 4. Two Agents Modify the Same File

**Symptom:** Merge conflict or silent overwrite of the other agent's changes.

**Fix:** This should not happen if ownership rules are followed. If it does:
1. Check the file ownership table in `plans/ORCHESTRATOR.md`
2. The non-owner should revert their changes
3. File a REQUEST in `plans/ISSUES.md` describing what they need changed
4. The owner makes the change and logs it in `plans/HANDOFF.md`

**Prevention:**
- Strict file ownership (defined in ORCHESTRATOR.md)
- Append-only shared files (STATE, HANDOFF, ISSUES) that merge cleanly
- Pairing tasks for shared contract changes
- `git pull --rebase` before starting each task

---

## 5. Agent Declares Victory Prematurely

**Symptom:** Agent marks a task as `completed` but tests are failing or acceptance criteria aren't met.

**Fix:** The post-task protocol requires `{{VERIFY_COMMAND}}` to pass before marking complete. If an agent skips this:
1. The other agent will catch it during cross-validation (step 5b)
2. File a BUG in `plans/ISSUES.md`
3. The agent must re-open the task and fix the issues

**Prevention:**
- Acceptance criteria should include exact commands to run
- Make the verification command the first line of the post-task protocol
- Use strongly-worded instructions: "NEVER mark a task complete without running {{VERIFY_COMMAND}}"

**Source:** Anthropic's "Effective Harnesses" guide identifies premature completion as the #1 failure mode for long-running agents. Their fix: maintain an exhaustive checklist and focus on single features per session.

---

## 6. Acceptance Criteria Fail — Retry Protocol

**Symptom:** `{{VERIFY_COMMAND}}` fails after completing a task's checklist.

**Protocol:**
1. **If the failure is in YOUR code:** Fix it immediately. Do not mark the task complete until it passes.
2. **If the failure is in the OTHER agent's code:** File an issue in `plans/ISSUES.md` with severity:
   - `BLOCKER` if you can't continue without the fix
   - `BUG` if you can work around it
3. **If the failure is a flaky test or environment issue:** Note it in `tasks/lessons.md`, fix the flakiness, re-run.
4. **If you've been stuck for 3+ attempts:** Stop. Write the problem in `plans/STATE.md` under blockers. Move on to non-blocked work.

**Never:** Brute-force retry the same approach. If it failed twice, the approach is wrong — re-think.

---

## 7. Context Window Exhaustion

**Symptom:** Agent responses become confused, forget earlier work, or start hallucinating file contents.

**Fix:**
1. Commit all current work: `git add . && git commit`
2. Update `plans/STATE.md` with current progress
3. Write any important context to `plans/HANDOFF.md`
4. Start a fresh session using the recovery protocol in `plans/BOOTSTRAP.md`

**Prevention:**
- Use subagents for research and exploration (keeps main context clean)
- Commit frequently — git history is infinite context
- Write important decisions to `tasks/lessons.md` (persists across sessions)
- Task plans are self-contained — the agent can reconstruct context from the plan file alone

**Source:** Anthropic's "Context Engineering" guide: structured note-taking + sub-agent architectures keep the main context window lean.

---

## 8. Windows Line Ending Issues (CRLF)

**Symptom:** `git status` shows files as modified when no code changed. Agents "fix" files by running `git checkout --` which reverts the other agent's real changes.

**Fix:**
- Configure: `git config core.autocrlf true` (Windows) or `git config core.autocrlf input` (Mac/Linux)
- Add a `.gitattributes` file: `* text=auto`
- Do NOT run `git checkout --` on files you don't own

**Why:** Windows converts LF to CRLF on checkout. When the other agent commits with LF, git sees every line as changed. This is a phantom diff — the content is identical.

---

## 9. Monitoring Without Interrupting

Check progress from a separate terminal without disrupting the agents:

```bash
# Progress overview
cat plans/STATE.md

# Recent commits
git log --oneline -20

# Open issues
cat plans/ISSUES.md

# Latest handoffs
tail -50 plans/HANDOFF.md

# Test status (won't interfere with agents)
{{VERIFY_COMMAND}}
```

**Tip:** Don't modify any plans/ files from a monitoring terminal while agents are running — you'll create merge conflicts.
