# 2026-08-11 — github_sync

## Problem

Push this local repo to a new public GitHub remote at
`https://github.com/richsuca/lichess_stats` (free account → public
repo). Before pushing, ensure **no secret or sensitive data** is in
anything that will be made public, then perform the push.

## Secret / sensitivity audit (done)

Scanned all 12 tracked files plus the full git history (3 commits) plus
the working tree for ignored files that might be sensitive.

**No secrets found.** Details:

| Check                                                    | Result                                                |
| -------------------------------------------------------- | ----------------------------------------------------- |
| Secret-keyword scan (`token`, `secret`, `password`, `api_key`, `bearer`, `-----BEGIN`, …) across tracked files + issue notes | Only `API_TOKEN = None` in `download_games.py:9` (placeholder, not a value); doc references in `README.md` and `docs/issues/` |
| 40+ char high-entropy blobs (Lichess tokens are 40+ hex; `lic_…`, `ghp_…`, `github_pat_…`, 40-hex) across all tracked blobs in history | No matches                                            |
| `.env`, `.env.*`, `.netrc`, `.git-credentials`, `id_rsa`, `id_rsa.pub` on disk | None exist                                            |
| `git config` for `remote`, `credential`, `http.extraHeader`, `user.` | None — purely local repo, no remote configured        |
| `lichess_data/games_*.json` (5 batch files, ~67 KB)      | **Currently tracked.** Each record is `{id, createdAtMs, perf, result}` — **no username, no opponent names** (verified: `richsu` does not appear in any batch). Game IDs are public on lichess.org but re-identifiable via cross-reference. Per plan step 1, this dir will be untracked + history-rewritten. |
| `lichess_data/fetch_state.json` (runtime state)          | Gitignored, not tracked. Contains `last_fetch_ms` + `seen_ids` (public game IDs) |
| `venv/`                                                  | Gitignored, not tracked                               |
| Anything committed then removed in history               | No — only 3 commits, all the same 12 files            |

**Privacy note (not a secret):** the username `richsu` appears in
tracked files **only** at `download_games.py:8` (`USERNAME = "richsu"`)
and `README.md:26`. It does **not** appear in any `lichess_data/`
batch or in `verified_monthly_stats.json` (verified by grep). So:

- The raw game dump (`lichess_data/games_*.json`) is de-identified but
  re-identifiable via Lichess game IDs. **Decision: keep it out of the
  public repo** (plan step 1).
- `verified_monthly_stats.json` (repo root) is just per-perf monthly
  W/L/D counts — no username, no game IDs. Least identifying. Still an
  open sub-decision (step 1).
- `USERNAME = "richsu"` in `download_games.py` + the README mention
  **will** be public and directly link `richsuca` ↔ `richsu`. If that
  link is the concern, those need parametrising too (flagged in step 1,
  not planned unless you say so). If the concern is only the raw data
  dump, gitignoring `lichess_data/` is sufficient.

## Plan

