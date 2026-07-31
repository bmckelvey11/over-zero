# Where else does this math pay? — portability brainstorm

*2026-07-31. Answers [MODEL_GUIDE §10 open question 7](MODEL_GUIDE.md#10-open-questions)
("does the mechanism travel?") properly rather than in one line. Two theory
results and one empirical result came out of writing it; they change the
research ranking, and one of them contradicts open question 3.*

Reproduce every number here with:

```bash
python research/extensions/portability_screen.py --all   # candidate board + scaling law
python research/extensions/division_cohorts.py           # the empirical finding
```

---

## 1. What the model actually is, stated generally

Strip the football off and Floor Bias is one instance of a generic trade:

> **A market quotes a latent quantity but settles on a nonlinear function of
> it. The quote misses the Jensen gap.**

For left-censoring at zero the gap is the paper's

```
bias(μ, σ) = σ·φ(μ/σ) − μ·Φ(−μ/σ) ≥ 0
```

which is **exactly the extrinsic value of a zero-strike Bachelier call** on
the latent score: `E[max(0,X)] = μ·Φ(μ/σ) + σ·φ(μ/σ)`, intrinsic value `μ`,
and the difference is the formula above. The repo has been trading an option
the sportsbook priced as a forward.

That reframing is what makes the model portable, because it names the four
conditions a candidate market must satisfy. All four, not three:

| # | Condition | Why it bites |
|---|---|---|
| 1 | **A kink or bound in the settlement function** | No curvature, no gap |
| 2 | **The quote sits within ~1σ of the kink** | At μ/σ > 2 the gap is < 0.05σ — unbettable at any price |
| 3 | **The quoted number is *derived*, not fitted** | If the book fits realized outcomes directly, the gap is already baked in. CFB works because implied team points are a by-product of two *other* liquid lines that nobody arbitrages |
| 4 | **The gap moves a *quantile*, not just the mean** | See §2 — this is the one everybody skips, and it kills the market the guide currently calls "purest" |

Conditions 1–2 are about the sport. Condition 3 is about market structure and
is where most of the money is. Condition 4 is about the payoff and is where
most of the *mistakes* are.

### The portable statistic

Define the **bias-to-noise ratio**

```
BNR = bias / SD(settled quantity)
```

A first-order expansion of Φ around the line gives edge ≈ `φ(0)·BNR` =
`0.399·BNR` in win-probability points. So:

- **−110 (2.38 pp hurdle) needs BNR ≳ 0.060.**
- **−115 (3.49 pp) needs BNR ≳ 0.088.**
- **−120 (4.55 pp) needs BNR ≳ 0.114.**

CFB's validated cohort sits at BNR = 0.069 — barely over the −110 line, which
is exactly why the edge is real but thin, and why the price filter in the
playbook is not optional. This single number is the screen: compute it from
two priors (implied means, score σ) before spending a dollar on data.

## 2. Two theory results that fell out of the screen

### 2a. The pooling theorem — censoring alone does *not* pay on a single side

`MODEL_GUIDE` open question 3 proposes underdog **team totals** as "the purest
expression of the mechanism… the censoring bias undiluted by the favorite's
noise." Under pure censoring that is backwards. The dog team total earns
**exactly zero**:

```
P(max(0,X) > μ)  =  P(X > μ)  =  0.5     for any μ > 0
```

Censoring is a **mean** effect. Every unit of displaced mass piles up at
exactly 0 — far *below* the line — so the median and every upper quantile are
untouched. An over/under settles on a quantile, not on the mean. Verified
directly: for μ = 10, σ = 11.03, censoring lifts the mean by +1.09 points and
moves P(over) by 0.0004.

Pooling two sides is what converts the mean gap into a location shift: the
dog's censoring increment lands *inside the favorite's noise*, so it can carry
the **sum** across the line. That is worth +1.7 pp, and it is the whole
mechanism.

| Settlement | bias | BNR | exact edge |
|---|---|---|---|
| CFB game total (pooled) | 1.11 | 0.069 | **+1.76 pp** |
| CFB dog team total (single side) | 1.09 | 0.099 | **−0.01 pp** |
| CFB 1H dog team total (single side) | 1.15 | 0.149 | **−0.01 pp** |

**Consequences.** (i) BNR and the linear approximation are valid *only* for
pooled settlements — trust the Monte Carlo column. (ii) Open question 3 should
be rewritten. It is still worth running, but as a **diagnostic, not an edge
hunt**: pure censoring predicts exactly 50% on dog team totals, so if a
team-totals backtest shows an edge, that edge is *by construction* the
unexplained residual of open question 1 (why realized ≈ 2× predicted), cleanly
separated from censoring for the first time. That makes it a better
experiment than it was, for a worse reason.

### 2b. The √t scaling law — shorter windows bind harder

Over a fraction `t` of a game, μ scales like `t` but σ like `√t`, so
`z = (μ/σ)√t` falls and the floor binds harder. The repo's own 1H data
confirms the law (full-game dog SD 12.1 → 1H 7.7, vs 12.1/√2 = 8.6).

| Window | t | μ_dog | σ_dog | bias | BNR | exact edge |
|---|---|---|---|---|---|---|
| full game | 1.00 | 10.00 | 11.03 | 1.11 | 0.069 | +1.76 pp |
| first half | 0.50 | 5.00 | 7.80 | 1.33 | 0.117 | +3.50 pp |
| first quarter | 0.25 | 2.50 | 5.51 | 1.43 | 0.177 | +5.65 pp |
| live, one quarter left | 0.15 | 1.50 | 4.27 | 1.42 | 0.228 | +7.61 pp |

BNR rises monotonically and asymptotes to 0.564 as t → 0. **Do not believe the
tail**: at small t scores are 0/3/7 lumps and the Gaussian latent is a bad
approximation (open question 8), while quarter markets are priced −115/−120,
which eats 3.5 pp of the 5.65. The law justifies moving full game → half →
quarter and no further without a discrete scoring model.

The important corollary is that **live/in-game totals are the theoretical
maximum** of this family: as the clock runs down in a decided game, remaining
implied points march toward the floor and BNR climbs the table above. It is
also the hardest to execute (fastest lines, lowest limits, worst prices).

## 3. The empirical finding: it already travels — one rung *down*, not sideways

The most promising extension turned out not to be another sport. CFBD tags
every game's division, and the repo has never split on it. Under the **exact
walk-forward protocol that produced the headline** (train pooled on seasons
< t, bet season t):

| Cohort | Bets | Win% | Wilson 95% | Unit return |
|---|---|---|---|---|
| **FBS vs FBS** | 268 | **50.00%** | [44.1, 55.9] | **−4.5%** |
| **FBS vs FCS** | 328 | **59.45%** | [54.1, 64.6] | **+13.5%** |
| **FCS vs FCS** | 85 | **68.24%** | [57.7, 77.2] | **+30.3%** |
| ALL (published headline) | 681 | 56.83% | [53.1, 60.5] | +8.5% |

**Essentially the entire validated edge comes from games involving an FCS
team.** The FBS-only market — the one a reader of the guide would assume they
are betting — sits at breakeven, below it after vig.

The obvious confound is that FCS totals might just be set too low, in which
case bias is incidental. It isn't. The within-cohort **lift** (over rate at
bias > 1.0 minus over rate at bias < 0.5) differences out any cohort-level
pricing offset, and the mechanism is strongest exactly where the theory says
it should be:

