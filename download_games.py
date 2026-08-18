#!/usr/bin/env python3
"""Incrementally download rated games from the Lichess API.

Upstream dependency note: the games-by-user endpoint has a known regression
tracked at https://github.com/lichess-org/api/issues/667 (opened 2026-08-02).
When that endpoint returns 404 for all requests, this script detects the
situation and exits gracefully instead of dumping a traceback.
"""
import json
import os
import sys
from datetime import datetime, timezone

import berserk

USERNAME = "richsu"
API_TOKEN = None

OUT_DIR = "lichess_data"
STATE_PATH = os.path.join(OUT_DIR, "fetch_state.json")

# Optional perf filter; leave None for all rated perfs
PERF_TYPES = None  # e.g. ["blitz", "rapid"]

# Fetch overlap to avoid boundary/ordering issues (5 minutes is usually plenty)
OVERLAP_MS = 5 * 60 * 1000

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def load_state():
    if not os.path.exists(STATE_PATH):
        return {"last_fetch_ms": None, "seen_ids": []}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(last_fetch_ms: int, seen_ids: list[str]):
    # Keep the seen-id set bounded (only need recent history for dedupe)
    seen_ids = seen_ids[-5000:]
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_fetch_ms": last_fetch_ms, "seen_ids": seen_ids}, f)

def dt_to_ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def result_for_user(game: dict, username: str) -> str:
    winner = game.get("winner")  # 'white'/'black' or None for draw
    players = game.get("players", {})
    w_name = (players.get("white", {}).get("user", {}) or {}).get("name", "")
    b_name = (players.get("black", {}).get("user", {}) or {}).get("name", "")

    if winner is None:
        return "D"
    if w_name.lower() == username.lower():
        return "W" if winner == "white" else "L"
    if b_name.lower() == username.lower():
        return "W" if winner == "black" else "L"
    return "D"

def minimal_record(game: dict, username: str) -> dict:
    created_ms = dt_to_ms(game["createdAt"])
    perf = game.get("perf") or game.get("speed") or "unknown"
    return {
        "id": game["id"],
        "createdAtMs": created_ms,
        "perf": perf,
        "result": result_for_user(game, username),
    }


def bool_query(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"


def make_client():
    if API_TOKEN:
        return berserk.Client(session=berserk.TokenSession(API_TOKEN))
    return berserk.Client()

def _handle_404(client: berserk.Client) -> None:
    """Handle HTTP 404 from the games endpoint.

    Distinguishes between the upstream Lichess bug (issue #667) and a
    genuinely non-existent username, then exits cleanly.
    """
    try:
        client.users.get_public_data(USERNAME)
        # User exists — this is the upstream endpoint regression.
        print(
            f"Lichess games endpoint returned 404 for user '{USERNAME}'.\n"
            f"This is a known upstream bug: https://github.com/lichess-org/api/issues/667\n"
            f"No games fetched; state unchanged. stats.py still works on "
            f"already-downloaded data."
        )
        sys.exit(0)
    except berserk.exceptions.ResponseError:
        # User doesn't exist — different problem.
        print(
            f"Error: user '{USERNAME}' not found on Lichess.\n"
            f"Check the USERNAME setting in download_games.py.",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    ensure_out_dir()
    state = load_state()
    last_fetch_ms = state.get("last_fetch_ms")
    seen_ids = set(state.get("seen_ids", []))

    if last_fetch_ms is None:
        print(f"No state file yet; downloading ALL rated games for {USERNAME}...")
        since_ms = None
    else:
        # Overlap window: re-fetch a bit, then dedupe by ID
        since_ms = max(0, int(last_fetch_ms) - OVERLAP_MS)
        print(f"Incremental fetch since {since_ms} ms (includes overlap, will dedupe)...")

    client = make_client()

    export_kwargs = {
        "since": since_ms,
        "rated": bool_query(True),
        "as_pgn": False,
        "moves": bool_query(False),
        "tags": bool_query(False),
        "clocks": bool_query(False),
        "evals": bool_query(False),
        "opening": bool_query(False),
    }
    if PERF_TYPES is not None:
        export_kwargs["perf_type"] = PERF_TYPES

    iterator = client.games.export_by_player(USERNAME, **export_kwargs)

    batch = []
    newest_ms_seen = last_fetch_ms if last_fetch_ms is not None else 0
    newly_seen_ids = []

    try:
        for game in iterator:
            gid = game["id"]
            if gid in seen_ids:
                continue

            rec = minimal_record(game, USERNAME)
            batch.append(rec)

            seen_ids.add(gid)
            newly_seen_ids.append(gid)

            if rec["createdAtMs"] > newest_ms_seen:
                newest_ms_seen = rec["createdAtMs"]
    except berserk.exceptions.ResponseError as e:
        if e.status_code == 404:
            _handle_404(client)
        raise

    if not batch:
        print("No new games.")
        return

    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUT_DIR, f"games_{run_stamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2)

    # Save updated state (carry forward seen IDs to prevent re-download)
    save_state(int(newest_ms_seen), state.get("seen_ids", []) + newly_seen_ids)

    print(f"Wrote {len(batch)} new games to {out_path}")
    print(f"Updated state last_fetch_ms={int(newest_ms_seen)}")

if __name__ == "__main__":
    main()
