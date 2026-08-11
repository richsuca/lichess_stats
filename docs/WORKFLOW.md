# Coding Workflow: Problem → Fix → Test → Rollback/History

A practical workflow for working with a coding agent (pi). The backbone is
**git + small commits**, with a lightweight issue log for the narrative. Git
gives you rollback and history; the log gives you readable context that code
diffs alone never capture.

---

## Setup (one time)

Add a `.gitignore` (ignore `venv/`, `__pycache__/`, `*.pyc`,
`lichess_data/fetch_state.json`, `output_md/`), then:

```bash
cd /home/richard/lichess_stats
git init
git add -A && git commit -m "baseline"
```

---

## Per-issue workflow

### 1. Capture the issue BEFORE touching code

Keep a running log. Two options:

- **Single file:** append to `ISSUES.md` (flat, chronological).
- **One file per issue:** `docs/issues/<slug>.md` (grep-able, easier to link
  from commits).

Template for one issue entry:

```markdown
# 2026-06-29 — <slug>

## Problem
<What's wrong. Symptoms. Which file/function.>

## Plan
1. <step> → verify: <check>
2. <step> → verify: <check>
3. <step> → verify: <check>

## Result
<What happened. Commit <sha>. Or: rolled back, retried with approach B.>
```

Writing the Problem/Plan *first* is what makes the history readable later —
it records **intent**, which code diffs never capture. It also forces
success criteria up front ("Define success criteria. Loop until verified."
per AGENTS.md).

### 2. Ensure you have a rollback point before the agent changes anything

If `git status` is clean, you already do — `HEAD` is your rollback
point, and `git checkout -- . && git clean -fd` will restore it.
**Do nothing.**

If there's uncommitted work, commit it first so it becomes part of
`HEAD`:

```bash
git status                          # confirm clean -> no commit needed
git add -A && git commit -m "checkpoint: pre-fix for <slug>"  # only if dirty
```

### 3. Let the agent work

In pi: describe the problem, point at the file, ask for the fix. The agent
edits files. Ask it to state assumptions and a plan before coding (AGENTS.md
§1).

### 4. Test

Tests live in `tests/`. Run them:

```bash
PYTHONPATH=src ./venv/bin/python -m pytest tests/

```

For a new bug, ask the agent to first write a test that reproduces it, then
make it pass (AGENTS.md §4).

### 5a. Success → commit with a structured message

```bash
git add -A
git commit -m "fix(<area>): <one-line summary>

Problem: <what was wrong>
Fix: <what changed>
Verified: tests/test_<x>.py"
```

Then append a **Result** section to the issue file and commit it:

```bash
git add <issue-file> && git commit -m "doc: close <slug>"
```

### 5b. Failure → rollback

Throw away all agent changes since the last commit:

```bash
git checkout -- .          # revert tracked files
git clean -fd              # remove untracked files the agent added
```

If you already committed the bad work:

```bash
git reset HEAD~1           # undo last commit, KEEP files on disk to inspect
git reset --hard HEAD~1    # undo last commit, DISCARD files entirely
```

Then re-prompt the agent with a different approach. The issue file's Plan
section is still valid — just iterate.

---

## Reading the history later

- **Code history (per file):**
  `git log --oneline -- src/docling_pdf_to_md/cli.py`
- **Full diff of one change:**
  `git show <sha>`
- **Why a line was introduced:**
  `git log -S "divmod" -- src/`  (finds commits that added/removed that string)
- **Issue narrative:**
  read `ISSUES.md` / `docs/issues/`, or `git log -- ISSUES.md` for the doc's
  own evolution.
- **pi session transcript:** pi keeps conversation history per project — the
  long-form back-and-forth reasoning that doesn't survive into commits.
  Treat the issue file as the *summary*, the pi session as the *long form*.

---

## Habits that make it cheap

1. **Commit constantly.** Every test pass = one commit. Small commits are
   easy to revert and easy to read. `git commit -am "wip"` is fine mid-session;
   `git rebase -i` later to clean up before sharing.
2. **Write the issue file first.** It forces success criteria up front and is
   what makes the history worth reading six months later.

---

## Minimal version (zero ceremony)

The absolute minimum that gives rollback + history:

```bash
git init && echo "venv/" > .gitignore && git add -A && git commit -m init
# before each agent task (only if tree is dirty; if clean, HEAD is
# already your rollback point and you can skip this):
git commit -am "checkpoint"
# agent works + tests pass:
git commit -am "fix: <summary>"
# tests fail:
git checkout -- . && git clean -fd
```

Everything above (ISSUES.md, structured messages, `tests/`) is an enhancement
on this core.

---

## Quick-reference command cheat sheet

| Goal | Command |
|------|---------|
| See what changed | `git status` / `git diff` |
| Save a checkpoint (only if tree dirty) | `git add -A && git commit -m "..."` |
| Throw away agent's edits | `git checkout -- . && git clean -fd` |
| Undo last commit, keep files | `git reset HEAD~1` |
| Undo last commit, discard files | `git reset --hard HEAD~1` |
| Per-file history | `git log --oneline -- <path>` |
| See one change in full | `git show <sha>` |
| Find when a line was added | `git log -S "<string>" -- <path>` |
| Run tests | `PYTHONPATH=src ./venv/bin/python -m pytest tests/` |
