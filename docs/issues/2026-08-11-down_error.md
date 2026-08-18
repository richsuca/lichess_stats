# 2026-08-11 — down_error

## Problem

`download_games.py` crashes with an HTTP 404 on every run, including
incremental runs that previously worked.

```
$ ./venv/bin/python download_games.py
Incremental fetch since 1783567347945 ms (includes overlap, will dedupe)...
Traceback (most recent call last):
  ...
  File "/home/richard/lichess_stats/download_games.py", line 111, in main
    for game in iterator:
  ...
berserk.exceptions.ResponseError: HTTP 404: Not Found: {'error': 'Not found'}
```

Full traceback in the original report (berserk → `requests` →
`raise_for_status`). Failing URL:

```
https://lichess.org/api/games/user/richsu?since=1783567347945&rated=true&moves=false&tags=false&clocks=false&evals=false&opening=false
```

### Root cause (investigated, not our code)

This is an **upstream Lichess API regression**, tracked at
https://github.com/lichess-org/api/issues/667 (opened 2026-08-02, still
open, no linked PR at time of writing).

Reproduction against the live API confirms the issue is on Lichess's
side, not in `download_games.py`:

| Request                                                | Result                                      |
| ------------------------------------------------------ | ------------------------------------------- |
| `GET /api/user/richsu`                                 | 200 — user exists, `count.rated = 626`      |
| `GET /api/games/user/richsu` (no params)               | 404 `{"error":"Not found"}`                 |
| `GET /api/games/user/richsu?since=0`                   | 404 `{"error":"Not found"}`                 |
| `GET /api/games/user/richsu` with `Accept: x-ndjson`   | 404 `{"error":"Not found"}` (berserk's path) |
| `GET /api/games/user/richsu` with no Accept header     | 404, text/html SPA "Page not found" page    |

The regression is **not** account-specific, **not** header-specific,
and **not** parameter-specific (per issue #667; reproduced here for
`richsu`). The `since` timestamp is valid (`1783567347945` ms =
`2026-07-09T03:22:27Z`, derived from `last_fetch_ms` minus `OVERLAP_MS`).
`USERNAME = "richsu"` is correct.

### Impact

- **No new games can be fetched** until Lichess fixes #667.
- **No state corruption**: the 404 raises inside `for game in iterator:`
  (`download_games.py:111`), before `save_state()` is reached, so
  `lichess_data/fetch_state.json` is left untouched. The next
  successful run resumes from the same `last_fetch_ms`.
- **`stats.py` is unaffected** — it reads the committed
  `lichess_data/games_*.json` batches and still prints monthly stats.

## Plan

1. Re-check whether the endpoint is still broken before doing anything
   else (issue #667 may be fixed by the time this is executed):
   `curl -sS -o /dev/null -w "%{http_code}\n" -H "Accept: application/x-ndjson" \
     "https://lichess.org/api/games/user/richsu?max=1"`
   → verify: `200` means Lichess fixed it → just re-run
   `./venv/bin/python download_games.py` and close this issue.
   `404` means still broken → continue to step 2.
2. Add graceful handling of the 404 in `download_games.py` so the script
   prints a clear, actionable message and exits 0 (or a distinct
   non-zero code) instead of dumping a traceback. Catch
   `berserk.exceptions.ResponseError` around the iterator; on HTTP 404
   specifically, print something like:
   `"Lichess games endpoint is currently broken (upstream issue \
   lichess-org/api#667). No games fetched; state unchanged. stats.py \
   still works on already-downloaded data."`
   → verify: run the script while the endpoint is down and confirm it
   exits cleanly with that message and no traceback; confirm
   `fetch_state.json` is byte-identical before/after.
3. Keep the existing crash-on-other-errors behaviour — only swallow the
   404 "endpoint broken" case. Other `ResponseError`s (429 rate limit,
   5xx, network) should still surface so they aren't silently masked.
   → verify: temporarily point `USERNAME` at a non-existent user to
   trigger a 404 from a different cause and confirm it's still reported
   distinctly (or that the message is worded so it doesn't claim
   "upstream broken" for a genuinely-missing user). Decide on wording.
4. Link issue #667 in the script's module docstring / README so the
   context survives outside this issue file.
   → verify: `README.md` mentions the upstream dependency and the
   tracking issue.
5. Track upstream: re-test the endpoint periodically. When #667 is
   fixed, revert the workaround-only parts (the 404 swallow) if it
   feels like dead weight, or keep it as defensive code.
   → verify: a normal `download_games.py` run fetches new games and
   updates `fetch_state.json`.

## Result

Completed 2026-08-17.

### Step 1 — re-check endpoint

```
$ curl -sS -o /dev/null -w "%{http_code}\n" -H "Accept: application/x-ndjson" \
    "https://lichess.org/api/games/user/richsu?max=1"
404
```

Still broken. Proceeded to step 2.

### Step 2 — graceful 404 handling

Added `_handle_404()` helper and wrapped the `for game in iterator:` loop
in a `try/except berserk.exceptions.ResponseError`. On HTTP 404 the
script now prints a clear message and exits 0.

Verification (endpoint still down):
```
$ ./venv/bin/python download_games.py
No state file yet; downloading ALL rated games for richsu...
Lichess games endpoint returned 404 for user 'richsu'.
This is a known upstream bug: https://github.com/lichess-org/api/issues/667
No games fetched; state unchanged. stats.py still works on already-downloaded data.
EXIT CODE: 0
```

`lichess_data/` directory left empty (no `fetch_state.json` created,
no batch files written). State is untouched.

### Step 3 — distinct handling for non-existent user

Verified with a fake username:
```
$ USERNAME=test_nonexistent_user_xyz ./venv/bin/python -c "..."
Error: user 'test_nonexistent_user_xyz' not found on Lichess.
Check the USERNAME setting in download_games.py.
EXIT CODE: 1
```

Distinct message (stderr, exit 1) vs. upstream-bug message (stdout,
exit 0). No false "upstream broken" claim for a genuinely-missing user.

Other `ResponseError`s (429, 5xx, etc.) are re-raised via `raise` after
the 404 check — they still surface as tracebacks.

### Step 4 — README updated

Added upstream-dependency note to the `download_games.py` section of
`README.md`, linking to lichess-org/api#667 and explaining the graceful
degradation behaviour.

Also added a module docstring to `download_games.py` referencing the
tracking issue.

### Step 5 — track upstream

Pending. Re-test endpoint periodically. When #667 is fixed:
- `curl` should return 200.
- Re-run `./venv/bin/python download_games.py` — should fetch games
  normally and update `fetch_state.json`.
- Optionally revert the 404-swallow workaround if desired, or keep as
  defensive code.

### Files changed

- `download_games.py` — added `sys` import, module docstring, `_handle_404()`,
  try/except around iterator loop.
- `README.md` — added upstream-dependency note with link to #667.
