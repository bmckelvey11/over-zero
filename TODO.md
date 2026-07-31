# TODO — open tasks

*Single tracker for everything outstanding across the repo. Consolidates
[MODEL_GUIDE §9/§10](docs/MODEL_GUIDE.md#9-next-steps),
[EXTENSIONS §9](docs/EXTENSIONS.md#9-ranked-next-actions),
[LEDGER](docs/LEDGER.md), [research/BLOCKERS.md](research/BLOCKERS.md) and
[REVIEW.md](REVIEW.md). Last reconciled 2026-07-31.*

Three things are true of this list and worth knowing before reading it: the
highest-value item needs **no new data and no money**; the two items that need
money are both **data purchases, not modelling work**; and §5 exists so
finished work doesn't get picked up again.

---

## 1. Needs a decision from you — blocked until then

Nothing here can move without an owner call. Each states the exact decision.

- [ ] **B1 — buy first-half lines?** `floor_bias_1h/` is built and waiting;
      it needs a CSV of `game_id,half_spread,half_total` and runs immediately
      (`python floor_bias_1h/run_1h.py --half-lines file.csv`). Survey found
      no free, ToS-permitted, joinable source. **Decision: approve
      ~$30/month at the-odds-api.com** (accepting that period markets only go
      back to 2023-05-03), **or** point at a dataset the survey missed.
      Theory says this market is ~1.6–2.3× stronger than the validated one
      ([EXTENSIONS §2b](docs/EXTENSIONS.md#2b-the-t-scaling-law--shorter-windows-bind-harder)).
      *Highest-value blocked item.* → [BLOCKERS 2026-07-31 B1.1](research/BLOCKERS.md)

- [ ] **B2 — chase team-totals data?** *Read the re-scope before deciding.*
      This was ranked as "the purest instrument"; that premise was wrong —
      single-side censoring earns **exactly zero**
      ([EXTENSIONS §2a](docs/EXTENSIONS.md#2a-the-pooling-theorem--censoring-alone-does-not-pay-on-a-single-side)).
      It is still worth running, but as a **diagnostic** for open question 1,
      not as a bigger edge. **Decision: approve a support inquiry to confirm
      NCAAF `team_totals` coverage exists at all before any spend** — coverage
      is unconfirmed at 2 of 4 vendors. Lower priority than it used to be.
      → [BLOCKERS 2026-07-31 B2.1](research/BLOCKERS.md)

- [ ] **B3 remainder — supply `ODDS_API_KEY`?** Open question 4 (does the
      total drift open→close) is **answered: null**, n=514, 95% CI [−0.05,
      +0.32]. Open question 5 (what juice books actually charge on qualifying
      overs) is unanswerable from raw files, which carry no price field. Needs
      either a key for forward capture or your own bet log. *Your bet log
      answers it for free if you start one — see §4.*

## 2. Ready to run — no new data, no spend

- [ ] **Finish the division-cohort work.** Threshold sweep and per-season
      stability on FBS-vs-FBS / FBS-vs-FCS / FCS-vs-FCS, then decide whether
      the bet rule carries a division filter. Current state: the walk-forward
      edge is carried almost entirely by FCS-involved games (FBS-vs-FBS 50.00%
      over 268 bets at bias > 1.0, but 56.14% at bias > 1.75), which suggests
      the vig-clearing threshold is division-dependent rather than the FBS
      edge being absent. **This currently affects live betting advice and is
      the single highest-value open item in the repo.** Data is local; hours
      of work. → [EXTENSIONS §3](docs/EXTENSIONS.md#3-the-empirical-finding-it-already-travels--one-rung-down-not-sideways),
      `python research/extensions/division_cohorts.py`

- [ ] **MLB truncation test.** The home team doesn't bat in the bottom of the
      9th when leading — a stopping-rule truncation that moves quantiles
      directly, unlike football's floor. `full-game total − F5 total` is the
      market's own estimate of innings 6–9 *including* the censoring, giving a
      built-in control the CFB market never had. Free data (Retrosheet).
      Cheapest clean test of a second sport. → [EXTENSIONS §5](docs/EXTENSIONS.md)

- [ ] **Live/in-game CFB totals feasibility study.** Highest theoretical
      bias-to-noise ratio on the board (0.186 vs 0.069 full-game); execution
      is the entire question — line speed, limits, and pricing. Study first,
      code second.

- [ ] **CS2 map round totals.** Softest books on the candidate list, but needs
      a discrete race model built from scratch (13-round cap + overtime lump).
      Weeks of work; lowest priority in this section.

## 3. Open questions with no current path

Tracked, not actionable today. Each line says what would move it.
Full text: [MODEL_GUIDE §10](docs/MODEL_GUIDE.md#10-open-questions).

- [ ] **Q1 — why is the realized edge ~2× what censoring predicts?** The
      oldest open item in the repo (raised by v2, survived v3, still open —
      [LEDGER v2-B3](docs/LEDGER.md)). Needs a feature outside the two lines.
      Best available experiment is the re-scoped B2 above, which isolates the
      residual by construction.
- [ ] **Q6 — how much money can this absorb?** Qualifying games are illiquid
      by construction. Compounds with the division finding: if the edge lives
      on FCS boards, limits are *smaller* than assumed. Matters only if sizing
      beyond recreational units.
- [ ] **Q8 — is the Gaussian-Tobit approximation costing accuracy?** Scores
      are 0/3/7 lumps. Second-order for bet/no-bet, first-order for per-game
      Kelly pricing, and blocking for the short-window markets in §2.
- [ ] **Q9 — team-level σ heterogeneity.** Tested in
      [research/b5_team_sigma/](research/b5_team_sigma/RESULTS.md): team σ
      **hurts** OOS at K=30. Reopen only with the calibration caveat in that
      writeup addressed (both arms shared one pooled-calibrated probit).
- [ ] **Q10 — why is the edge concentrated in FCS/cross-division games?**
      Mechanism (mismatches drive dogs to the floor) vs market quality (nobody
      is paid to sharpen FCS boards). Not exclusive. §2's sweep is the first
      step; distinguishing them decides sizing more than rule.

## 4. If you're betting this season

From [MODEL_GUIDE §9 track A](docs/MODEL_GUIDE.md#a-if-youre-going-to-bet-it-this-season).
Do these in order; steps 2–3 also resolve open questions 4 and 5 for free.

- [ ] **Dry-run one full Saturday before staking.** Score the slate, check the
      qualifying list against the board, confirm verdicts and prices look like
      §4–§5 predict. Costs nothing, catches setup mistakes.
- [ ] **Start the bet log on day one.** Date, teams, book, spread taken, total
      taken, price, bias, model P(over), closing total, closing price, result.
      This is the instrument that answers "what juice do books really charge"
      and "should I bet early or late" — not bookkeeping.
- [ ] **Ramp sizing.** First ~25–30 bets at half stakes while the log confirms
      you can get −110 and your CLV isn't systematically negative.
- [ ] **Decide the division question first** (§2 item 1) if you intend to bet
      the FBS board at bias > 1.0 — the headline win rate is carried by games
      elsewhere.

### Recurring — after every season

- [ ] Scrape the new season into `cfb-site`, then re-run
      `python monitor/run_walkforward.py` and `python monitor/run_monitor.py`.
- [ ] Check the stop rules: halt if a trailing 3-season window shows both
      `SLOPE~0` and a win% CI centred at/below breakeven. As of 2025 data:
      no decay (trend +0.006/yr, p = 0.55).

## 5. Engineering conveniences

Nice-to-have; none blocks research. From
[MODEL_GUIDE §9 track C](docs/MODEL_GUIDE.md#c-engineering-conveniences).

- [ ] **`score_week.py`** — pull the week's lines from the CFBD API (cfb-site
      has the scraper and auth), score every game, print the qualifying list.
      Removes manual number entry from the weekly workflow.
- [ ] **Bet-log template + CLV summarizer** — a CSV header plus a ~30-line
      script reporting average price, average CLV in points, and
      realized-vs-expected win rate. Makes §4 step 2 mechanical.
- [ ] **Season-maintenance checklist** in `monitor/README.md` so the recurring
      block above is copy-paste, not memory.

## 6. Done — do not redo

Recorded so settled work isn't picked up again. Each is reproducible from the
command in its writeup.

| Item | Outcome | Where |
|---|---|---|
| REVIEW.md action list (all 9 items) | Landed 2026-07-30, commits `22ca204`…`32a43c3` | [REVIEW.md addendum](REVIEW.md) |
| Walk-forward backtest | 56.83% / 681 bets, Wilson [53.1, 60.5] | [monitor/](monitor/) |
| Season-clustered probit SEs | Slope robust, p ≈ 1e−18 | [monitor/](monitor/) |
| Consensus-only sensitivity | 58.16% — edge is not soft-book artifact | [REVIEW.md](REVIEW.md) |
| v2 — analytic SEs, ρ independence | Both caveats immaterial | [LEDGER](docs/LEDGER.md) |
| v3 — "is it just low totals?" | Refuted; `biasTotals` irreducible | [LEDGER](docs/LEDGER.md) |
| Saturation / under-side edge | Negative result — no symmetric ceiling | [saturation_bias/](saturation_bias/) |
| B3 — open→close drift (Q4) | Null: n=514, CI [−0.05, +0.32] | [research/b3_snapshots/](research/b3_snapshots/RESULTS.md) |
| B4 — residual features | No feature displaces the censoring signal | [research/b4_features/](research/b4_features/RESULTS.md) |
| B5 — hierarchical team σ | Team σ hurts OOS at K=30 | [research/b5_team_sigma/](research/b5_team_sigma/RESULTS.md) |
| Open question 3 re-scope | Premise corrected; now a Q1 diagnostic | [EXTENSIONS §2a](docs/EXTENSIONS.md) |
| Open question 7 (portability) | Answered — screen, board, taxonomy | [EXTENSIONS](docs/EXTENSIONS.md) |