1. **Decision: gitignore all of `lichess_data/`.**
   a. Update `.gitignore`: replace the `lichess_data/fetch_state.json`
      line with `lichess_data/` (ignores the whole directory).
   b. Untrack the dir without deleting it from disk:
      `git rm -r --cached lichess_data/`
   c. **History rewrite (required for a clean first push).** The
      baseline commit `4beaf99` contains the 5 game batches.
      `git rm --cached` alone leaves them in history, and `git push`
      sends *all* history — so the games would still land on GitHub.
      Since this repo is pre-push with only 3 local commits, collapse
      to a single fresh baseline that excludes `lichess_data/`:
      ```
      git reset --soft $(git rev-list --max-parent=0 HEAD)
      git commit --amend -m "baseline"
      ```
      This squashes baseline + docs + close-issue commits into one
      clean baseline. The issue files and README still record the
      narrative; only the per-step commit separation is lost (fine for
      a pre-push personal repo). The shas cited in
      `docs/issues/2026-08-11-setup_and_analyse.md` Result will go
      stale — acceptable, the narrative survives.
      Alternative if the 3-commit history matters:
      `git filter-repo --path lichess_data/ --invert-paths` (needs
      `git-filter-repo` installed), then commit the `.gitignore`
      change on top.
   → verify: `git ls-files lichess_data/` prints nothing;
   `git log --all -- lichess_data/` prints nothing (no commit touches
   the dir); files still on disk (`ls lichess_data/` shows 5 batches +
   `fetch_state.json`); `./venv/bin/python stats.py` still runs.

   **Open sub-decision: `verified_monthly_stats.json`** (repo root).
   No username, no game IDs — just per-perf monthly W/L/D aggregates.
   - **(i)** Keep tracked — aggregate counts, useful checkpoint,
     doesn't identify the user on its own. → do nothing.
   - **(ii)** Untrack for consistency — `git rm --cached
     verified_monthly_stats.json`, add to `.gitignore`, fold into the
     squash in 1c. → verify: not in `git ls-files`.

   **Flagged, not planned:** `USERNAME = "richsu"` in
   `download_games.py:8` and `README.md:26` stays public and directly
   links `richsuca` ↔ `richsu`. If that's unacceptable, say so and I'll
   add a step to parametrise it (env var) and scrub the README mention.
   Otherwise the account link is the cost of a public repo for a
   personal Lichess tool.
2. Confirm clean state: `git status` clean, `git log --oneline` shows
   the single fresh baseline (post-squash) — or baseline + filter-repo
   rewritten history if that alternative was used.
   → verify: `git status` prints nothing; no surprise untracked files;
   `git log --all -- lichess_data/` still prints nothing.
3. Create the remote on GitHub. Two options — pick based on how you
   want to authenticate:
   - **(a) `gh` CLI** (recommended): `gh repo create richsuca/lichess_stats --public --source=. --remote=origin --description "Personal Lichess game stats — incremental fetch + monthly W/L/D reporter"`
     This creates the remote, sets `origin`, and pushes in one command.
     Requires `gh auth login` first (see auth step 4a).
   - **(b) `git` + web**: create the empty repo at
     `https://github.com/new` (name `lichess_stats`, **no** README,
     **no** .gitignore, **no** license — would conflict with the
     baseline commit). Then locally:
     `git remote add origin https://github.com/richsuca/lichess_stats.git`
     `git push -u origin main` (or `master` — check `git branch --show-current`)
     → verify: `git remote -v` shows `origin`; `gh repo view` or the
     web UI shows all commits.
