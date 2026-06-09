# ADR-010: Onda Wave Methodology

- **Date:** 2026-06-04
- **Status:** Accepted
- **Last updated:** 2026-06-07

## Context

SolarStorm is a clean-slate rewrite of a prior NZWN forecasting project that
produced no predictive value (NULL_NOT_BEATEN, negative skill vs persistence).
The rewrite must avoid the same failure mode: building complex models on an
untested foundation.

The project needs a phased delivery model where each wave (onda) depends on and
validates the previous wave. No wave may skip ahead: a model trained on biased
features is no better than a coin flip, regardless of architecture.

## Decision

**Sequential waves (ondas) where each builds on the validation of the previous.**

### Onda 0: Scaffold (complete: 2026-06-04)

- Repository structure, tooling, CI
- Frozen principles P1-P6
- Data pipeline: IEM ASOS ingest, METAR parsing, obs.parquet, labels.parquet
- Causal firewall (P1)
- No models, no predictions: infrastructure only

### Onda 1: Baselines (complete: 2026-06-04)

- L0-L4 baseline ladder (persistence, dminus1, climatology, empirical conditional)
- Walk-forward harness with expanding-window splits
- Frozen gates G1-G5 (G4 hard, non-demotable)
- Initial regime classifier and hypothesis catalog
- Hypothesis catalog H1-H23 with bootstrap CI framework
- CLI: ingest, baselines, leaderboard, eda
- Leaderboard artifact generation (P5)

### Onda 2: Prove Value (complete after fresh 2026-06-05 artifacts)

- Feature validation: walk-forward bootstrap CI + FDR on H1-H23
- Best-null-per-CP computed inside each walk-forward split
- Calibrated train-only CP null included in the validation gates
- Baseline+feature nulls in leaderboard
- **Gate:** At least one feature must beat the best null baseline with validated
  CI and pass all gates. If no feature passes G1-G5, Onda 3 is blocked.

### Onda 2R: Regime Ontology Repair (implemented / R2 rerun blocking)

Onda 2R repairs a flaw discovered by Onda 4: the old regime ontology treated
`late_warming = tmax_hour >= 18` as a causal regime, but this is an ex-post
timing outcome. Onda 2R must separate causal physical regimes from late-Tmax
risk labels, revalidate affected features, and then rerun Onda 4.

As of the 2026-06-06 rerun, Onda 2R is implemented in code and regenerated
artifacts. The old `late_warming` structural failure is gone, but Onda 4 R2 now
blocks on dead physical regimes: `calm_radiative` and `standard_nw`.

Gate: Onda 3 cannot start until the rerun Onda 4 passes with no dead causal
physical regime.

### Onda 2E: Wellington Climatology Thesis Atlas (in progress)

Onda 2E exists because the project repeatedly found that prior regime and
feature choices were too superficial. It studies the official 251-thesis
Wellington climatology atlas in `reports/onda2e/thesis_atlas_v1.md`.

Onda 2E is not a feature factory. It is a decision-producing climatology wave.
Each thesis must be proved, rejected, adapted, or blocked by data before it can
influence downstream work.

### Onda 2E-Gate: Evidence-to-Decision Framework (implemented; review required)

Before any Onda 2E finding can change a regime, enter feature design, justify a
model input, or drive an Onda 4 repair, it must pass ADR-012.

Required decision statuses are `SUPPORTED`, `REJECTED`, `ADAPTED`, `BLOCKED`,
`PROMOTED_TO_REGIME_DESIGN`, `PROMOTED_TO_FEATURE_CANDIDATE`, and
`QUARANTINED_BASELINE`.

This gate explicitly quarantines the current heuristic regime classifier. It
can remain as a diagnostic comparator, but it is not final climatological truth.
Fixed rules such as `tmax_hour >= 18`, broad `min_delta_t_per_h < -2` cooling,
or fixed foehn thresholds cannot be retained as production definitions unless
the evidence register says so.

Generated 2026-06-07 artifacts:

