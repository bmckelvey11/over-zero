# B5.1: Team-σ walk-forward comparison — Results

## Command

```
python research/b5_team_sigma/team_sigma.py
```

## Output (verbatim)

```
K=30: mean OOS logloss improvement (pooled - team) = -1.38 x1e-4  season-block bootstrap 95% [-2.76,-0.11] x1e-4  (10,255 games)
K=15: mean OOS logloss improvement (pooled - team) = -2.02 x1e-4  season-block bootstrap 95% [-3.75,-0.34] x1e-4  (10,255 games)
K=60: mean OOS logloss improvement (pooled - team) = -0.87 x1e-4  season-block bootstrap 95% [-1.99,+0.04] x1e-4  (10,255 games)

VERDICT (K=30): TEAM-SIGMA HURTS OOS
```

## Checklist

1. **CI excludes 0 at K=30?** Yes — 95% CI is [-2.76, -0.11] x1e-4, entirely below 0. This means the improvement (pooled minus team) is significantly *negative*: team-σ is significantly *worse* than pooled-σ out of sample, not better.
2. **Same sign across K=15/60?** Yes for the point estimates — all three K values (15, 30, 60) give a negative mean improvement (-2.02, -1.38, -0.87 x1e-4), i.e. team-σ underperforms pooled-σ at every shrinkage level tested. Note the K=60 CI is [-1.99, +0.04] x1e-4, which straddles zero — so at the weakest shrinkage (largest K, most pooling toward the pooled estimate) the direction is consistent but not statistically significant.
3. **Verdict:** TEAM-SIGMA HURTS OOS (K=30, primary).

Because the result is not an improvement, the prespecified follow-up note (rerun the BET simulation) is not added — the brief gates that note on an improved result, which this is not.

## Caveat

Team σ estimated on uncensored games only (mild truncation); shrinkage constant K is games-count prior weight, K=30 ≈ 2.5 seasons.
