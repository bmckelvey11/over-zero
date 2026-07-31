# Ledger of things tried — v2 and v3

*Every hypothesis v2 and v3 put to the data, in one place: what was asked, how
it was tested, what came back, and what it changed. Numbers regenerated
2026-07-31 from a live re-run of `python v2/run_v2.py` and `python v3/run_v3.py`
on 12,493 CFBD games (2013–2025), not copied from the module READMEs — see
[§ Drift](#drift-where-this-ledger-disagrees-with-the-module-readmes).*

The point of a ledger is to stop work being redone. If a question below is
marked **settled**, the finding is reproducible from the command in its row and
re-running it is not research. If it's marked **open**, the row says what would
move it.

## The board

| ID | Question | Method | Headline | Verdict |
|---|---|---|---|---|
| **v2-A** | Are v1's BFGS inverse-Hessian standard errors good enough? | Analytic Tobit score → OPG/BHHH covariance; statsmodels probit | OPG SEs within 7.4% of BFGS, uniformly *larger* | **Settled — immaterial.** v1 stands |
| **v2-B0** | Are favorite and underdog score errors actually independent? | Pearson ρ on both-uncensored games | **ρ = +0.068** (n = 12,025) | **Settled — small and positive** |
| **v2-B1** | Does `biasTotals` depend on ρ? | Analytic argument + censored bivariate-normal MC | Analytic 0.2027; MC 0.1908 (ρ=0) vs 0.1910 (ρ̂) | **Settled — invariant.** Proved, not just measured |
| **v2-B2** | Does ρ move P(over \| bias)? | Theoretical P(over) by bias bin, ρ=0 vs ρ̂ | Columns differ by ≤ 0.004 | **Settled — harmless** |
| **v2-B3** | *(bonus)* Does pure censoring explain the *size* of the edge? | Theory vs empirical probit across bias bins | Theory 0.502→0.523; empirical 0.477→0.559 | **OPEN — theory underpredicts.** Spawned v3, still open |
| **v3-1** | Which single line feature best predicts the over? | Univariate probit, standardized | `biasTotals` +0.0710 (p 5.5e−10, pseudo-R² 0.227%) beats all | **Settled — biasTotals wins** |
| **v3-2** | Does `biasTotals` survive controlling for total and spread? | Multivariate probit | bias stays significant; `totalsEst` → p = 0.57, `spreadEst` → p = 0.31 | **Settled — dominance runs one way** |
| **v3-3** | Does any richer spec beat v1's single feature out of sample? | 5-fold OOS bake-off on log-loss | Nothing beats it *meaningfully*; `totalsEst` alone collapses (4 bets, 25%) | **Settled with a caveat** — see below |
| **v3-4** | Is the censoring *transform* doing the work, or the total level? | Incremental pseudo-R² | bias over totals **+0.199 pp**; totals over bias **+0.002 pp** | **Settled — decisive** |

Two things this board establishes that are worth stating plainly: v1's
methodology is sound as built (v2), and its single feature is irreducible
(v3). One thing it does **not** establish: *why* the edge is roughly twice what
censoring alone predicts (v2-B3). That is the only genuinely open item here.

---

## v2 — were v1's two methodological caveats load-bearing?

```bash
python v2/run_v2.py            # pooled 2013–2025
```

### v2-A — analytic standard errors vs the BFGS approximation

v1 read SEs off the BFGS optimizer's inverse-Hessian approximation. v2 derives
the analytic score of the Tobit log-likelihood and builds the covariance from
the outer product of gradients (OPG/BHHH). Params `[α, β, log σ]`, `μ = α + βx`:

| | uncensored (y>0), z=(y−μ)/σ | censored (y=0), a=μ/σ, λ=φ(a)/Φ(−a) |
|--|--|--|
| ∂ℓ/∂μ | z/σ | −λ/σ |
| ∂ℓ/∂log σ | z²−1 | a·λ |

The optimizer used this exact gradient and converged to the same σ as v1, which
validates the derivation independently of the SE question.

| Parameter | OPG (analytic) | BFGS (v1) | Ratio |
|---|---|---|---|
| Tobit dog α | 0.3903 | 0.3634 | 1.074 |
| Tobit dog β | 0.0172 | 0.0166 | 1.036 |
| Tobit fav α | 0.5352 | 0.5239 | 1.022 |
| Tobit fav β | 0.0153 | 0.0152 | 1.007 |

Fitted: σ_dog = 11.0306 (α +0.3677, β 0.9825, 437 censored), σ_fav = 11.7751
(α −0.0916, β 1.0103, 31 censored). Probit slope **+0.1762, SE 0.0284,
p = 5.5e−10**; season-clustered SE 0.0200 (p ≈ 1e−18, 13 clusters, indicative).

**Verdict: settled, immaterial.** OPG is uniformly larger — i.e. v1 was if
anything slightly *anti*-conservative — but the largest gap is 7.4% on a
p-value with ten orders of magnitude of headroom. No conclusion moves.

### v2-B — dropping the independence assumption

v1 assumed cov(δ_fav, δ_dog) = 0. Measured: **ρ = +0.068** on 12,025
both-uncensored games (v2-B0). Small, positive, and worth propagating properly
rather than waving at.

**v2-B1 — `biasTotals` is invariant to ρ.** This is a proof, not a
measurement: the expected censoring bias is a *marginal* expectation,
`E[max(0,x)] − μ`, and by linearity of expectation it cannot depend on the
joint correlation. Monte Carlo over 2,000 games confirms:

| Quantity | Value |
|---|---|
| Analytic `biasTotals` (ρ-free formula) | 0.2027 |
| MC, ρ = 0 | 0.1908 |
| MC, ρ = +0.07 | 0.1910 |

ρ = 0 and ρ = 0.068 give the same answer to 4 decimal places; the residual gap
to the analytic value is MC sampling noise. **The trading signal is untouched.**

**v2-B2 — the win probability barely moves.** ρ can only reshape the *variance*
of the totals error, so it could in principle shift P(over | bias):

| bias bin | N | empirical | probit | theory ρ=0 | theory ρ̂ |
|---|---|---|---|---|---|
| (−1.00, 0.25] | 1518 | 0.470 | 0.477 | 0.502 | 0.502 |
| (0.25, 0.50] | 271 | 0.535 | 0.496 | 0.504 | 0.504 |
| (0.50, 1.00] | 133 | 0.526 | 0.518 | 0.509 | 0.508 |
| (1.00, 1.75] | 47 | 0.511 | 0.559 | 0.523 | 0.519 |

Last two columns differ by ≤ 0.004. **Verdict: settled, harmless.** And there
is a structural reason v1 was safe even in principle — its probit is fit on
*realized* outcomes, which already embed the true correlation. Independence
only ever entered the theoretical derivation, never the empirical edge.

**v2-B3 — the bonus finding, and the one thing still open.** Compare the two
middle columns above. Pure-censoring theory predicts the over-rate climbing
0.502 → 0.523 across the bins; the empirical probit climbs 0.477 → 0.559. The
direction is right and the *magnitude is not*: the realized edge is roughly
twice what censoring alone accounts for.

This is the thread that runs through everything downstream. It spawned v3,
survived v3, and is now [MODEL_GUIDE open question 1](MODEL_GUIDE.md#10-open-questions).
[EXTENSIONS §2a](EXTENSIONS.md#2a-the-pooling-theorem--censoring-alone-does-not-pay-on-a-single-side)
supplies the first clean experiment for it: because pure censoring predicts
*exactly* 50% on a single-side team total, any edge measured there is the
residual, isolated from censoring for the first time.

### v2 net

Both caveats checked, both immaterial. v1's strategy is unchanged: **680 bets,
56.62%, +8.09% per unit (LR vs breakeven p = 0.027)**; at the strong threshold
**227 bets, 63.44%, +21.11% (p = 0.001)**.

---

## v3 — is the edge really censoring, or just "low total / lopsided"?

```bash
python v3/run_v3.py            # pooled 2013–2025
```

`biasTotals` is high exactly when the total is low and the game lopsided, so
the natural suspicion is that it repackages "bet the over on low-total games."
Four attacks, all of which it survives.

**v3-1 — univariate probit** (standardized, in-sample):

| Feature | Slope | SE | p | pseudo-R² |
|---|---|---|---|---|
| **biasTotals** | **+0.0710** | 0.0114 | **5.5e−10** | **0.227%** |
| dogPointEst | −0.0650 | 0.0113 | 8.6e−09 | 0.194% |
| spreadEst | +0.0559 | 0.0113 | 7.5e−07 | 0.143% |
| totalsEst | −0.0258 | 0.0113 | 2.2e−02 | 0.030% |

The raw total level is the *weakest* of the four and barely significant. All
pseudo-R² are tiny because game-level over/under is near coin-flip — 0.2% is
what a 55–57% win rate looks like.

**v3-2 — multivariate.** Does bias survive its own correlates?

| Spec | biasTotals | totalsEst | spreadEst |
|---|---|---|---|
| bias + totals | **+0.0691 (p 6.6e−09)** | −0.0067 (p 0.57) | — |
| bias + totals + spread | **+0.0520 (p 0.012)** | −0.0145 (p 0.30) | +0.0201 (p 0.31) |

Bias stays significant throughout; both raw lines go insignificant once it is
included. The dependence runs one way — the total level's weak signal is
absorbed by the censoring bias, not the reverse.

**v3-3 — 5-fold OOS bake-off**, bet the over where predicted P > 52.38%:

| Spec | Bets | Win% | Unit% | ¼-Kelly | Log-loss |
|---|---|---|---|---|---|
| v1: biasTotals | 1089 | 55.56% | +6.06% | +69.9% | 0.6843 |
| totalsEst only | 4 | 25.00% | −52.27% | −0.2% | 0.7241 |
| bias + totals | 1098 | **56.28%** | **+7.45%** | +66.6% | **0.6837** |
| bias + totals + spread | 1238 | 55.01% | +5.02% | +62.9% | 0.6853 |

**Read this one carefully — it is the caveat in the board.** On current code
the single-feature rule does *not* sweep: `bias + totals` edges it on win%
(+0.72 pp) and log-loss (0.6837 vs 0.6843). Those margins are noise — 0.0006 of
log-loss on a shared fold split — so the honest reading is that **the bake-off
cannot distinguish `biasTotals` from `bias + totals`, and decisively rejects
everything without bias in it**. `totalsEst` alone clears the hurdle 4 times in
12,493 games and loses money doing it. The case for v1's single feature is
parsimony at equal performance, which is a good case; it is not "wins on every
metric" (see [§ Drift](#drift-where-this-ledger-disagrees-with-the-module-readmes)).

**v3-4 — incremental pseudo-R²**, the cleanest statement of the whole module:

- `biasTotals` added on top of `totalsEst` alone: **+0.199 pp**
- `totalsEst` added on top of `biasTotals` alone: **+0.002 pp**

A hundred-to-one ratio. The censoring *transform* — the nonlinearity — carries
essentially all the predictive power, not the total level it is built from.

### v3 net

The "it's just low totals" worry is **refuted**. `biasTotals` dominates the raw
lines in-sample and out, and nothing simpler replaces it. Note what this does
*not* do: it leaves v2-B3 exactly where it was. The residual gap is not
explained by an omitted simple line feature, so it needs a feature outside the
two betting lines — a different study, and still open.

---

## Drift — where this ledger disagrees with the module READMEs

The ledger was rebuilt from a live re-run, and one number set has moved since
`v3/README.md` was written. The bake-off is deterministic (`seed=0`), so this
is not run-to-run noise — the README predates the 2026-07-30 fix commits
(notably the one replacing `round(win_rate × n_bets)` with a stored win count,
which changes reported win counts and unit returns).

| Row | v3/README | Current code |
|---|---|---|
| v1: biasTotals | 1053 bets, 55.46%, +5.88%, LL 0.6848 | 1089, 55.56%, +6.06%, LL 0.6843 |
| totalsEst only | 16 bets, 31.25% | 4, 25.00% |
| bias + totals | 1100, 55.36%, +5.69%, LL 0.6851 | 1098, **56.28%**, +7.45%, LL **0.6837** |

The module's *conclusion* is unaffected — bias is irreducible, raw totals are
useless — but its sentence "v1's single-feature rule wins on every metric (best
win%, best log-loss)" is no longer true of the code in the repo, and has been
corrected in place. Everything else in v2 and v3 reproduced within rounding
(v2's ρ moved +0.067 → +0.068 on 12,025 vs 11,976 both-uncensored games).

## What v2 and v3 did *not* test

Recorded so the settled rows above aren't read as broader than they are:

- **Neither is a walk-forward.** Both use randomized k-fold, which mixes time.
  The deployable-protocol check lives in [monitor/](../monitor/).
- **v3's bake-off searched only line-derived features** — total, spread,
  implied dog points. Nothing about weather, pace, injuries or team identity;
  those were tried later in [research/b4_features/](../research/b4_features/).
- **v2-B2 is a theory-vs-theory comparison** at two ρ values. It shows ρ is
  harmless; it does not validate the Gaussian model itself, which remains an
  approximation to discrete 0/3/7 scoring (open question 8).
- **Both are in-sample on the same 2013–2025 CFBD sample** used to fit σ, so
  they inherit its book-selection and coverage properties.

## Not in this ledger

Other modules keep their own records: [v1/](../v1/) (frozen baseline),
[saturation_bias/](../saturation_bias/) (under-side negative result),
[floor_bias_1h/](../floor_bias_1h/) (first-half, awaiting real lines),
[monitor/](../monitor/) (walk-forward + decay), [research/](../research/)
(track B: features, team σ, snapshots, data blockers), and
[research/extensions/](../research/extensions/) (portability, division
cohorts). [REVIEW.md](../REVIEW.md) is the audit of all of it.
