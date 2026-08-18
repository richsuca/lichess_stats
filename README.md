# lichess_stats

Personal Lichess game stats. Downloads your rated games via the Lichess
API and prints monthly win/loss/draw breakdowns per perf type (blitz,
rapid, bullet, etc.).

## Setup

```bash
# from the project root, with the existing venv
./venv/bin/pip install berserk==0.14.0
```

`berserk` is the only direct dependency; the rest (`requests`, `ndjson`,
`python-dateutil`, ...) come in transitively.

## Scripts

### `download_games.py` — fetch games from Lichess

Incrementally downloads your rated games into `lichess_data/games_*.json`,
one timestamped batch per run.

- Uses the [`berserk`](https://github.com/rhgrant10/berserk) Lichess API
  client.
- **Upstream dependency:** the Lichess games-by-user endpoint has a known
  regression ([lichess-org/api#667](https://github.com/lichess-org/api/issues/667),
  opened 2026-08-02). When the endpoint returns 404 for all requests, the
  script detects the situation and exits gracefully with an informational
  message instead of dumping a traceback. State is left unchanged so the
  next successful run resumes normally.
- Targets the user `richsu` (edit `USERNAME` at the top of the file to
  use your own).
- `API_TOKEN` is optional: leave it `None` to use an anonymous client,
  which works for public game data. Set it (e.g. via an env var) only if
  you need a higher rate limit or private data.
- State is kept in `lichess_data/fetch_state.json`:
  - `last_fetch_ms` — timestamp of the newest game seen; the next run
    fetches games since `last_fetch_ms - OVERLAP_MS`.
  - `seen_ids` — bounded list of recently-seen game ids used to dedupe
    across the overlap window (kept to the last 5000 entries).
- `OVERLAP_MS` (default 5 min) re-fetches a small window each run to
  avoid boundary/ordering issues; duplicates are dropped by id.
- `PERF_TYPES` (default `None`) — set to a list like `["blitz", "rapid"]`
  to filter by perf type; `None` fetches all rated perfs.
- Each game is stored as a minimal record: `id`, `createdAtMs`, `perf`,
  `result` (W/L/D from the targeted user's perspective).

Run it:

```bash
./venv/bin/python download_games.py
```

First run downloads all rated games; subsequent runs are incremental.

### `stats.py` — print monthly stats

Loads every `lichess_data/games_*.json` batch, dedupes by `id`, and
prints monthly W/L/D counts and win percentage per perf type. Perfs are
printed in a fixed preferred order (blitz, rapid, bullet, classical,
ultraBullet) then any others alphabetically.

Run it:

```bash
./venv/bin/python stats.py
```

### `verified_monthly_stats.json`

A hand-verified snapshot of monthly stats (per perf, per month:
`games`, `W`, `L`, `D`, `winPct`). Kept as a reference/checkpoint of
what the output looked like at a known-good point.

## Layout

```
download_games.py          # fetcher
stats.py                   # monthly stats reporter
lichess_data/              # game batches (games_*.json) + fetch_state.json (gitignored)
verified_monthly_stats.json
docs/                      # WORKFLOW.md, issues/
venv/                      # gitignored
```

`lichess_data/fetch_state.json` is gitignored (runtime state, changes
every run). The `games_*.json` batches are committed so `stats.py` works
out of the box.

## Workflow

See `docs/WORKFLOW.md` for the git + issue-log workflow used on this
repo.
