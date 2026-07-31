# Research Track B — Summary

Executed per `docs/superpowers/plans/2026-07-30-research-track-b.md`. All
five phases addressed; three concluded blocked on data acquisition
(prespecified valid outcomes), two produced completed analyses (one
positive-process/negative-result, one deviation-adjusted null).

| Phase | Status | Verdict | Link |
|---|---|---|---|
| B4 — Residual features | done | Base `biasTotals` +0.0710 (SE 0.0081) replicated. Full spec (week, neutralSite, conferenceGame, home_dog — `fcs_dog` substituted, zero-variance post-join, see BLOCKERS.md): only `neutralSite` clears Bonferroni (p=0.0067), small negative effect; `biasTotals` shifts +0.39 SE (robust). **No feature materially displaces the censoring signal.** | [research/b4_features/](b4_features/RESULTS.md) |
| B5 — Hierarchical team σ | done | K=30 (primary): OOS logloss improvement (pooled − team) = **negative**, 95% CI [-2.76, -0.11]×1e-4, entirely below zero. Same sign at K=15/60. **TEAM-SIGMA HURTS OOS** — pooled σ is the better choice, not team-shrunk σ. | [research/b5_team_sigma/](b5_team_sigma/RESULTS.md) |
| B1 — First-half lines backtest | blocked | Source survey found no free, ToS-permitted, join-able 1H spread+total dataset (CFBD raw data, sportsbookreviewsonline.com, Kaggle all ruled out). Cheapest paid: the-odds-api.com $30/mo (coverage from 2023-05-03 only). **VERDICT: blocked** — needs owner-approved spend or an alternate data source to proceed to B1.2–B1.4. | [research/b1_first_half/](b1_first_half/SOURCES.md) |
| B2 — Dog team-total backtest | blocked | Source survey found no free, ToS-permitted team-totals dataset; all paid vendors cost-blocked, team-totals-specific coverage additionally unconfirmed at 2 of 4. Cheapest paid: the-odds-api.com $30/mo (coverage unconfirmed). **VERDICT: blocked** — needs owner-approved spend/inquiry or an alternate data source to proceed to B2.2–B2.3. | [research/b2_team_totals/](b2_team_totals/SOURCES.md) |
| B3 — Multi-snapshot odds capture | done (deviated) | `ODDS_API_KEY` unavailable; owner approved building the open→close drift analysis from already-downloaded raw historical data instead of live capture (see BLOCKERS.md). Usable coverage: 2021–2025 only (`overUnderOpen` null for 2013–2020 in this data source). Pooled QUALIFYING-games drift: n=514, mean +0.13, 95% CI **[-0.05, +0.32] — straddles zero, null result**. Open question 5 (juice/price drift) is unanswerable from this data source; the original API-key capture script remains a valid path if a key becomes available. | [research/b3_snapshots/](b3_snapshots/RESULTS.md) |

## Notes

- Full blocker/decision trail (data-acquisition blockers, owner
  resolutions, plan deviations) is in [research/BLOCKERS.md](BLOCKERS.md).
- B4's `fcs_dog` → `home_dog` substitution and B3's live-capture →
  raw-data-analysis substitution were both owner-approved mid-execution;
  see BLOCKERS.md for the full reasoning on each.
- Every task went through implementer → task-reviewer (spec compliance +
  code quality) gates per `superpowers:subagent-driven-development`; two
  tasks (B4.1, B3) required one fix round each before approval.