- `reports/onda2e/evidence_decision_register.csv`
- `reports/onda2e/regime_design_queue.csv`
- `reports/onda2e/feature_candidate_queue.csv`
- `reports/onda2e/rejection_register.csv`
- `reports/onda2e/quarantined_baseline_register.csv`
- `reports/onda2e/onda2e_decision_report.md`

The gate generated on 2026-06-07 currently has 250 evidence-decision rows: 245
active thesis decisions and 5 baseline-rule decisions. The 6 theses requiring
unavailable external data were removed from the active ADR-012 universe and
recorded in `reports/onda2e/removed_external_theses.csv`. Active decision
counts are `ADAPTED` 48, `PROMOTED_TO_REGIME_DESIGN` 4,
`QUARANTINED_BASELINE` 2, `REJECTED` 22, and `SUPPORTED` 174; there are 0
active `BLOCKED` thesis decisions.

Implemented domain EDA now covers `TIMING`, `COOLING`, `FOEHN`, `WIND`, thesis
domain evidence, and regime architecture. Regime-design promotions are
`WCT-COOL-003`, `WCT-FOEHN-001`, `WCT-WIND-019`, and `WCT-REGIME-016`.
Adapted diagnostic comparators are `RULE_LATE_WARMING_FIXED_18`,
`RULE_COOLING_FIXED_MINUS_2_C_PER_H`, and `RULE_FOEHN_SCORE_FIXED_60`; none of
these fixed rules is production truth.

Active quarantined decision rows are `REGIME_CLASSIFIER_CURRENT` and
`RULE_ONDA2R_PHYSICAL_REGIME_FAMILY`. The separate
`quarantined_baseline_register.csv` still has 5 baseline comparator rows, so it
must not be confused with the active quarantine count in the decision register.
The regime design queue has 9 items: 5 baseline comparators plus the four
promoted thesis decisions. `feature_candidate_queue.csv` is empty and
`rejection_register.csv` has 22 items.

`WCT-REGIME-016` has an offline regime-design validation path through
`tmax regime-design-validate`, which writes `reports/regime-design/` and does
not mutate `data/features.parquet` or the production classifier. The 2026-06-07
screening assigned 21,824/21,824 feature rows with 0 null candidate labels, but
R2 still found 2 dead candidate families: `candidate_maritime_cloudy` and
`candidate_mixed_or_transition`. This is regime-design evidence only, not a
production unblock.

Gate: this is not a modeling unblock and does not promote any production
feature, model input, regime classifier, or regime ontology. Onda 3 remains
blocked. Onda 4 repair work must use these queues for data-backed
robustness/regime repair, then rerun the gates.

### Onda 3: Models (blocked)

- ML models: LightGBM, quantile regression, NWP integration
- Model ladder: model beats best feature-null at each CP
- Hyperparameter tuning within causal firewall
- Ensemble blending
- **Gate:** Model must beat best feature-null on walk-forward holdout. No model
  without validated features and a passed Onda 4 robustness report.

### Onda 4: Robustness Hardening (implemented; post-Onda 2R NO-GO)

Onda 4 is a model-foundation hardening wave. It stress-tests Onda 2's validated
feature-null claims before any Onda 3 production model work. It does not create
a financial layer.

The first full Onda 4 run completed on 2026-06-06. It produced a report and
artifacts, but returned NO-GO because R2 found `late_warming` as a dead regime.
That result is retained as the pre-Onda 2R ontology failure.

The post-Onda 2R rerun on regenerated artifacts also returned NO-GO, now
because R2 found no passing feature for `calm_radiative` and `standard_nw`.
This blocks Onda 3 until the physical-regime segmentation and feature evidence
are strong enough to pass without injecting ex-post timing labels.

Financial execution, EV, position sizing, shadow trading, Polymarket API work,
and production deployment are explicitly on hold. The active objective is a
predictive model with real skill, calibrated uncertainty, and stay-out behavior,
not a nowcast or market-execution system.

Scope:

- Per-test-year replication: confirm features work across years, not only in a
  pooled holdout.
