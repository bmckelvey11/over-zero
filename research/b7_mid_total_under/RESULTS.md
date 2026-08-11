# B7 — "55–65 totals line → bet the under": NULL (conclusive)

Tests betting the under on totals lines in the 55–65 band, plus a pre-registered
feature scan inside it.

Run: `python research/b7_mid_total_under/test_mid_total_under.py`
Data: `data/raw/lines_{2013..2025}.json`, 12,493 usable games / 12,372 after
pushes. Prices from `data/raw/actionnetwork_odds.csv`.

**Verdict: not a bettable edge, and this time the null is conclusive rather than
underpowered.** The band comes in at **51.46%** — *below* break-even, not above
it. At N=4,559 this sample could have detected a true 54.20% rate; it found
nothing close. Unlike B6, this does not leave "maybe with more data" open at
bettable effect sizes.

## The break-even is 52.36%, and that is measured, not assumed

B6 closed by noting its null assumed symmetric juice, and that per-book prices
could in principle lower the under's real hurdle. `actionnetwork_odds.csv` has
real consensus over/under **prices** (4,399 games with both sides, 2018–2019 and
2023–2025). Checked before running anything else:

| totals line | N | median under odds | median over odds | mean under break-even |
|---|---|---|---|---|
| ≤55 | 2515 | −110 | −110 | 52.36% |
| 55–59 | 805 | −110 | −110 | 52.37% |
| 59–62 | 429 | −110 | −110 | 52.35% |
| 62–65 | 291 | −110 | −110 | 52.36% |
| >65 | 359 | −110 | −110 | 52.34% |

**Books do not shade the under on high totals.** The hurdle is flat at ~52.36%
across every band. B6's open question is closed: that caveat does not rescue
either result.

## [A] Sub-bins first — the band is a slice, not a plateau

Computed disjoint sub-bins *before* the aggregate, because 55–65 straddles B6's
bin edges and could have been an average across two regimes.

| cell | N | under% | 95% CI | vs 52.36% |
|---|---|---|---|---|
| 55–59 | 2382 | 50.76% | [48.7, 52.8] | −1.60pp |
| 59–62 | 1167 | 51.16% | [48.3, 54.0] | −1.20pp |
| 62–65 | 1010 | 53.47% | [50.4, 56.5] | +1.11pp |
| **55–65 (aggregate)** | **4559** | **51.46%** | [50.0, 52.9] | **−0.90pp** |
| <55 (below band) | 6593 | 50.17% | [49.0, 51.4] | −2.19pp |
| >65 (above band) | 1220 | 53.28% | [50.5, 56.1] | +0.92pp |

The band is not a plateau. Under% rises monotonically across it (50.76 → 51.16 →
53.47) and keeps rising above it — 55–65 is an arbitrary slice through a
continuous gradient, and it cuts the gradient in a place that averages to a
loser. Only the top sub-bin clears break-even, and it does so by +1.11pp with a
CI spanning [50.4, 56.5].

