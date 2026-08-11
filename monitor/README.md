# monitor — edge-decay tracking + walk-forward backtest

Operational truth tools for the [Floor Bias model](../v1/). Two questions a
published anomaly must keep answering: **is the edge still there?** (books
correct once a finding spreads) and **would the strategy have worked without
seeing the future?** (k-fold CV mixes seasons).

```bash
python monitor/run_monitor.py                 # decay tables, 2013–2025
python monitor/run_monitor.py --width 3       # trailing-window width
python monitor/run_walkforward.py             # train ≤ t−1, bet season t
python monitor/run_walkforward.py --threshold 1.75 --min-train 5
```

Files: `monitor.py` (per-season/trailing stats, Wilson CIs, slope trend test),
`run_monitor.py` (decay driver), `run_walkforward.py` (walk-forward backtest).
Estimator core imported from `../v2`.

## run_monitor — is the edge decaying?

If books start pricing censoring, the signature is: probit slope on
`biasTotals` → 0, the bias needed to clear the 52.38% hurdle rises, and the
bias>1.0 over-win% drifts to 50%. The monitor computes each per season and
over trailing windows, with CIs, plus an OLS trend test on the per-season
slope.

Flags:

- `SLOPE~0` — slope 95% CI includes 0 (signal weak/dead in that window).
- `UNPROF` — bias>1.0 win% CI lower bound below the 52.38% breakeven.

**Read flags on trailing windows, not single seasons.** At 20–100 bets/season
the win% CI half-width is ±10–14 pp against an edge of ~4 pp over breakeven,
so per-season `UNPROF` fires routinely on noise; the 3-season window
(~250 bets, ±6 pp) is the smallest honest unit.

Snapshot (2013–2025, run 2026-07-30): every trailing window since 2016-2018
has a positive, significant slope (recent windows ≈ +0.16 to +0.24,
p ≤ 7e-4); trend on the per-season slope is **+0.006/yr, p = 0.55 — no
decay**. The 2018-2020 window is the only one whose win% CI clears breakeven
outright; the rest sit above breakeven on the point estimate with the CI
straddling it, which is what a ~4 pp edge at these Ns looks like.

## run_walkforward — would it have worked in real time?

For each season t: fit the full pipeline (Tobit σ + probit) **only on seasons
< t**, then bet season t. No future data ever enters training — this is the
deployable protocol the k-fold tables can't certify. Two rules:

- **A** (v1 headline rule): bet the over where expected censoring bias > 1.0.
- **B** (k-fold rule): bet the over where trained-probit P(over) > 52.38%.

Note: the *operational* bet rule moved to **bias > 1.75** on 2026-08-11 (see
`bias_bins.py` and MODEL_GUIDE §3). These drivers deliberately keep 1.0 as
their default — the wider bucket has more games and therefore more power to
detect the signal decaying, which is a different question from where to bet.

Result (2013–2025 data, first bet season 2016, run 2026-07-30):

| rule | bets | win% | Wilson 95% | unit% | LR vs breakeven |
|------|------|------|------------|-------|-----------------|
| A: bias > 1.0 | 681 | **56.83%** | [53.1%, 60.5%] | +8.49% | p = 0.020 |
| B: P > 52.38% | 992 | 55.65% | [52.5%, 58.7%] | +6.23% | p = 0.039 |

9/10 test seasons profitable under rule A (2016 the exception). The pooled
Wilson **lower bound clears breakeven** for both rules, and the walk-forward
win rate matches the in-sample headline (56.62%) — the edge is not an
artifact of time-mixed cross-validation.
