# 2026-08-11 — setup_and_analyse

## Problem

The project has two working scripts (`download_games.py`, `stats.py`) and a
populated `lichess_data/` directory, but:

- It is **not under git** — `git status` fails with "not a git repository".
  No rollback, no history.
- There is **no `.gitignore`** — `WORKFLOW.md` claims one is "already in
  place" but it isn't; that doc is currently inaccurate.
- There is **no documentation** of what the scripts do or how to run them.
- The local venv is empty; the package list below comes from the original
  Windows installation and needs to be reproduced here (Linux venv).

Reference — packages installed in the original (Windows) venv, to reproduce:

| Package            | Version        |
| ------------------ | -------------- |
| berserk            | 0.14.0         |
| certifi            | 2026.6.17      |
| charset-normalizer | 3.4.9          |
| Deprecated         | 1.3.1          |
| idna               | 3.18           |
| ndjson             | 0.3.1          |
| pip                | 26.1.2         |
| python-dateutil    | 2.9.0.post0    |
| requests           | 2.34.2         |
| six                | 1.17.0         |
| typing_extensions  | 4.16.0         |
| urllib3            | 2.7.0          |
| wrapt              | 2.2.2          |

## Plan

1. Write `.gitignore` (ignore `venv/`, `__pycache__/`, `*.pyc`,
   `lichess_data/fetch_state.json`, any `output_md/`) → verify:
   `git status` shows only intended files staged after `git add -A`.
2. Initialise git and record a baseline commit:
   `git init && git add -A && git commit -m "baseline"` → verify:
   `git log --oneline` shows one commit; `git status` clean.
3. Install runtime deps into the local venv. `berserk` is the only
   third-party import the scripts use directly; the rest come in as
   transitive deps:
   `./venv/bin/pip install berserk==0.14.0` → verify:
   `./venv/bin/python -c "import berserk; print(berserk.__version__)"` prints `0.14.0`
   and `./venv/bin/python -c "import requests, ndjson, dateutil"` succeeds.
4. Write a `README.md` (or `docs/USAGE.md`) covering:
   - what `download_games.py` does (incremental fetch via `berserk`,
     state in `lichess_data/fetch_state.json`, dedupe by game id, overlap
     window `OVERLAP_MS`);
   - what `stats.py` does (loads all `games_*.json`, dedupes, prints
     monthly W/L/D per perf);
   - how to run each (`./venv/bin/python download_games.py`,
     `./venv/bin/python stats.py`), and that `API_TOKEN` in
     `download_games.py` is optional (anonymous client works for public
     data).
   → verify: a fresh reader can run both scripts from the doc alone.
5. Fix `docs/WORKFLOW.md` inaccuracy — remove/soften the "A `.gitignore`
   is already in place" claim now that step 1 makes it true, or note it
   was added as part of this issue. → verify: doc matches repo reality.

## Result

All five steps done. Two commits:

- `4beaf99` — `baseline`: `.gitignore` + existing scripts, docs, and game
  data under git. `lichess_data/fetch_state.json` correctly excluded;
  `venv/`, `__pycache__/` ignored.
- `42e49e4` — `docs(setup): add README, fix WORKFLOW .gitignore claim`:
  added `README.md` documenting both scripts; reframed the inaccurate
  "already in place" line in `docs/WORKFLOW.md` as a setup step.

Verification:

- `git log --oneline` shows both commits; `git status` clean.
- `./venv/bin/pip install berserk==0.14.0` pulled in the full transitive
  set; `./venv/bin/python -c "import berserk, requests, ndjson, dateutil"`
  succeeds. `berserk` prints `0.14.0`.
- Minor transitive version drift vs. the original Windows venv:
  `wrapt` 2.3.0 (was 2.2.2), `certifi` 2026.7.22 (was 2026.6.17). Direct
  deps match. Not worth pinning — these are platform/date-specific.
- `./venv/bin/python stats.py` runs against the committed `games_*.json`
  batches and prints monthly W/L/D per perf (Blitz 2025-01 through
  2026-06, etc.).
- `README.md` covers both scripts' behaviour, run commands, the optional
  `API_TOKEN`, the incremental-fetch state model, and the repo layout.
