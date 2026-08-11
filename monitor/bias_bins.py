"""Profit by expected-censoring-bias bin, walk-forward.

  python monitor/bias_bins.py [--season 2013 ... 2025] [--min-train 3]
      [--fig docs/figs/bias_bins.png]

Answers two different questions that are easy to conflate:

  DISJOINT BINS      -- "profit by bias bin". Is the edge monotone in bias?
                        Monotonicity is the mechanism check: censoring theory
                        says more expected bias => more mispricing => more
                        over-profit. One bin popping alone is noise.
  CUMULATIVE SWEEP   -- "bias > x" for a range of x. This is the shape of the
                        deployable rule, since you bet a threshold, not a bin.

Both use the same walk-forward protocol as run_walkforward.py: for season t,
fit the pipeline (Tobit sigmas + probit) ONLY on seasons < t, then assign bins
and grade bets in season t. Binning on a full-sample fit would leak test-season
games into the sigmas that define `bias` itself, not merely into the win rate.

Estimator core imported from ../v2; loader/CI/protocol shared with monitor.py
and run_walkforward.py.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2"))
from monitor import _wilson, load_from_raw  # noqa: E402
from run_walkforward import HURDLE, _unit, fit_train  # noqa: E402
from models_v2 import censoring_bias, implied_team_points  # noqa: E402

# Disjoint bin edges. Straddles the two documented thresholds (1.0, 1.75) so
# the standard and high-conviction buckets appear as their own rows.
BIN_EDGES = [0.0, 0.5, 1.0, 1.75, 2.5, np.inf]

# Cumulative thresholds swept for the "bias > x" curve.
SWEEP = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]


def walk_forward(data, years, min_train):
    """Collect every out-of-sample bet: (bias, over_outcome) per graded game.

    Returns bias and outcome arrays pooled over all test seasons, where each
    game was scored by a model that never saw its season.
    """
    bias_all, over_all = [], []
    for t in years[min_train:]:
        tr = [y for y in years if y < t]
        se, te, fp, dp = (np.concatenate([data[y][k] for y in tr])
                          for k in range(4))
        s1, s2, _probit = fit_train(se, te, fp, dp)

        se_t, te_t, fp_t, dp_t = data[t]
        dog_t, fav_t = implied_team_points(se_t, te_t)
        _, bias_t = censoring_bias(dog_t, fav_t, s1, s2)

        nu_t = (fp_t + dp_t) - te_t
        keep = nu_t != 0          # drop pushes: no bet resolves on an exact total
        bias_all.append(bias_t[keep])
        over_all.append((nu_t[keep] > 0).astype(float))
    return np.concatenate(bias_all), np.concatenate(over_all)


def _row(bias, over, sel, label):
    n = int(sel.sum())
    if n == 0:
        return {"label": label, "n": 0, "win": float("nan"),
                "unit": float("nan"), "lo": float("nan"), "hi": float("nan")}
    wins = int(over[sel].sum())
    lo, hi = _wilson(wins, n)
    return {"label": label, "n": n, "win": wins / n,
            "unit": _unit(wins, n), "lo": lo, "hi": hi}


def bin_rows(bias, over):
    rows = []
    for lo_e, hi_e in zip(BIN_EDGES[:-1], BIN_EDGES[1:]):
        sel = (bias > lo_e) & (bias <= hi_e)
        label = f"{lo_e:.2f}-{hi_e:.2f}" if np.isfinite(hi_e) else f">{lo_e:.2f}"
        rows.append(_row(bias, over, sel, label))
    return rows


def sweep_rows(bias, over):
    return [_row(bias, over, bias > x, f">{x:.2f}") for x in SWEEP]


def _print_table(title, rows, note=""):
    print(f"\n{title}")
    if note:
        print(note)
    hdr = f"  {'bias':>12} {'N':>6} {'win%':>8} {'unit%':>9} {'Wilson95':>18}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        if r["n"] == 0:
            print(f"  {r['label']:>12} {0:>6}      n/a       n/a"
                  f" {'n/a':>18}")
            continue
        ci = f"[{r['lo']*100:.1f}, {r['hi']*100:.1f}]"
        edge = "*" if r["lo"] > HURDLE else " "
        print(f"  {r['label']:>12} {r['n']:>6} {r['win']*100:>7.2f}% "
              f"{r['unit']*100:>+8.2f}% {ci:>18}{edge}")
    print("  " + "-" * (len(hdr) - 2))
    print(f"  * = Wilson lower bound clears the {HURDLE*100:.2f}% breakeven")


def make_figure(bins, sweep, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
    be = HURDLE * 100

    # Left: disjoint bins -- the monotonicity / mechanism check.
    labels = [r["label"] for r in bins]
    wins = [r["win"] * 100 for r in bins]
    lo_err = [max(0.0, r["win"] * 100 - r["lo"] * 100) for r in bins]
    hi_err = [max(0.0, r["hi"] * 100 - r["win"] * 100) for r in bins]
    colors = ["#4C72B0" if r["lo"] > HURDLE else "#B0B7C3" for r in bins]
    ax1.bar(labels, wins, color=colors, yerr=[lo_err, hi_err],
            capsize=4, ecolor="#444", width=0.62)
    ax1.axhline(be, color="#C44E52", ls="--", lw=1.4,
                label=f"breakeven {be:.2f}% (-110)")
    for x, r in enumerate(bins):
        if r["n"]:
            ax1.text(x, wins[x] + hi_err[x] + 1.1, f"n={r['n']}",
                     ha="center", fontsize=8.5, color="#333")
    ax1.set_title("Over win rate by expected-bias bin\n(disjoint, walk-forward)",
                  fontsize=11)
    ax1.set_xlabel("expected censoring bias (points)")
    ax1.set_ylabel("over win rate (%)")
    ax1.set_ylim(35, 85)
    ax1.legend(fontsize=8.5, loc="upper left")
    ax1.grid(axis="y", alpha=0.25)

    # Right: cumulative thresholds -- the shape of the deployable rule.
    xs = [float(r["label"].lstrip(">")) for r in sweep]
    ws = [r["win"] * 100 for r in sweep]
    los = [r["lo"] * 100 for r in sweep]
    his = [r["hi"] * 100 for r in sweep]
    ax2.plot(xs, ws, "-o", color="#4C72B0", lw=1.8, ms=5, label="win% (bias > x)")
    ax2.fill_between(xs, los, his, color="#4C72B0", alpha=0.16,
                     label="Wilson 95% CI")
    ax2.axhline(be, color="#C44E52", ls="--", lw=1.4, label=f"breakeven {be:.2f}%")
    for x_t, c in ((1.0, "#55A868"), (1.75, "#8172B2")):
        ax2.axvline(x_t, color=c, ls=":", lw=1.6,
                    label=f"documented rule: bias > {x_t}")
    ax2b = ax2.twinx()
    ax2b.plot(xs, [r["n"] for r in sweep], color="#937860", lw=1.2,
              alpha=0.65, ls="-.")
    ax2b.set_ylabel("bets at threshold (N)", color="#937860", fontsize=9)
    ax2b.tick_params(axis="y", labelcolor="#937860", labelsize=8)
    ax2.set_title("Cumulative threshold sweep: bet the over when bias > x\n"
                  "(CI widens as the sample thins)", fontsize=11)
    ax2.set_xlabel("threshold x (points of expected bias)")
    ax2.set_ylabel("over win rate (%)")
    ax2.legend(fontsize=8, loc="upper left")
    ax2.grid(alpha=0.25)

    fig.suptitle("Floor Bias: profit by expected censoring bias "
                 "(walk-forward, train on seasons < t)", fontsize=12.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    print(f"\nWrote {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, nargs="+",
                    default=list(range(2013, 2026)))
    ap.add_argument("--min-train", type=int, default=3)
    ap.add_argument("--fig", default="docs/figs/bias_bins.png")
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()

    data = load_from_raw(args.season)
    years = sorted(data)
    if len(years) <= args.min_train:
        sys.exit(f"Need > {args.min_train} seasons; have {len(years)}.")

    bias, over = walk_forward(data, years, args.min_train)
    print(f"Walk-forward over seasons {years[args.min_train]}-{years[-1]}: "
          f"{bias.size:,} graded games "
          f"(trained only on seasons < each bet season)")

    bins = bin_rows(bias, over)
    sweep = sweep_rows(bias, over)

    _print_table("PROFIT BY BIAS BIN (disjoint)", bins,
                 note="  Monotone rise across bins = the mechanism; "
                      "a lone spike = noise.")
    _print_table("CUMULATIVE THRESHOLD SWEEP (bias > x)", sweep,
                 note="  Descriptive. The argmax of a swept threshold is "
                      "biased upward -- not a recommendation.")

    best = max((r for r in sweep if r["n"] >= 100), key=lambda r: r["win"])
    print(f"\n  Sweep argmax with N>=100: bias {best['label']} "
          f"({best['win']*100:.2f}%, N={best['n']}). Reported for shape only; "
          f"picking it post hoc would be a multiple-comparisons artifact.")

    if not args.no_fig:
        make_figure(bins, sweep, args.fig)


if __name__ == "__main__":
    main()
