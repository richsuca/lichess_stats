# 2026-08-17 — add_coding_best_practise

## Problem

The project has two Python scripts (`download_games.py`, `stats.py`) with no
automated checks for code quality, type correctness, or spelling. Bugs, style
drift, and typos can slip in unnoticed.

Goal: add lightweight tooling that catches common issues before they reach the
repo.

## Plan

1. **Add `ruff`** — linter + formatter (replaces flake8, isort, black in one
   tool).
   - Install: `./venv/bin/pip install ruff`
   - Config: add `[tool.ruff]` section to `pyproject.toml` (or use defaults)
   - Run: `./venv/bin/ruff check .` and `./venv/bin/ruff format --check .`
   - Verify: both commands exit 0 with no errors on current code.

2. **Add `mypy`** — static type checker.
   - Install: `./venv/bin/pip install mypy`
   - Run: `./venv/bin/mypy *.py`
   - Verify: exits 0. Fix any type errors surfaced (the code already uses some
     type hints like `list[str]`, `dict`, `int | None`).

3. **Add `typos`** — spell checker for source code and docs.
   - Install: depends on platform; see
     <https://github.com/crate-ci/typos#install>
   - Run: `typos .`
   - Verify: exits 0. Fix any real typos; add false positives to
     `_typos.toml` if needed.

4. **Optional: add a pre-commit hook or Makefile target** to run all three in
   one command (e.g., `make check` or `pre-commit run --all-files`). Only if
   it adds value without overcomplicating the workflow.

5. **Document** the checks in `README.md` under a "Development" or "Checks"
   section so future runs know how to invoke them.

## Result

Completed 2026-08-17.

### Tools added

| Tool    | Version | Purpose                          |
| ------- | ------- | -------------------------------- |
| `ruff`  | 0.16.3  | Linter + formatter               |
| `mypy`  | 2.3.1   | Static type checker              |
| `typos` | 1.28.4  | Spell checker (installed to `~/.local/bin/`) |

### Fixes applied to pass checks

- `download_games.py:157` — replaced `if x > y: y = x` with `y = max(y, x)` (PLR1730)
- `download_games.py:168` — added `tz=timezone.utc` to `datetime.now()` (DTZ005)
- Both `.py` files reformatted by `ruff format`

### Deviation from plan

- Skipped the Makefile — `make` is not installed on this system. Used a
  `check.sh` shell script instead (no installation required).

### Files changed

- `download_games.py` — 2 lint fixes + formatting
- `stats.py` — formatting only
- `check.sh` — new: runs all checks
- `README.md` — added "Checks" section, updated layout

### Verification

```
$ ./check.sh
=== ruff check ===
All checks passed!
=== ruff format ===
9 files already formatted
=== mypy ===
Success: no issues found in 2 source files
=== typos ===
All checks passed.
```
