# v3 — is the over-edge really censoring, or just "low total / lopsided"?

v2 flagged a puzzle: the realized over-edge rises with expected censoring bias
*more steeply* than pure-censoring theory predicts. Since `biasTotals` is high
exactly when `totalsEst` is low and the game is lopsided, the natural suspicion
is that "censoring bias" is a fancy repackaging of "bet the over on low-total
games." v3 tests that head-on.

```bash
python v3/run_v3.py                    # pooled 2013–2025
python v3/run_v3.py --season 2024 2025
```

`models_v3.py` adds feature construction, (multi)variate probit, and an OOS
k-fold bake-off. Shared core (Tobit, censoring bias, Kelly) imported from `../v2`.

---

## Result: the censoring transform is the real signal, not a proxy

### 1. Univariate probit — which single line feature predicts the over?

| feature | slope (std.) | p | pseudo-R² |
|---------|-------------|---|-----------|
| **biasTotals** | **+0.071** | **6e−10** | **0.227%** |
| dogPointEst | −0.065 | 9e−09 | 0.194% |
| spreadEst | +0.056 | 7e−07 | 0.144% |
| totalsEst | −0.026 | 0.024 | 0.030% |

`biasTotals` is the strongest single predictor. The raw total level (`totalsEst`)
is the *weakest* — barely significant. (All pseudo-R² are tiny: game-level
over/under is near coin-flip; a 0.2% edge is what powers a 55–57% win rate.)

### 2. Multivariate — does biasTotals survive controlling for the total level?

| spec | biasTotals | totalsEst | spreadEst |
|------|-----------|-----------|-----------|
| bias + totals | **+0.069 (p=7e−9)** | −0.007 (p=0.58) | — |
| bias + totals + spread | **+0.052 (p=0.013)** | −0.014 (p=0.31) | +0.020 (p=0.31) |

**`biasTotals` stays significant; `totalsEst` and `spreadEst` go insignificant
once it's included.** The dependence runs one way: the total level's weak signal
is fully absorbed by the censoring bias, not vice versa.

### 3. Out-of-sample 5-fold bake-off (bet over where predicted P > 52.38%)

*(Numbers refreshed 2026-07-31; the previous table predated the 2026-07-30 fix
that stores fold win counts instead of reconstructing them from a rounded win
rate. Deterministic at `seed=0`.)*

| spec | bets | win% | unit% | ¼-Kelly | logloss |
|------|------|------|-------|---------|---------|
| v1: biasTotals | 1089 | 55.56% | +6.06% | **+69.9%** | 0.6843 |
| totalsEst only | 4 | 25.00% | −52.27% | −0.2% | 0.7241 |
| bias + totals | 1098 | **56.28%** | **+7.45%** | +66.6% | **0.6837** |
| bias + totals + spread | 1238 | 55.01% | +5.02% | +62.9% | 0.6853 |

Every spec containing `biasTotals` performs the same to within noise;
`bias + totals` is nominally best on win% and log-loss, but by 0.0006 of
log-loss on a shared fold split — the bake-off **cannot distinguish them**.
What it *does* settle is decisive: adding features to `biasTotals` buys
nothing, and "totalsEst only" clears the hurdle 4 times in 12,493 games and
loses money doing it. So v1's single-feature rule is preferred on **parsimony
at equal performance**, not because it sweeps the table.

### 4. Incremental pseudo-R²

- biasTotals over totalsEst alone: **+0.199 pp**
- totalsEst over biasTotals alone: **+0.002 pp**

Decisive: censoring's nonlinearity carries essentially all the predictive power.

---

## Verdict

v3 **refutes the "it's just low totals" worry.** `biasTotals` is not a stand-in
for the total level or the spread — it dominates both, in-sample and out, and
nothing simpler replaces it. The paper's feature is well-chosen and irreducible.

*(Consolidated with v2 as a single ledger of settled and open questions:
[docs/LEDGER.md](../docs/LEDGER.md).)*

The v2 puzzle (theory underpredicts the empirical slope) therefore is **not**
explained by an omitted simple line feature. The residual gap is most likely
either (a) the empirical probit calibrating to realized outcomes more flexibly
than the Gaussian-censoring MC, or (b) genuine extra mispricing in low-scoring
games beyond what normal-tail censoring captures (fat tails / scoring dynamics).
Both need a feature outside the two betting lines, so they're a different study —
v1's rule remains the best line-only strategy.
