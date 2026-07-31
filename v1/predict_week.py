"""Fit the Arscott (2022) pipeline on historical seasons, then apply it to a
future week's lines (no scores yet) to produce over/under picks.

Run:  python v1/predict_week.py --fit-seasons 2015 2016 ... 2025 \
          --raw data/raw/lines_2026_week1.json --book DraftKings
"""

import argparse
import json
from pathlib import Path

import numpy as np

from censoring_bias import censoring_bias, fit_pipeline, implied_team_points
from run_on_project_data import DEFAULT_CSV, load

REPO = Path(__file__).resolve().parents[1]


def load_future_lines(path, book):
    """Extract home-relative spread/total for one book from a lines_{...}.json
    file with unplayed games (no scores). Skips games missing that book,
    missing spread/total, or pick'em (spread == 0)."""
    games = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for g in games:
        line = next((l for l in (g.get("lines") or [])
                     if l.get("provider") == book), None)
        if line is None:
            continue
        spread, total = line.get("spread"), line.get("overUnder")
        if spread is None or total is None or float(spread) == 0:
            continue
        rows.append({
            "game_id": g.get("id"),
            "home_team": g.get("homeTeam"),
            "away_team": g.get("awayTeam"),
            "spread": float(spread),   # home-relative, neg = home favored
            "total": float(total),
        })
    return rows


def main():
    ap = argparse.ArgumentParser(
        description="Fit on historical seasons, predict a future week's overs")
    ap.add_argument("--fit-csv", default=str(DEFAULT_CSV))
    ap.add_argument("--fit-seasons", type=int, nargs="+", required=True,
                     help="historical seasons to fit the pipeline on")
    ap.add_argument("--raw", required=True,
                     help="path to lines_{...}.json for the target week (unplayed)")
    ap.add_argument("--book", default="DraftKings",
                     help="sportsbook to read spread/total from (no consensus "
                          "book exists this far from kickoff)")
    ap.add_argument("--hurdle", type=float, default=0.5238,
                     help="break-even win-prob threshold for -110 pricing")
    args = ap.parse_args()

    spread_est, totals_est, fav_points, dog_points = load(
        Path(args.fit_csv), args.fit_seasons
    )
    n = spread_est.size
    print(f"Fit on {n:,} games from seasons {args.fit_seasons}")
    if n < 250:
        print("Warning: small fit sample; sigmas/probit may be unstable.")
    fit = fit_pipeline(spread_est, totals_est, fav_points, dog_points)

    rows = load_future_lines(args.raw, args.book)
    print(f"Loaded {len(rows)} games with {args.book} lines from {args.raw}\n")
    print("NOTE: lines captured well before kickoff (opening lines), not "
          "closing lines the model was fit against historically -- treat "
          "as illustrative, not a validated edge.\n")

    spread_arr = np.array([abs(r["spread"]) for r in rows])
    total_arr = np.array([r["total"] for r in rows])
    dog_est, fav_est = implied_team_points(spread_arr, total_arr)
    _, bias_totals = censoring_bias(
        dog_est, fav_est, fit.tobit_dog.sigma, fit.tobit_fav.sigma
    )
    win_probs = fit.probit.win_prob(bias_totals)

    print(f"{'home':<20} {'away':<20} {'total':>6} {'bias':>6} {'P(over)':>8} pick")
    picks = 0
    for r, bias, p in zip(rows, bias_totals, win_probs):
        pick = "OVER" if p > args.hurdle else ""
        if pick:
            picks += 1
        print(f"{r['home_team']:<20} {r['away_team']:<20} {r['total']:>6.1f} "
              f"{bias:>6.2f} {p*100:>7.2f}% {pick}")
    print(f"\n{picks}/{len(rows)} games clear the {args.hurdle*100:.2f}% hurdle")


if __name__ == "__main__":
    main()
