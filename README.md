# paper_models — Arscott (2022) censoring-bias recreation

Recreation of *"Market efficiency and censoring bias in college football
gambling"* (SSRN 4197428): the over/under line ignores that team scores are
left-censored at 0, so the **over** is underpriced when expected censoring bias
is high.

**Start here: [docs/MODEL_GUIDE.md](docs/MODEL_GUIDE.md)** — the full writeup
with figures: how the model works, the evidence, which games qualify, and the
betting playbook (filters, pricing, sizing, stop rules). Score a game with
`python monitor/score_game.py SPREAD TOTAL`.

## Versions

- **[v1/](v1/) — Floor Bias model** — frozen reference. Named for the mechanism:
  scores censored at the **floor** of 0 bias totals up → bet the over. Full
  recreation (Tobit, censoring bias, probit, Kelly), backtested on 13 seasons of
  real CFBD data (2013–2025). Headline: bet the over when expected bias > 1.0 →
  56.6% win over 680 bets. **Do not edit — this is the baseline.**

- **[v2/](v2/)** — tightens two v1 caveats: analytic (OPG) standard errors in
  place of the BFGS approximation, and dropping the favorite/underdog error
  independence assumption. Both proven immaterial on this data; v1 stands.

- **[v3/](v3/)** — tests whether the over-edge is genuinely censoring or just a
  repackaging of "low total / lopsided game." Verdict: `biasTotals` dominates
  the raw total and spread in- and out-of-sample; nothing simpler replaces it.
  v1's single-feature rule is the best line-only strategy.

  **[docs/LEDGER.md](docs/LEDGER.md)** consolidates v2 and v3 into one ledger
  of things tried — nine hypotheses, what each returned, which are settled and
  which are still open, so nothing gets re-run by accident.

## Extensions & sibling models

- **[floor_bias_1h/](floor_bias_1h/)** — Floor Bias extended to **first-half**
  totals. Theory predicts a stronger over edge (1H censoring bias ~2.3× larger,
  underdog shutouts 3.9× more common). Ready to run: approximation mode now,
  true backtest the moment real 1H lines are supplied (`--half-lines`). Approx
  results show the edge survives de-biasing the 1H scoring excess.

- **[saturation_bias/](saturation_bias/)** — the ceiling-side mirror: does the
  theory extend to betting the **under** via a soft scoring ceiling? **Negative
  result.** The ceiling isn't identifiable (no pile-up at the top), the fitted
  relationship runs the wrong way, and no OOS under strategy survives. The
  censoring asymmetry is real: floor → over edge, no symmetric under edge.

- **[research/extensions/](research/extensions/)** — where else the math pays.
  Restates the model as a zero-strike Bachelier call, screens candidate
  markets on a bias-to-noise ratio, and splits the validated CFB edge by
  division. Two results worth knowing: single-side **team totals earn exactly
  zero** under pure censoring (it's a mean effect, not a quantile effect), and
  the walk-forward edge is carried almost entirely by **FCS/cross-division**
  games (FBS-vs-FBS: 50.0% over 268 bets). Writeup:
  **[docs/EXTENSIONS.md](docs/EXTENSIONS.md)**.

- **[monitor/](monitor/)** — operational truth tools: the **edge-decay
  monitor** (per-season and trailing-window probit slope + win% with CIs,
  trend test — no decay through 2025) and the **walk-forward backtest**
  (train on seasons ≤ t−1, bet season t: 56.83% over 681 bets, Wilson 95%
  lower bound above breakeven — the deployable-protocol check behind v1's
  headline).

Run instructions are in each version's README.

## Data dependency

Scripts read CFBD data from the local `data/` folder (`data/raw/games_{season}.json`,
`data/raw/lines_{season}.json`, `data/processed/games.csv`) — a copy of the
same files produced by the sibling `cfb-site` repo's scraper. To refresh with
newer seasons, re-run `python -m cfb_system_maker scrape --season ...` from
`cfb-site` and copy the updated `games_*.json`/`lines_*.json`/`games.csv` into
this repo's `data/`. `v1/run_on_project_data.py` also accepts an explicit
`--csv` path if your layout differs.
