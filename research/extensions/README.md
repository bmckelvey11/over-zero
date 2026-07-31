# extensions — where else does this math pay?

Answers [MODEL_GUIDE open question 7](../../docs/MODEL_GUIDE.md#10-open-questions)
("does the mechanism travel?"). Full writeup with the reasoning, the candidate
board and the non-football markets: **[docs/EXTENSIONS.md](../../docs/EXTENSIONS.md)**.

```bash
python research/extensions/portability_screen.py --all   # candidate board + √t scaling law
python research/extensions/division_cohorts.py           # split the CFB edge by division
```

## `portability_screen.py`

Screens candidate markets *before* any data is bought. The model restated
generally: a market quotes a latent mean but settles on a nonlinear function
of it, so the quote misses the Jensen gap — which for a floor at zero is
exactly the extrinsic value of a zero-strike Bachelier call.

The portable statistic is the **bias-to-noise ratio**, `BNR = bias / SD(settled
quantity)`. A first-order expansion gives edge ≈ `φ(0)·BNR`, so −110 needs
BNR ≳ 0.060, −115 needs ≳ 0.088, −120 needs ≳ 0.114. CFB's validated cohort
sits at 0.069.

Two results from the screen:

- **Pooling theorem.** Single-side settlements (dog team totals) earn exactly
  zero under pure censoring: displaced mass piles at 0, below the line, so
  `P(max(0,X) > μ) = P(X > μ) = 0.5` — the mean moves, the median doesn't.
  Pooling two sides is what converts the gap into a quantile shift. This
  contradicts open question 3's premise; the guide has been corrected.
- **√t scaling law.** Over a fraction `t` of a game μ scales like `t` but σ
  like `√t`, so BNR rises monotonically as the window shrinks (0.069 full game
  → 0.117 half → 0.177 quarter). Confirmed by the repo's own 1H sigmas. Breaks
  down at small `t` where scores are 0/3/7 lumps.

Sigmas outside CFB full-game are **documented priors, not fits** — this ranks
data-acquisition targets, not bets. `--scaling` prints the scaling table alone.
A self-test asserts the screen reproduces `models_v2.censoring_bias` and the
guide's published anchor (spread 21 / total 41 → bias 1.11).

## `division_cohorts.py`

CFBD tags each game's division and the repo had never split on it. Under the
same walk-forward protocol that produced the headline (train pooled on seasons
< t, bet season t):

| Cohort | Bets | Win% | Unit |
|---|---|---|---|
| FBS vs FBS | 268 | 50.00% | −4.5% |
| FBS vs FCS | 328 | 59.45% | +13.5% |
| FCS vs FCS | 85 | 68.24% | +30.3% |
| ALL (headline) | 681 | 56.83% | +8.5% |

Not a level effect: baseline over rates are ~49% in every cohort, and the
within-cohort **lift** (over% at bias > 1.0 minus over% at bias < 0.5) is
+2.0 / +15.6 / +20.5 respectively. The probit slope is positive and
significant in all three — the mechanism is real on the FBS board too, it just
doesn't clear the vig there.

**This is a post-hoc subgroup split of a published result.** Three cohorts, the
split chosen structurally rather than by search, surviving the honest protocol
— but read the caveats in `docs/EXTENSIONS.md §3` before it changes anything
you bet. It is flagged in the guide's failure modes, not applied to the rule.

Both scripts import the estimator core from `../../v2/models_v2.py`; v1 stays
frozen. `division_cohorts.py` reproduces the repo's published 12,493-game
count, pooled sigmas (11.03 / 11.78) and walk-forward headline (681 bets,
56.83%, +8.5%), which is how its loader is verified against the frozen one.