| Cohort | Baseline over% | bias < 0.5 | bias > 1.0 | Lift | Mean dog implied | P(dog scores 0) | Probit slope |
|---|---|---|---|---|---|---|---|
| FBS vs FBS | 48.80% | 48.48% | 50.52% | **+2.0** | 21.78 | 2.9% | +0.118 (p = 7e−3) |
| FBS vs FCS | 52.55% | 43.73% | 59.29% | **+15.6** | 13.25 | **12.7%** | +0.222 (p = 4e−5) |
| FCS vs FCS | 48.80% | 47.91% | 68.35% | **+20.5** | 20.32 | 2.9% | +0.378 (p = 2e−5) |

Baselines are ~49% in every cohort, so this is not a level effect. The slope is
positive and significant in **all three** — the mechanism is real in FBS too,
it just doesn't clear the vig there at this threshold. Cross-division games
have 4× the shutout rate, which is the censoring mechanism in its rawest
observable form.

**The FBS board is not dead — it needs a higher threshold.** At bias > 1.75
(`--threshold 1.75`), FBS-vs-FBS goes 56.14% over 57 walk-forward bets
(+7.2% per unit), clearing breakeven, though at that sample the Wilson
interval [43.3, 68.2] still contains it. So the honest statement is not "the
FBS edge is absent" but "**the bias threshold that clears the vig is
division-dependent**" — roughly 1.0 where mismatches are structural, higher
on the FBS board. That is a rule refinement, not an exclusion, and it is what
the threshold sweep in §9 item 1 should pin down.