4. **Authenticate** (you'll be prompted; pick one):
   - **(a) `gh auth login`** — opens a browser flow, stores a
     Personal Access Token (PAT) in your system credential store. This
     is the smoothest path and makes `gh` + `git` both work afterward.
   - **(b) SSH**: `ssh-keygen -t ed25519 -C "richsuca@github"` (if no
     key exists), `cat ~/.ssh/id_ed25519.pub` → add that public key at
     https://github.com/settings/keys, then use the SSH remote:
     `git remote set-url origin git@github.com:richsuca/lichess_stats.git`
   - **(c) HTTPS + PAT**: create a fine-grained PAT at
     https://github.com/settings/personal-access-tokens with
     `Contents: read/write` for the new repo; on first `git push`
     Git will prompt for username (`richsuca`) and password (paste the
     PAT — not your GitHub password). To avoid re-prompting, use a
     credential helper: `git config credential.helper store` (plain) or
     `cache --timeout=3600` (in-memory, 1h).
   → verify: `gh auth status` (for 4a) or `ssh -T git@github.com`
   (for 4b) succeeds before attempting the push.
5. Push and confirm:
   `git push -u origin <branch>` (if not already pushed by `gh repo create`).
   → verify: `git log origin/<branch> --oneline` matches local; the
   GitHub repo page shows the README, scripts, and docs.
6. Final post-push secret re-check on the remote (defensive — in case
   anything slipped into a blob not in the working tree):
   `git log --all -p | grep -iE 'token|secret|password|api_key|bearer|-----BEGIN' | grep -v 'API_TOKEN = None' | grep -v 'docs/issues/'`
   → verify: no output (or only the known `None` placeholder / doc
   references). If anything unexpected appears, force-push a fix
   *immediately* and treat the leaked secret as compromised — rotate it
   at the source; GitHub's secret scanning may also flag it.

## Result

### Done — steps 1 & 2 (local prep)

- **Step 1:** `lichess_data/` now fully gitignored (replaced
  `lichess_data/fetch_state.json` line with `lichess_data/`).
  `git rm -r --cached lichess_data/` untracked the 5 game batches
  (files kept on disk). `verified_monthly_stats.json` kept tracked
  (per user decision — it's part of the test). `USERNAME = "richsu"`
  left in `download_games.py` + README (per user decision — public
  info).
- **Step 1c (history rewrite):** squashed the 3 commits (4beaf99 +
  42e49e4 + 1fadfc6) into a single fresh baseline via
  `git reset --soft <root> && git commit --amend -m "baseline"`.
  **Hitch:** forgot to `git add .gitignore` before the soft reset, so
  the first amend committed the old `.gitignore` (with
  `lichess_data/fetch_state.json`). Caught in verification (`git status`
  showed ` M .gitignore`), fixed with a second
  `git add .gitignore && git commit --amend --no-edit`.
- **Step 2:** clean state verified.
  - `git log --oneline` → single commit `07d6de4 baseline`.
  - `git ls-files` → 9 files, no `lichess_data/`.
  - `git log --all -- lichess_data/` → empty (no commit in history
    touches the dir; the squash fully erased it).
  - `ls lichess_data/` → 5 batches + `fetch_state.json` still on disk.
  - `./venv/bin/python stats.py` → runs, prints monthly stats.
  - `git status` → clean.
- **Secret recheck on final history:** no actual token values
  (`lic_…`, `ghp_…`, `github_pat_…`, 40-hex) — only the word "token"
  in docs/code and `API_TOKEN = None` placeholder. Clean.

### Done — steps 3-6 (remote + push)

- **Step 3 (remote):** an empty public repo already existed at
  https://github.com/richsuca/lichess_stats (created via web; no
  README/.gitignore/license, `isEmpty: true`, no default branch).
  `gh repo create` returned "Name already exists" — expected, so no
  creation needed. Remote `origin` (HTTPS) added locally earlier.
- **Step 4 (auth):** `gh` CLI installed + `gh auth login` completed
  by user (account `richsuca`, HTTPS protocol, scopes include `repo`).
  Git operations over HTTPS use `gh`'s stored token automatically — no
  PAT paste, no credential helper needed.
- **Step 5 (push):** `git push -u origin master` → `* [new branch]
  master -> master`. `master` tracks `origin/master`.
- **Step 6 (post-push recheck):**
  - Local/remote parity: `git log --oneline master` and
    `git log --oneline origin/master` both → `7290b0f baseline`.
  - Remote tree (`gh api .../git/trees/master`): `.gitignore`,
    `README.md`, `docs/`, `download_games.py`, `stats.py`,
    `verified_monthly_stats.json` — **no `lichess_data/`**.
  - Secret value scan on history (`lic_…`, `ghp_…`, `github_pat_…`,
    `gho_…`, 40-hex): no matches. Clean.

### Final state

- **Remote:** https://github.com/richsuca/lichess_stats (public).
- **Auth method:** `gh` CLI (`gh auth login`, HTTPS).
- **Final commit sha pushed:** `7290b0f` (single `baseline` commit).
- **Tracked on remote:** 9 files (5 under `docs/`); `lichess_data/`
  fully excluded from tree and history.
