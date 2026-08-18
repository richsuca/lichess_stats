#!/usr/bin/env python3
import glob
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

DATA_DIR = "lichess_data"

# Map your stored perf string to display name
PERF_DISPLAY = {
    "blitz": "Blitz",
    "rapid": "Rapid",
    "bullet": "Bullet",
    "classical": "Classical",
    "ultraBullet": "UltraBullet",
}


def ms_to_yyyymm(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m")


def load_all_games(data_dir: str):
    """
    Loads all games_*.json batches in a directory.
    De-dupes by 'id' so overlap downloads don't double count.
    """
    paths = sorted(glob.glob(os.path.join(data_dir, "games_*.json")))
    games_by_id = {}

    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            batch = json.load(f)
        for g in batch:
            gid = g["id"]
            # Keep the latest record if duplicates exist (should be identical anyway)
            games_by_id[gid] = g

    return list(games_by_id.values()), paths


def compute_monthly_stats(games):
    """
    Returns:
      stats[perf][yyyymm] = dict(games=N, W=w, L=l, D=d)
    """
    stats = defaultdict(
        lambda: defaultdict(lambda: {"games": 0, "W": 0, "L": 0, "D": 0})
    )

    for g in games:
        perf = g.get("perf") or "unknown"
        month = ms_to_yyyymm(int(g["createdAtMs"]))
        res = g.get("result", "D")

        bucket = stats[perf][month]
        bucket["games"] += 1
        if res in ("W", "L", "D"):
            bucket[res] += 1
        else:
            # unexpected -> treat as draw so totals still line up
            bucket["D"] += 1

    return stats


def format_section(perf_key: str, months_dict: dict) -> str:
    # Sort months ascending
    months = sorted(months_dict.keys())

    display = PERF_DISPLAY.get(perf_key, perf_key.capitalize())
    lines = []
    lines.append(f"{display} (All)")
    lines.append("-----------")

    for m in months:
        d = months_dict[m]
        total = d["games"]
        w, l, dr = d["W"], d["L"], d["D"]
        win_pct = (100.0 * w / total) if total else 0.0
        lines.append(f"{m}: {total} games | W:{w} L:{l} D:{dr} | Win%: {win_pct:.1f}%")

    return "\n".join(lines)


def main():
    games, paths = load_all_games(DATA_DIR)
    if not paths:
        print(f"No games_*.json files found in {DATA_DIR}/")
        return

    stats = compute_monthly_stats(games)

    # Print header
    print("Monthly Stats - Combined")
    print("========================")
    print()

    # Print perf sections in a sensible order, then everything else
    preferred_order = ["blitz", "rapid", "bullet", "classical", "ultraBullet"]
    printed = set()

    for perf in preferred_order:
        if perf in stats:
            print(format_section(perf, stats[perf]))
            print()
            printed.add(perf)

    # Any remaining perfs
    for perf in sorted(stats.keys()):
        if perf in printed:
            continue
        print(format_section(perf, stats[perf]))
        print()

    # Optional: quick totals
    # print(f"Loaded {len(games)} unique games from {len(paths)} files.")


if __name__ == "__main__":
    main()