**Caveats, stated plainly.** This is a post-hoc subgroup split of an already
published result — precisely where false discoveries breed. Three cohorts were
tested; the split was chosen structurally (division mismatch drives implied dog
points toward the floor), not by search; and it survives the honest protocol.
The FCS-vs-FCS cell is 85 bets. Two competing readings, both plausible and
distinguishable:

1. **Mechanism**: mismatches push dogs closer to the floor (12.7% shutouts).
2. **Market quality**: books price FCS boards with less effort and lower
   limits — the edge survives *because* nobody is paid to kill it. This also
   predicts the capacity limit is severe (open question 6).

These are not exclusive, and the difference matters for sizing far more than
for the bet rule. The FBS-vs-FBS result also puts a number on decay: whatever
edge FBS totals once had at bias > 1.0 is not there now.

**This should be reflected in the guide before anyone bets the FBS board on
its strength.** Flagged, not applied — changing the operational playbook is
the owner's call, and it wants one more season plus a threshold sweep first.

## 4. Candidate board — same math, no new machinery

Sigmas outside CFB full-game are **documented priors, not fits**; this ranks
data-acquisition targets, not bets.

| Market | bias | BNR | exact | price | edge vs price | Verdict |
|---|---|---|---|---|---|---|
| CFB live 4Q remaining total, blowout | 1.36 | 0.186 | +5.94 | −115 | **+2.46** | Highest theory, hardest execution |
| CFB 1Q total, qualifying | 1.37 | 0.170 | +5.40 | −115 | +1.91 | Needs 1Q lines |
| **FCS / cross-division full game** | 2.53 | 0.140 | +5.11 | −115 | +1.62 | **Data already in repo — §3** |
| CFB game total, bias > 1.75 | 1.83 | 0.113 | +3.70 | −110 | +1.32 | Validated |
| CFB 1H total, qualifying | 1.23 | 0.109 | +3.22 | −110 | +0.84 | Blocked on 1H lines (B1) |
| CFB game total, bias > 1.0 | 1.11 | 0.069 | +1.76 | −110 | −0.62 | Validated; realized ≈ 2× theory |
| NFL 1Q total | 0.57 | 0.082 | +1.74 | −115 | −1.75 | Short window can't rescue NFL |
| NFL game total, biggest dogs | 0.11 | 0.008 | +0.10 | −110 | −2.28 | Dead — floor never binds |
| CBB, biggest mismatch *(control)* | 0.00 | 0.000 | +0.03 | −110 | −2.35 | Correctly rejected |
| CFB median game *(control)* | 0.14 | 0.008 | +0.09 | −110 | −2.29 | Correctly rejected |

The two controls exist to prove the screen can say no. Note the validated
cohort scores **−0.62** on pure censoring — the realized edge (+4.5 pp) is
about 2.5× the theoretical (+1.76 pp). That gap *is* open question 1, and it
means the screen is a **lower bound**: a market it rejects marginally may still
pay via whatever the second mechanism is.

**NFL is out.** Dogs are implied ~18 points against σ ≈ 9.5 — the floor is 1.9σ
away and the gap is 0.11 points. Short windows lift BNR to 0.082 but the −115
pricing on quarter markets takes more than that back, in the sharpest market
in sports. Basketball is out at any window: means sit 5–6σ from zero.

## 5. Other sports — and the taxonomy that decides which are worth it

§2a forces a distinction that the CFB-only view obscures. There are two
structurally different boundaries, and only one of them needs pooling:

