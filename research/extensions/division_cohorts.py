"""Where does the validated CFB edge actually live? Split by division.

The v1 headline (bias > 1.0 -> 56.6% in-sample, 56.8% walk-forward) is quoted
over ALL lined games. CFBD's `homeClassification`/`awayClassification` let us
ask a question the repo has never asked: is the edge uniform across the FBS
market and the cross-division / FCS games that share the same board?

It is not, and the difference is large. This module reports, per cohort:

  * baseline over rate                        (level effect — is the cohort
                                               just priced low overall?)
  * over rate at bias < 0.5 vs bias > 1.0     (the LIFT — differences out any
                                               cohort-level pricing offset)
  * probit slope on biasTotals                (does the signal work in-cohort?)
  * walk-forward: train on seasons < t (pooled, exactly as monitor/ does),
    bet season t restricted to the cohort     (the deployable protocol)

The lift column is the important one: a cohort where totals are simply set too
low would show a high over rate at EVERY bias level and a flat lift. A cohort
where the censoring mechanism is genuinely stronger shows a steep lift.

    python research/extensions/division_cohorts.py
    python research/extensions/division_cohorts.py --threshold 1.75

READ THIS BEFORE ACTING ON THE OUTPUT: this is a post-hoc subgroup split of an
already-published result. Three cohorts were tested, the split was chosen for a
structural reason (division mismatch drives implied dog points toward the
floor) rather than by search, and the walk-forward columns use the honest
protocol — but subgroup analyses of a validated edge are exactly where
false discoveries live. Treat as a research lead, not a betting instruction.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "v2"))
from models_v2 import (  # noqa: E402
    censoring_bias,
    implied_team_points,
    pick_line,
    probit_win_v2,
    tobit_left_censored_v2,
)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
HURDLE = 0.5238


def load_with_class(seasons, raw_dir=RAW_DIR):
    """Same game universe as models_v2.load_raw_seasons, plus the division pair.

    Favorite = negative-spread side (CFBD quotes spreads home-relative), pick'em
    dropped — identical to the frozen loader, verified by reproducing the
    repo's 12,493-game count and sigma_dog/sigma_fav of 11.03/11.78."""
    out = {}
    for season in seasons:
        path = Path(raw_dir) / f"lines_{season}.json"
        if not path.exists():
            continue
        se, te, fp, dp, cl = [], [], [], [], []
        for g in json.loads(path.read_text(encoding="utf-8")):
            hp, ap = g.get("homeScore"), g.get("awayScore")
            if hp is None or ap is None:
                continue
            picked = pick_line(g)
            if picked is None:
                continue
            spread, total = picked
            if spread == 0:
                continue
            fav, dog = (hp, ap) if spread < 0 else (ap, hp)
            se.append(abs(spread))
            te.append(total)
            fp.append(float(fav))
            dp.append(float(dog))
            cl.append(cohort_label(g.get("homeClassification"),
                                   g.get("awayClassification")))
        if se:
            out[season] = (np.array(se), np.array(te), np.array(fp),
                           np.array(dp), np.array(cl))
    return out


COHORTS = ("FBS vs FBS", "FBS vs FCS", "FCS vs FCS")


def cohort_label(home_class, away_class):
    """Division pair as a single label; anything else lands in 'other'."""
    pair = {str(home_class).lower(), str(away_class).lower()}
    if pair == {"fbs"}:
        return "FBS vs FBS"
    if pair == {"fbs", "fcs"}:
        return "FBS vs FCS"
    if pair == {"fcs"}:
        return "FCS vs FCS"
    return "other"


def cohort_masks(cls):
    """The structural cohorts sharing one betting board."""
    masks = {c: (cls == c) for c in COHORTS}
    other = cls == "other"
    if other.any():
        masks["other"] = other
    return masks


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def unit_return(wins, n, risk=110.0, payout=100.0):
    return (wins * payout - (n - wins) * risk) / (n * risk) if n else 0.0


def fit_train(se, te, fp, dp):
    """v1 pipeline on training seasons — same function monitor/ uses."""
    dog_est, fav_est = implied_team_points(se, te)
    s1 = tobit_left_censored_v2(dp, dog_est).sigma
    s2 = tobit_left_censored_v2(fp, fav_est).sigma
    _, bias = censoring_bias(dog_est, fav_est, s1, s2)
    nu = (fp + dp) - te
    keep = nu != 0
    return s1, s2, probit_win_v2((nu > 0).astype(float)[keep], bias[keep])