- vs break-even: z=−1.22, one-sided **p=0.888** (wrong direction entirely).
- Bonferroni over 19 comparisons (B6's 9 priors + 10 here): **p_adj=1.000**.
- Season block-bootstrap 95% CI **[49.49%, 53.23%]**.
- **MDE at N=4,559 is 54.20%.** This is the key number: the sample was powered
  to find a genuinely bettable edge and did not.

## [B] Probit inside the band — flat

Restricted to 55–65: slope **+0.005108** per point (SE 0.006424), z=+0.80,
p=0.4265. B6's full-range slope (+0.003279/pt, z=+2.28) does not survive
restriction to this band. Whatever weak totals-level gradient exists is not
locatable inside 55–65.

## [C] Feature scan inside the band — all 10 cells reported

Candidate pool fixed before running, from `b4_features/INVENTORY.md` (week,
neutral_site, conference_game, home_dog) plus the two line-shape variables the
model already prices (spread, censoring bias). Every cell tested is listed —
none are omitted.

| cell | N | under% | 95% CI | vs BE |
|---|---|---|---|---|
| week ≤ 4 (early) | 1450 | 50.34% | [47.8, 52.9] | −2.02pp |
| week > 4 (late) | 3109 | 51.98% | [50.2, 53.7] | −0.38pp |
| conference game | 2996 | 52.44% | [50.6, 54.2] | +0.08pp |
| non-conference | 1563 | 49.58% | [47.1, 52.1] | −2.78pp |
| home dog | 1592 | 52.83% | [50.4, 55.3] | +0.47pp |
| home favorite | 2967 | 50.72% | [48.9, 52.5] | −1.64pp |
| spread ≤ 7 (close) | 1653 | 53.36% | [50.9, 55.8] | +1.00pp |
| spread > 14 (lopsided) | 1790 | 48.04% | [45.7, 50.4] | −4.32pp |
| censoring bias < 0.25 | 3653 | 52.92% | [51.3, 54.5] | +0.56pp |
| censoring bias ≥ 0.25 | 906 | 45.58% | [42.4, 48.8] | −6.78pp |

Four cells clear break-even in-sample, all by under 1.1pp, none with raw
p < 0.20 (best: spread ≤ 7 at p=0.208), all at **p_adj = 1.000**.

**`neutral_site`: declared but not testable.** `lines_*.json` carries no venue
field, so neutral-site games are not separable from this source. Not tested, and
not counted as a null — flagged so the pre-registered list stays honest.

The two largest effects in the whole table are the *negative* ones, and both are
the floor-bias model talking: censoring bias ≥ 0.25 gives 45.58% under (i.e. a
54.4% **over** rate) and spread > 14 gives 48.04%. This is B6 [C] again — the
under side of a high-bias game is the wrong side of the edge v1 already prices.

## [D] Walk-forward — the one apparent survivor is a single season

Every cell clearing break-even in-sample went through the repo's walk-forward
protocol (decide season t using only seasons ≤ t−1):

| cell | in-sample | walk-forward |
|---|---|---|
| conference game | 52.44% | never bet (prior-seasons rate never cleared) |
| home dog | 52.83% | 55.29% on 170 bets |
| spread ≤ 7 (close) | 53.36% | 51.59% on 818 bets |
| censoring bias < 0.25 | 52.92% | 50.96% on 1144 bets |

The two cells with real walk-forward volume both land below break-even. "Home
dog" at 55.29% is the only apparent survivor and it does not hold up: all 170
bets are **a single season (2025)**, z=+0.77, one-sided **p=0.222**, Wilson 95%
CI **[47.79%, 62.57%]**, season block-bootstrap **[48.96%, 56.34%]**. The
per-season series is 39.66 / 49.49 / 54.29 / 53.15 / 60.00 / 49.11 / 52.63 /
53.85 / 60.33 / 41.03 / 60.00 / 57.96 / 55.29 — swinging 39%–60% with no
stability. The filter only started betting recently because the trailing mean
happened to cross break-even, which is the textbook shape of a cell, not an edge.

## Conclusion

No model change. Consistent with B6 and with the paper's asymmetry claim:
censoring is one-directional, so the under gets nothing from the mechanism, and
the totals level is mostly a proxy for the *absence* of the over edge that
`biasTotals` already prices.

What B7 adds over B6:

1. **The juice question is closed.** Real prices show no under shading at any
   totals level — 52.36% is the true hurdle, so B6's "unless books tilt price"
   caveat is now resolved against the lead.
2. **The null is conclusive, not underpowered.** B6 could only say "no edge
   demonstrable at N=977." At N=4,559 with MDE 54.20%, B7 rules out an edge of
   bettable size in this band.
3. **The band's own framing does not survive.** 55–65 is a slice through a
   monotone gradient, not a plateau; the aggregate is below break-even because
   the slice includes the losing 55–59 region.

Filed alongside `b6_high_total_under/` and `saturation_bias/` as a clean
negative result.

**What would reopen this.** Not another cut of this data — the MDE gap and the
[D] walk-forward collapse are both juice-independent and both point the same
way. It would take a genuinely different mechanism for the under (something
producing one-directional pressure at the scoring ceiling, which
`saturation_bias/` already looked for and did not find), not a new filter on
totals level.
