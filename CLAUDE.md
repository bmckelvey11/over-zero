# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A betting-research repo recreating Arscott (2022), *"Market efficiency and censoring bias in college football gambling"* (SSRN 4197428). The thesis: team scores can't go below 0 (left-censored), betting lines price the latent uncensored score, so the **over** on the game total is systematically underpriced when expected censoring bias is high. The repo validates that edge on real CFBD data (2013–2025) and extends it.

Start with `docs/MODEL_GUIDE.md` (the full writeup and betting playbook) and the root `README.md` (module index). `REVIEW.md` is a 2026-07-30 code/methodology audit; its code findings (broken `--raw` path, missing `requirements.txt`, undocumented `monitor/`) have since been fixed.

Plain Python scripts over numpy/scipy/statsmodels — no package structure, build system, test framework, linter, or CI.

## Commands

```bash
pip install -r requirements.txt        # numpy, scipy, statsmodels (Python 3.11+ works)
```

Run scripts from the repo root as `python <dir>/<script>.py`. Sibling-module imports resolve via the script's own directory; data paths resolve relative to `__file__`. Each script's docstring shows its exact invocation.

```bash
# De facto regression test (synthetic; ~seconds). Must end "SELF-TEST OK".
python v1/demo_reproduce.py

# Headline 13-season backtest. --raw is the recommended data path.
python v1/run_on_project_data.py --raw --season 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025

# Operational entry points
python monitor/score_game.py SPREAD TOTAL [SPREAD TOTAL ...]   # score upcoming games
python v1/predict_week.py --fit-seasons 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 \
    --raw data/raw/lines_2026_week1.json --book DraftKings     # picks for an unplayed week

# Study drivers (all accept --season; defaults to 2013–2025)
python v2/run_v2.py                          # caveat checks: analytic SEs, correlation
python v3/run_v3.py                          # is the signal censoring or just "low total"?
python floor_bias_1h/run_1h.py [--total-frac 0.52 | --half-lines file.csv]   # first-half extension
python saturation_bias/run_saturation.py     # under-side mirror (negative result)
python monitor/run_monitor.py [--width 3]    # edge-decay tracking
python monitor/run_walkforward.py [--threshold 1.75 --min-train 5]   # honest time-ordered backtest

# Data build scripts (ActionNetwork first-half data)
python data/raw/1H-raw/combine_to_csv.py        # -> data/processed/1h_lines.csv
python data/raw/1H-raw/build_1h_games_csv.py    # -> data/processed/1h_games.csv
```

There is no pytest suite. After touching estimator code, rerun `v1/demo_reproduce.py` plus the affected drivers and compare against the results tables in the module READMEs.

## Architecture

**Versioned research layout — v1 is frozen, v2 is the shared core.** Each top-level directory is a self-contained study with its own README (mechanism, run commands, dated results tables, caveats).

- `v1/` — the Floor Bias baseline: all 10 paper models as pure functions over numpy arrays in `censoring_bias.py`; `fit_pipeline` chains implied team points → Tobit σ → censoring bias → probit. **Frozen: do not edit model logic or results.** Restoring broken behavior (e.g. path bugs) is allowed — the freeze protects conclusions, not bugs. v1 imports nothing from other versions.
- `v2/` — self-contained reimplementation with analytic (OPG) standard errors. `models_v2.py` is the estimator core (Tobit, probit, censoring bias, Kelly, and the shared CFBD raw-lines loader) that **every later module imports** via `sys.path.insert(0, <repo>/v2)` at module top. A change to `models_v2.py` propagates to v3, floor_bias_1h, saturation_bias, monitor, and research/ scripts.
- `v3/`, `floor_bias_1h/`, `saturation_bias/`, `monitor/` — follow-on studies, each split into a logic module plus a `run_*.py` driver. `saturation_bias/` is a deliberate, documented negative result (no under edge exists) — don't "fix" it into a positive one.
- `research/` — Track B studies (b1–b5), one directory each with `RESULTS.md` or `SOURCES.md`; verdicts indexed in `research/SUMMARY.md`. `research/BLOCKERS.md` is the dated blocker/decision log where plan deviations and owner sign-offs are recorded; the prespecified plan lives in `docs/superpowers/plans/`.

**Data flow.** `data/raw/games_{season}.json` (1992–2025) and `lines_{season}.json` (2013–2025) are CFBD dumps produced by the sibling `cfb-site` repo's scraper and copied in (see root README "Data dependency" for the refresh procedure); `data/processed/games.csv` is the consensus-book build. Two load paths: `--raw` picks, per game, any book carrying both spread and total (recovers ~2,800 games — the recommended path); the processed CSV silently omits 2013/2015/2016. Betting lines only exist from 2013 — earlier seasons are unusable. First-half data comes from ActionNetwork snapshots in `data/raw/1H-raw/` and builds into `data/processed/1h_*.csv`. All data is committed; analyses run fully offline with no credentials (`env.env` is gitignored for local secrets).

**Sign conventions.** Raw CFBD spreads are home-relative (negative = home favored). The models use the paper's favorite/underdog frame: `spreadEst = |spread|` ≥ 0, `dogPointEst = (total − spread)/2`, `favPointEst = (total + spread)/2`. `score_game.py` deliberately ignores the sign of its SPREAD argument. Don't confuse the four point quantities defined in MODEL_GUIDE.md §"Which lines this guide means": game spread and game total are markets; implied team points are model internals; sportsbook "team totals" are unused.

**The headline rule** (what the whole repo defends): bet the over when expected censoring bias > 1.0 points (strong tier > 1.75) at −110 juice; breakeven 52.38%; walk-forward result 56.83% over 681 bets (2016–2025).

## Conventions

- Results tables in READMEs and MODEL_GUIDE.md are generated output from actual runs and carry run dates. If your change moves the numbers, rerun the driver and update the tables with the new date — never hand-edit numbers or leave them stale.
- Three distinct return metrics — unit return, Kelly turnover return, and fractional-Kelly bankroll ROI — must not be conflated when reporting results (see v1 README "Kelly sizing notes"; compounded figures are order-dependent and in-sample).
- Report win rates with Wilson confidence intervals, and judge edge decay on trailing windows, not single seasons (per-season N is too small; see `monitor/README.md`).
- Commit messages follow `type: summary` or `type(scope): summary`; types in history: `feat`, `fix`, `chore`, `data`, `research(bN)`.
- `docs/cfbd-api/` is vendored, generated CFBD API reference documentation — don't edit it.
