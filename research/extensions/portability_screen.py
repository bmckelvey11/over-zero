"""Portability screen — where else does the Floor Bias math pay?

The v1 edge is one instance of a general trade: a market quotes a LATENT mean
but settles on a NONLINEAR function of it, so the quote misses the Jensen gap.
For left-censoring at zero the gap is the paper's

    bias(mu, sigma) = sigma*phi(mu/sigma) - mu*Phi(-mu/sigma)      >= 0

which is exactly the extrinsic value of a zero-strike Bachelier call on the
latent score. This module turns that into a screen that ranks candidate
markets BEFORE any data is bought, using two numbers per market: the implied
mean of each side and the per-side score sigma.

Key portable statistic — the bias-to-noise ratio

    BNR = biasTotals / sigma_settle

sigma_settle is the SD of the settled quantity (the totals forecast error).
A first-order expansion of Phi around the line gives

    edge (in win-probability points) ~= phi(0) * BNR = 0.3989 * BNR

so a -110 market (2.38 pp hurdle) needs BNR >~ 0.060 to be bettable at all.
That single threshold is the screen. `exact` columns replace the expansion
with Monte Carlo over the censored bivariate normal (rho = 0), which is the
honest pure-censoring prediction — v1's realized edge runs ABOVE it (see
MODEL_GUIDE open question 1), so treat `exact` as a floor, not a forecast.

Run:
    python research/extensions/portability_screen.py            # market table
    python research/extensions/portability_screen.py --scaling  # time-slice law
    python research/extensions/portability_screen.py --all

Sigmas for unvalidated markets are documented PRIORS, not fits — the point of
the screen is to rank data-acquisition targets, not to price bets. Anything
outside CFB full-game totals is untested; see docs/EXTENSIONS.md.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "v2"))
from models_v2 import censoring_bias  # noqa: E402
from scipy import stats  # noqa: E402

NORM = stats.norm
PHI0 = float(NORM.pdf(0.0))          # 0.3989 — pp of win prob per unit BNR
MC_DRAWS = 400_000
MC_SEED = 0


def breakeven(price_american: int) -> float:
    """Win rate that breaks even at an American price (-110 -> 0.5238)."""
    p = float(price_american)
    return (-p) / (-p + 100.0) if p < 0 else 100.0 / (p + 100.0)


# ---------------------------------------------------------------------------
# Market specification
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Market:
    """One candidate bet, described by what the two lines imply per side.

    mu_dog/mu_fav : implied points for the weak/strong side over the settlement
                    window (from the market's own spread + total arithmetic).
    sd_dog/sd_fav : latent score SD per side over that window (Tobit sigma).
    settle        : "total" (both sides settle) or "dog" (a dog team total).
    price         : American price assumed available on the over.
    """
    name: str
    mu_dog: float
    mu_fav: float
    sd_dog: float
    sd_fav: float
    settle: str = "total"
    price: int = -110
    tier: str = "prior"              # validated | approx | prior
    note: str = ""
    tags: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class Screen:
    market: Market
    bias_dog: float
    bias_fav: float
    bias: float                      # gap on the settled quantity
    sd_settle: float
    bnr: float
    edge_lin: float                  # pp over 50, first-order
    edge_mc: float                   # pp over 50, Monte Carlo
    hurdle: float                    # pp over 50 required by the price
    margin: float                    # edge_mc - hurdle


def _mc_over_rate(mu_d, mu_f, sd_d, sd_f, settle, draws=MC_DRAWS, seed=MC_SEED):
    """P(settled quantity > line) when the line equals the LATENT mean.

    Realized score per side is max(0, X), X ~ N(mu, sd^2), sides independent.
    This is the pure-censoring prediction with no other mispricing."""
    rng = np.random.default_rng(seed)
    dog = np.maximum(0.0, rng.normal(mu_d, sd_d, draws))
    if settle == "dog":
        return float((dog > mu_d).mean())
    fav = np.maximum(0.0, rng.normal(mu_f, sd_f, draws))
    return float(((dog + fav) > (mu_d + mu_f)).mean())


def _team_bias(mu, sd):
    """Single-side censoring bias — the paper's footnote-4 quantity."""
    z = mu / sd
    return sd * NORM.pdf(z) - mu * NORM.cdf(-z)


def screen_market(m: Market) -> Screen:
    """Bias, bias-to-noise ratio and edge for one candidate market.

    Cross-checked against v2's `censoring_bias` (see `_selftest`) so this stays
    the same arithmetic the validated model uses."""
    bias_dog = _team_bias(m.mu_dog, m.sd_dog)
    bias_fav = _team_bias(m.mu_fav, m.sd_fav)
    if m.settle == "dog":
        bias = bias_dog
        sd_settle = m.sd_dog
    else:
        bias = bias_dog + bias_fav
        sd_settle = float(np.hypot(m.sd_dog, m.sd_fav))
    bnr = bias / sd_settle
    edge_mc = (_mc_over_rate(m.mu_dog, m.mu_fav, m.sd_dog, m.sd_fav,
                             m.settle) - 0.5) * 100.0
    hurdle = (breakeven(m.price) - 0.5) * 100.0
    return Screen(
        market=m, bias_dog=bias_dog, bias_fav=bias_fav, bias=bias,
        sd_settle=sd_settle, bnr=bnr, edge_lin=PHI0 * bnr * 100.0,
        edge_mc=edge_mc, hurdle=hurdle, margin=edge_mc - hurdle,
    )


def _selftest():
    """The screen must reproduce v2's censoring_bias exactly, and must return
    the guide's published anchor (spread 21 / total 41 -> bias 1.11)."""
    m = CANDIDATES[0]
    _, ref_total = censoring_bias(m.mu_dog, m.mu_fav, m.sd_dog, m.sd_fav)
    s = screen_market(m)
    assert abs(s.bias - float(ref_total)) < 1e-9, "diverged from models_v2"
    assert abs(s.bias - 1.11) < 0.02, f"anchor moved: {s.bias:.3f} != 1.11"
    return s.bias


# ---------------------------------------------------------------------------
# Candidate board
# ---------------------------------------------------------------------------
# CFB anchors are this repo's fitted values (MODEL_GUIDE §2): sigma_dog 11.03,
# sigma_fav 11.78 on 12,493 games. Everything else is a documented prior.
# Time-sliced sigmas use the sqrt-t law (see --scaling), which the repo's own
# 1H data confirms: full-game dog SD 12.1 -> 1H 7.7 vs 12.1/sqrt(2) = 8.6.
SIG_D, SIG_F = 11.03, 11.78

CANDIDATES = [
    Market("CFB game total — bias>1.0 cohort (VALIDATED)",
           10.00, 31.00, SIG_D, SIG_F, tier="validated",
           note="v1 baseline: spread 21 / total 41. Walk-forward 56.83%.",
           tags=("cfb", "anchor")),
    Market("CFB game total — bias>1.75 cohort (VALIDATED)",
           6.75, 41.75, SIG_D, SIG_F, tier="validated",
           note="spread 35 / total 48.5. Walk-forward 64.53%.",
           tags=("cfb", "anchor")),
    Market("CFB game total — median game (control)",
           21.00, 31.00, SIG_D, SIG_F, tier="validated",
           note="No qualifying bias; the screen must reject this.",
           tags=("cfb", "control")),
    Market("CFB 1H total — qualifying cohort",
           5.20, 16.10, 7.70, 8.30, tier="approx",
           note="1H sigma from floor_bias_1h README (dog 7.7). Awaiting real 1H lines.",
           tags=("cfb", "time-slice")),
    Market("CFB 1Q total — qualifying cohort",
           2.60, 8.05, 5.52, 5.89, tier="prior",
           price=-115,
           note="sqrt-t sigma; quarter markets are routinely -115/-120.",
           tags=("cfb", "time-slice")),
    Market("CFB dog TEAM total — qualifying cohort",
           10.00, 31.00, SIG_D, SIG_F, settle="dog", tier="prior",
           note="MODEL_GUIDE open question 3: the undiluted instrument.",
           tags=("cfb", "team-total")),
    Market("CFB 1H dog TEAM total",
           5.20, 16.10, 7.70, 8.30, settle="dog", tier="prior", price=-115,
           note="Both amplifiers stacked: short window x single side.",
           tags=("cfb", "team-total", "time-slice")),
    Market("CFB live 4Q remaining total — blowout",
           2.20, 6.60, 5.00, 5.30, tier="prior", price=-115,
           note="Remaining-points market late in a decided game.",
           tags=("cfb", "live")),
    Market("FCS/body-bag game total",
           5.50, 45.00, 12.00, 13.50, tier="prior", price=-115,
           note="Biggest spreads on the board; softest lines, smallest limits.",
           tags=("cfb", "low-tier")),
    Market("NFL game total — biggest dogs",
           18.00, 31.00, 9.50, 10.00, tier="prior",
           note="Sharpest market in sport; floor barely binds.",
           tags=("nfl",)),
    Market("NFL 1Q total",
           4.50, 7.75, 4.75, 5.00, tier="prior", price=-115,
           note="Short window rescues NFL; price is the problem.",
           tags=("nfl", "time-slice")),
    Market("NFL 1H dog TEAM total — big dog",
           9.00, 15.50, 6.70, 7.10, settle="dog", tier="prior", price=-115,
           tags=("nfl", "team-total", "time-slice")),
    Market("CBB game total — biggest mismatch",
           58.00, 88.00, 10.00, 11.00, tier="prior",
           note="Control: mean is ~6 sigma off the floor. Must screen out.",
           tags=("cbb", "control")),
]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def verdict(s: Screen) -> str:
    if s.market.settle == "dog":
        return "NO EDGE (mean-only, see note)"
    if s.market.tags and "control" in s.market.tags:
        return "REJECT (control)" if s.margin <= 0 else "!! control passed !!"
    if s.margin >= 2.0:
        return "PRIORITY"
    if s.margin > 0.0:
        return "marginal"
    return "reject"


def print_board(rows):
    print(f"{'market':<44} {'bias':>6} {'sdSet':>6} {'BNR':>6} "
          f"{'lin':>6} {'exact':>6} {'need':>6} {'edge':>6}  verdict")
    print("-" * 108)
    for s in rows:
        print(f"{s.market.name:<44} {s.bias:6.2f} {s.sd_settle:6.2f} "
              f"{s.bnr:6.3f} {s.edge_lin:6.2f} {s.edge_mc:6.2f} "
              f"{s.hurdle:6.2f} {s.margin:+6.2f}  {verdict(s)}")
    print("\nbias  = Jensen gap on the settled quantity, in points")
    print("BNR   = bias / SD(settled quantity) — the portable statistic")
    print("lin   = phi(0)*BNR, edge in win-% points over 50 (first order)")
    print("exact = Monte Carlo over censored bivariate normals (pure censoring)")
    print("need  = points over 50 required by the assumed price")
    print("edge  = exact - need. BNR ~ 0.060 is breakeven at -110.\n")
    print("Tiers: validated = backtested here; approx = mechanism shown, lines")
    print("missing; prior = sigma is an assumption, nothing tested.\n")
    print("POOLING NOTE — why single-side markets show BNR high but exact ~0:")
    print("  censoring is a MEAN effect. For one censored side, all displaced")
    print("  mass piles at exactly 0, far below the line, so the median and")
    print("  every upper quantile are UNCHANGED: P(max(0,X) > mu) = P(X > mu)")
    print("  = 0.5 exactly. An over/under settles on a quantile, not the mean,")
    print("  so a lone censored side pays nothing. Pooling two sides is what")
    print("  converts the gap into a location shift — the dog's increment")
    print("  lands inside the favorite's noise and can carry the SUM across")
    print("  the line. BNR and the linear column are therefore only valid for")
    print("  POOLED settlements; trust `exact` everywhere.\n")


def print_scaling():
    """How BNR moves as the settlement window shrinks (the sqrt-t law).

    Over a fraction t of a game, mu scales like t but sigma like sqrt(t), so
    z = (mu/sigma)*sqrt(t) falls and the floor binds harder. This is the single
    most useful prediction the model makes about where to look next."""
    print("Time-slice scaling — CFB qualifying game (full-game dog 10.0 / fav 31.0)\n")
    print(f"{'window':<22} {'t':>5} {'muDog':>6} {'sdDog':>6} {'bias':>6} "
          f"{'BNR':>6} {'exact':>6}")
    print("-" * 62)
    for label, t in [("full game", 1.0), ("first half", 0.5),
                     ("first quarter", 0.25), ("one quarter (live)", 0.15),
                     ("final 6 minutes", 0.10), ("final 3 minutes", 0.05)]:
        m = Market(label, 10.0 * t, 31.0 * t,
                   SIG_D * np.sqrt(t), SIG_F * np.sqrt(t))
        s = screen_market(m)
        print(f"{label:<22} {t:5.2f} {m.mu_dog:6.2f} {m.sd_dog:6.2f} "
              f"{s.bias:6.2f} {s.bnr:6.3f} {s.edge_mc:6.2f}")
    print("\nBNR rises monotonically as the window shrinks and asymptotes to")
    print(f"phi(0)*(sd_dog+sd_fav)/hypot(sd_dog,sd_fav) = "
          f"{PHI0 * (SIG_D + SIG_F) / np.hypot(SIG_D, SIG_F):.3f} as t->0.")
    print("DO NOT trust the bottom rows: at small t scores are 0/3/7 lumps and")
    print("the Gaussian latent is a bad approximation. The law justifies moving")
    print("from full game -> half -> quarter, and no further without a discrete")
    print("scoring model (MODEL_GUIDE open question 8).\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scaling", action="store_true",
                    help="print the time-slice scaling law only")
    ap.add_argument("--all", action="store_true", help="print everything")
    args = ap.parse_args()
    _selftest()

    if args.scaling and not args.all:
        print_scaling()
        return

    rows = sorted((screen_market(m) for m in CANDIDATES),
                  key=lambda s: -s.margin)
    print("\nPORTABILITY SCREEN — Gaussian floor-censoring candidates")
    print("Sigmas outside CFB full-game are PRIORS. Ranks targets, not bets.\n")
    print_board(rows)
    if args.all:
        print_scaling()


if __name__ == "__main__":
    main()