**Type A — boundary censoring.** Mass piles up *at* the bound, below the line
(football's floor at 0). Mean-only; needs a pooled settlement to pay.
**Type B — stopping-rule truncation.** Play *stops*, so mass is removed from
the *upper tail*. This shifts quantiles directly, so it pays on a single side
and is the stronger family for one-leg markets.

The repo has only ever studied Type A, and the saturation negative result is a
Type A result — it says nothing about Type B.

| Sport / market | Type | Boundary | Side favored | Machinery needed | Data | Priority |
|---|---|---|---|---|---|---|
| **MLB — home 9th not played / walk-off** | B | Home team stops batting when ahead | **Under** | Inning-level truncation model; P(home leads after 8.5) from ML + total | **Retrosheet, free** | **High** |
| **Cricket — chase innings** | B | Innings ends the instant the target is passed | **Under** | Exact known censor point (= 1st-innings score) | Cricsheet, free | High (theory) |
| **CS2 / esports — map round totals** | B | Map ends at 13; loser's rounds capped at 12; OT lump | Under | Discrete race model, not Gaussian | HLTV, semi-free | Medium |
| **MMA — total rounds** | B | Fight ends on finish | Under | Hazard model; cross-check vs method-of-victory market | Free | Medium |
| **Tennis — total games** | B | Match ends at 2 (or 3) sets | Under | Stopped-sum; heavily modelled by sharps already | Paid | Low |
| **NHL — empty net / OT lump** | B+ | Goalie pulled when trailing late; OT adds exactly 1 goal ~23% | Over, state-dependent | Atoms in the settlement distribution | Free | Medium (live) |
| **NBA / CBB — garbage time** | A′ | Behavioural ceiling: benches empty in blowouts | **Under** | Not distributional — a behavioural ceiling | Free | Medium |
| **Soccer — team/match goals** | — | Native ℕ support | **None** | Poisson/Dixon-Coles already correct | Free | **Control** |
| **Golf — matchups** | — | Right-skewed strokes; cut = *sample* truncation | Depends | Heckman for the cut; skew for matchups | DataGolf, paid | Low |

Four of these deserve more than a table row:

**MLB is the best non-football candidate, and it's free.** The home team
doesn't bat in the bottom of the 9th when leading (~45–50% of games) and a
walk-off truncates the inning mid-scoring. That removes ≈ 0.22–0.25 runs of
upper tail against a game-total σ of ≈ 4.4 → BNR ≈ 0.057, right at the −110
threshold and comparable to CFB's 0.069. The catch: this is the single most
famous feature of baseball scoring and the *level* is certainly priced. The
tradable claim is therefore the **cross-sectional variation** — the truncation
is large when the home team is a heavy favorite and small when it's a dog, and
that variation is a function of two quoted lines (moneyline/run line + total),
which is exactly the condition-3 structure that makes CFB work.

And MLB hands you a control the CFB market never had: **first-5-innings totals
are not truncated at all.** `full-game total − F5 total` is the market's own
estimate of innings 6–9 *including* the censoring. Regressing that spread on
the model-predicted 9th-inning truncation is a direct, clean, free test of
whether the market prices the variation. That is the single cheapest
high-quality experiment on this whole list.

**Cricket has the cleanest identification anywhere.** In a chase the censoring
point is not estimated — it *is* the first-innings score, known exactly before
the second innings starts. No Tobit needed. The mechanism is enormous rather
than subtle, so assume the level is priced and go straight to the variation.

**Basketball is the mirror, and CFB's negative result does not transfer.** The
saturation module looked for a *distributional* soft ceiling on football scores
and correctly found none. Basketball's ceiling is **behavioural**: in a blowout
the starters sit and scoring rate falls; in a close game late fouling *inflates*
it. So the map from |margin| to total is non-monotone — convex at small
margins, concave at large ones — and any book extrapolating pace linearly
misprices both tails. This is a live-betting hypothesis (bet the under in
blowouts, the over in close late games), untested here, and it needs a
possession model rather than a Tobit.

**Soccer is the control that proves the mechanism is about *modelling*, not
about zero.** Soccer has the most binding floor in sport — a team's expected
goals is ~1.3 and P(0 goals) ≈ 27%. Yet there is no censoring bias, because
goals are natively non-negative counts with no latent negative mass, and books
model them Poisson. **The CFB edge does not come from scores being near zero.
It comes from a book using a Gaussian/linear internal representation for a
bounded quantity.** Any sport where the book's model already respects the
bound is dead on arrival, no matter how low-scoring. That is the sharpest
statement of where this travels, and it's why the screen must always be
applied to the *book's model*, not the sport.

## 6. Beyond sports

The zero-strike-call reframing makes the non-sports analogues immediate. The
generic hunt: **a derived instrument whose value depends on the *distribution*
of a quoted quantity, priced off that quantity's point estimate.**

- **Weather derivatives** — HDD/CDD are literally `max(0, 65 − T)`. This is
  the reference case for what "priced correctly" looks like: the industry
  moved to Bachelier/Black option math decades ago. Sports totals markets are
  where weather markets were before they did.
- **Insurance layers** — deductibles, attachment points and limits are
  `E[min(max(0, L − D), Limit)]`. Same formula, priced properly by anyone
  competent; the money is in counterparties who quote expected loss linearly.
- **Energy** — spark and crack spreads are `max(0, P_out − k·P_in)`: an option
  on a spread. A forward-mean valuation always undervalues it.
- **Corporate structures** — earn-outs, revenue floors, capped bonus pools and
  convertible caps are all kinked payoffs routinely valued at the mean of the
  underlying forecast.
- **Prediction / combination markets** — the condition-3 pattern in its purest
  form: any market whose settlement is a `min`/`max`/threshold over legs that
  are *themselves* quoted, where the derived leg is stale relative to the
  liquid ones.

The reusable discipline: whenever you see a payoff with a kink, ask whether
whoever quoted it used a distribution or a point estimate — and then ask §2a's
question, whether the gap actually moves a quantile.

## 7. Where it does *not* travel

Worth as much as the candidate list. A market is dead if **any** of these hold:

1. **μ more than ~2σ from the bound** → BNR < 0.02. Basketball, NFL full game.
2. **Native non-negative support the book already models** → soccer, hockey
   goals. Low scoring is *not* sufficient.
3. **Single-side settlement with Type A censoring** → the pooling theorem.
   Team totals, per §2a.
4. **The quote is fitted to realized outcomes, not derived** → the gap is
   already in the number. Only cross-sectional *variation* can be mispriced.
5. **Price ≥ −120** → the hurdle is 4.55 pp; almost nothing on this list
   clears it. Derived and exotic markets are exactly where books widen.
6. **Two-sided bounds** → floor and ceiling gaps partially cancel.
7. **Capacity** → qualifying games are illiquid *by construction*. This
   compounds with §3's reading 2: the edge may exist precisely where it isn't
   worth a book's while to fix.

## 8. Porting protocol, and the multiplicity problem

This document names ~15 candidates. Testing all of them at α = 0.05
**guarantees** a couple of 56% winners from noise. The repo's credibility comes
from pre-registration discipline (the 1.0/1.75 thresholds are the paper's, not
fitted here), and porting is where that discipline is easiest to lose.

Six steps for any new market:

1. **Screen first, on priors.** Compute BNR and the exact edge *before*
   acquiring data. Write the predicted edge down. Reject anything under the
   price hurdle.
2. **Classify the boundary** (Type A vs Type B) and check the pooling
   condition. A Type A single-side market is dead before you start.
3. **Choose machinery to match the support.** Tobit for censored Gaussian;
   hurdle/negative-binomial for counts; stopped-sum or hazard for Type B;
   possession models for behavioural ceilings. Never port the Tobit blindly.
4. **Run the v3 test in the new market.** Does the gap dominate the raw lines
   it was built from? If a simple "low total / big spread" filter reproduces
   it, there is no new finding.
5. **Walk-forward, always.** Train on the past only. §3 exists because the
   walk-forward machinery was already there.
6. **Correct for the family.** Benjamini–Hochberg across every market tested,
   and pre-register the ranking by *theoretical* edge (§4's table is that
   ranking, published before the tests). A market that beats its own
   pre-registered prediction is a finding; one that merely beats 52.38% after
   fifteen attempts is not.

## 9. Ranked next actions

| # | Action | Cost | Why it ranks here |
|---|---|---|---|
| 1 | **Extend §3**: threshold sweep, per-season stability and decay check on the division cohorts; decide whether the guide's bet rule should carry a division filter | Hours — data is in the repo | Largest effect found, already walk-forward validated, currently affects live betting advice |
| 2 | **Rewrite open question 3** as the §2a diagnostic and re-scope the team-totals data hunt accordingly | Minutes | Stops a data purchase being made for a reason that is theoretically wrong |
| 3 | **MLB F5-vs-full-game truncation test** | Days, free data | Cheapest clean test of a Type B market; a genuine second sport |
| 4 | **1H/1Q lines** (research B1, still blocked) | Blocked on spend | §2b says the payoff is real; unchanged by this doc |
| 5 | **Live/in-game CFB totals** feasibility study | Weeks | Highest theoretical BNR in §4; execution is the whole question |
| 6 | **CS2 map round totals** | Weeks | Softest books on the list; needs discrete machinery built from scratch |

Items 1 and 2 need no new data and no new money. They should happen before
anything on this list gets purchased.

---

*Screen and cohort analysis: [research/extensions/](../research/extensions/).
Model and playbook: [MODEL_GUIDE.md](MODEL_GUIDE.md). Audit: [REVIEW.md](../REVIEW.md).
Nothing in this document is a validated edge except §3, and §3 is a post-hoc
subgroup split — read its caveats before staking anything on it.*