def in_sample_table(data, threshold):
    years = sorted(data)
    se, te, fp, dp = (np.concatenate([data[y][k] for y in years]) for k in range(4))
    cls = np.concatenate([data[y][4] for y in years])

    s1, s2, _ = fit_train(se, te, fp, dp)
    dog_est, fav_est = implied_team_points(se, te)
    _, bias = censoring_bias(dog_est, fav_est, s1, s2)
    nu = (fp + dp) - te
    keep = nu != 0
    over = (nu > 0).astype(float)

    print(f"In-sample, {se.size:,} games {years[0]}-{years[-1]} "
          f"(pooled sigmas dog={s1:.2f} fav={s2:.2f})\n")
    print(f"{'cohort':<12} {'games':>6} {'base':>7} {'<0.5':>7} "
          f"{'>' + str(threshold):>7} {'lift':>7} {'dogEst':>7} {'dog=0':>6}"
          f"  probit slope")
    print("-" * 88)
    masks = cohort_masks(cls)
    masks["ALL"] = np.ones(se.size, bool)
    for name, m in masks.items():
        k = m & keep
        lo = k & (bias < 0.5)
        hi = k & (bias > threshold)
        lov, hov = over[lo].mean() * 100, over[hi].mean() * 100
        pf = probit_win_v2(over[k], bias[k])
        p = 2 * stats.norm.sf(abs(pf.slope / pf.se_slope))
        print(f"{name:<12} {int(m.sum()):>6} {over[k].mean() * 100:6.2f}% "
              f"{lov:6.2f}% {hov:6.2f}% {hov - lov:+6.2f} "
              f"{dog_est[m].mean():7.2f} {100 * (dp[m] == 0).mean():5.1f}%"
              f"  {pf.slope:+.3f} (SE {pf.se_slope:.3f}) p={p:.1e}")
    print("\nlift = over% at bias>threshold minus over% at bias<0.5, within cohort.")
    print("A pure 'this cohort is priced too low' story predicts lift ~ 0.\n")


def walkforward_table(data, threshold, min_train=3):
    """Train pooled on seasons < t (the deployable protocol), bet season t,
    reporting results separately per cohort."""
    years = sorted(data)
    if len(years) <= min_train:
        sys.exit("not enough seasons")
    tally = {k: [0, 0] for k in COHORTS + ("other", "ALL")}
    for i in range(min_train, len(years)):
        tr = years[:i]
        se_tr, te_tr, fp_tr, dp_tr = (
            np.concatenate([data[y][k] for y in tr]) for k in range(4))
        s1, s2, _ = fit_train(se_tr, te_tr, fp_tr, dp_tr)

        t = years[i]
        se, te, fp, dp, cls = data[t]
        dog_est, fav_est = implied_team_points(se, te)
        _, bias = censoring_bias(dog_est, fav_est, s1, s2)
        nu = (fp + dp) - te
        bet = (bias > threshold) & (nu != 0)
        won = nu > 0
        masks = cohort_masks(cls)
        masks["ALL"] = np.ones(se.size, bool)
        for name, m in masks.items():
            sel = bet & m
            tally[name][0] += int(sel.sum())
            tally[name][1] += int(won[sel].sum())

    print(f"Walk-forward (train seasons < t, bet season t, first bet "
          f"{years[min_train]}), rule: bias > {threshold}\n")
    print(f"{'cohort':<12} {'bets':>6} {'wins':>6} {'win%':>8} "
          f"{'Wilson 95%':>18} {'unit':>8}")
    print("-" * 62)
    for name, (n, w) in tally.items():
        if n == 0:
            print(f"{name:<12} {n:>6}      —")
            continue
        lo, hi = wilson(w, n)
        print(f"{name:<12} {n:>6} {w:>6} {100 * w / n:7.2f}% "
              f"  [{100 * lo:5.1f}, {100 * hi:5.1f}] {100 * unit_return(w, n):+7.1f}%")
    print(f"\nBreakeven at -110 is 52.38%. Cohorts are disjoint and sum to ALL.")
    print("Post-hoc subgroup split — see module docstring before acting.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, nargs="+",
                    default=list(range(2013, 2026)))
    ap.add_argument("--threshold", type=float, default=1.0)
    ap.add_argument("--min-train", type=int, default=3)
    args = ap.parse_args()

    data = load_with_class(args.season)
    if not data:
        sys.exit("No data found in data/raw.")
    in_sample_table(data, args.threshold)
    walkforward_table(data, args.threshold, args.min_train)


if __name__ == "__main__":
    main()