- Regime sensitivity: verify skill by causal physical regimes, not ex-post
  timing outcomes.
- Drift trend: detect calendar-time degradation in feature-null skill.
- Causal re-audit: verify every validated feature still respects the temporal
  firewall.
- Fresh gate re-run: G1-G5 must still pass on fresh artifacts.
- Anti-nowcast lead-time check: skill must exist before the answer is
  effectively known.
- Physical Tmax-hour stratification: evaluate by regime/month/Tmax-hour buckets
  so fixed CPs do not force non-physical conclusions.
- Late-spike evidence pack: preserve cases where `k_cp` looked settled but the
  final Tmax increased later. These cases inform future modeling, especially
  Open-Meteo/NWP research.

Entry gate:

1. Onda 2 fresh artifacts exist and are not marked superseded.
2. `ruff check .` and `uv run pytest -q -m "not network"` pass.
3. The current validated-feature count is read from
   `validated_feature_contract.json`; plans must not hard-code stale counts.

Exit gate:

1. Per-year replication has enough passing years.
2. No causal physical regime is dead.
3. Causal re-audit has zero violations.
4. Fresh G1-G5 gates pass.
5. Skill is not concentrated only after Tmax is effectively known.
6. Fixed CP timing is shown not to be the source of apparent skill.

Go: Onda 3 model planning may proceed only if no intervening wave or ADR gate
is active. When an intervening wave exists, such as Onda C for regime
classifiability/topology after Opcao A, that wave must pass first.
No-Go: Onda 3 remains blocked until the root cause is fixed and the robustness
report reruns.

### Out of Scope Until Separate ADR

- Live trading execution.
- Real-money position sizing.
- Automated deployment to production.
- Shadow trading, EV, market-pricing, or Polymarket API work before a model
  passes Onda 3 gates.

## Wave Gate Rules

Each Onda N must satisfy:

1. All gates from Onda N-1 still pass (no regression).
2. The Onda N deliverable beats the best deliverable from Onda N-1 on the
   walk-forward holdout.
3. No feature or model is promoted without validated CI excluding zero and all
   gates passing.
4. No EDA finding, regime definition, or candidate feature is promoted without
   an ADR-012 decision record and artifact reference.

## Alternatives Considered

1. **Single epic build:** Build the full pipeline (data + features + models +
   trading) in one go. Rejected: this is what the old project did, and it masked
   foundation bugs until there was no time to fix them.
2. **Model-first:** Start with models and backfill baselines later. Rejected:
   without baselines, there is no null to beat. You cannot know if a model is
   good or lucky.
3. **Waterfall (rigid phases):** Each wave must be 100% complete before starting
   the next. Rejected: cross-wave feedback should feed back immediately.
4. **Trading as Onda 4:** Rejected for the current project state. Onda 4 must
   prove robustness before models; financial work starts only after the model
   gate passes and a separate ADR accepts that scope.

## Consequences

### Enabled

- Each wave validates its dependents: features are only as good as the baselines
  they beat; models are only as good as the features they use.
- Clear go/no-go decisions: Onda 2 must prove features add value before Onda 3
  invests in modeling.
- The baseline ladder serves as a permanent performance floor: no model can
  claim victory without beating L0-L4.
- Onda 4 has a concrete robustness path without silently enabling financial
  work.
- EDA results become project decisions instead of unused reports.

### Prevents

- Building models on unvalidated features (the old project's core mistake).
- Shipping without knowing whether the foundation works.
- Premature optimization of model architecture when feature engineering is the
  bottleneck.
- Treating stale or superseded reports as decision evidence.
- Keeping hardcoded meteorological rules by inertia after data contradicts or
  fails to support them.

## References

- `CHANGELOG.md` -- Wave completion entries
- `ROADMAP.md` -- living project roadmap
- `docs/onda4_robustness_plan.md` -- Onda 4 robustness scope
- `docs/decisions/012-evidence-to-decision-gate.md` -- EDA decision gate
- `solarstorm/__init__.py` -- package version
