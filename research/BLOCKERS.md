# Blockers log

Dated entries. Format: `## YYYY-MM-DD — <phase>` then what was attempted,
what is blocked, and a recommendation.

## 2026-07-30 — B4.2 (residual-feature probit)

**Attempted:** Write and run `research/b4_features/probit_features.py` (multivariate probit with 4 features from B4.1).

**Blocked:** `fcs_dog` feature has zero variance — all 12,493 joined games (post-lines filter) have `fcs_dog=0`.

**Evidence:**
- Joined games: 12,493 with complete score/line/game data (2013–2025)
- `fcs_dog` feature statistics: mean=0.0000, std=0.0000, unique values=[0.0]
- Direct count: "FCS games in lines with spread: 0" across all years
- Root cause: FCS opponents exist in `games_*.json` (e.g., College of Idaho, Valley City State; ~1.4–1.5% of raw records), but carry no betting lines. After `pick_line` filters for games with both spread and overUnder, no FCS dogs survive to the join.
- B4.1's "available" determination ran on `games_2024.json` alone (awayConference None in 53/3747 ≈ 1.4%), did not recheck post-join.

**Impact:**
- Script crashes: `MissingDataError: exog contains inf or nans` (standardization of zero-variance column → NaN)
- Cannot compute full spec fit; checklist questions (any feature *SIG*? biasTotals shift?) cannot be answered
- Base spec fit succeeds and matches expected: `biasTotals +0.0710 (SE 0.0081)`, confirming upstream pipeline is correct

**Unblocking options** (brief authorizes none; pick one):
1. **Drop to 3 features:** Use only `[week, neutralSite, conferenceGame]`, set `BONFERRONI_P = 0.05/3 = 0.0167`
2. **Substitute `home_dog`:** Replace `fcs_dog` with the already-computed `home_dog` (1 if spread > 0, 0 otherwise; available and non-constant in full set)
3. **Report as inestimable:** Run full spec with 3 features, explicitly note `fcs_dog` dropped due to zero variance, leave threshold at 0.0125

Each choice alters the prespecified 4-feature budget or the Bonferroni denominator — none is transparent without intervention. Recommend clarifying with the research plan owner before proceeding.
