# Changelog

**Onda** (Portuguese: "wave") is the phased development methodology used by
SolarStorm. Each onda depends on and validates the previous. See
[ADR-010](docs/decisions/010-onda-waves.md).

---

## [Unreleased] - 2026-06-09

### Added

- Added Onda 3 baseline-first design spec:
  `docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md`.
- Added Onda 3 baseline-first implementation plan:
  `docs/superpowers/plans/2026-06-09-onda3-baseline-model.md`.
- Added `solarstorm.onda3` with causal feature manifest, design matrix audit,
  NumPy ridge challenger, slice diagnostics, uncertainty/abstention reporting,
  artifact writer, and `onda3-baseline-model` CLI.
- Generated the first Onda 3 baseline artifacts under `reports/onda3/`.

### Changed

- Updated ADR-012, ROADMAP, Onda 4 robustness plan, and regime model card to
  record that the binary macro candidate is eligible for Onda 3 design review
  while production remains blocked.
- Documented that `macro_non_southerly` must be modeled with continuous
  EDA-derived features and slice diagnostics because its R2 sensitivity remains
  weak.
- Recorded the first Onda 3 baseline result as `EXPERIMENT_ONLY`: train-mean
  null MAE 2.8120, ridge challenger MAE 1.3487, and decision
  `READY_FOR_ONDA4_MODEL_RERUN`.

### Fixed

- Fixed the binary macro validation gate so train/test splits with insufficient
  class variation no longer receive a fabricated `predictive_auc = 1.0`; they
  now block as `BLOCKED_INSUFFICIENT_CLASS_VARIATION`.
- Fixed Onda 3 ridge challenger handling of missing numeric features by using
  train-window mean imputation before fitting and prediction.

---

## [Unreleased] - 2026-06-08

### Added

- **Regime Deadlock Pivot** — formally records that the v2.2/v2.3/CEXP
  threshold-restoration loop is superseded as the active Onda 3 unlock path.
  Evidence: `train_only_gmm` stability 0.0799, 82% low-confidence share,
  0/92 R2 pass rows for `macro_calm_radiative` across all versions.
- Added `solarstorm/onda2e/_regime_deadlock_pivot.py` with
  `build_regime_deadlock_pivot_artifacts` and `write_regime_deadlock_pivot_artifacts`.
  Generates: decision record, audit-demotion table, superseded-path table.
- Added `solarstorm/onda2e/_regime_binary_macro_candidate.py` with
  `build_regime_binary_macro_candidate_artifacts`. Collapses 3-macro surface to
  `macro_southerly_flow` + `macro_non_southerly` (experiment-only).
- Added `solarstorm/onda2e/_cloud_cover_baseline_experiment.py` with
  `build_cloud_cover_baseline_experiment`. Walk-forward OLS baseline comparison
  using `cloud_cover_suppression` independent of regime resolution.
  Result: 96 rows (2024-2025, 4 CPs). All `EXPERIMENT_ONLY`.
- Added CLI commands: `regime-deadlock-pivot`, `regime-binary-macro-candidate`,
  `cloud-cover-baseline-experiment`.
- Updated `ADR-012`, `docs/regime_model_card.md`, and `ROADMAP.md` to record
  the pivot as the active path and block v2.4 threshold tuning.

### Changed

- `macro_calm_radiative` demoted from production-blocking macro to audit-only
  segment. Production-blocking set is now `macro_nw_continuum` and
  `macro_southerly_flow` only.

---

## [Unreleased] - 2026-06-05

### Added

- Added `solarstorm.robustness` for Onda 4 hardening: per-year replication,
  regime sensitivity, drift trend, causal re-audit, anti-nowcast lead-time
  analysis, Tmax-hour stratification, late-spike evidence, and markdown
  go/no-go reporting.
- Added `python -m solarstorm robustness` CLI with real artifact hashing and
  outputs under `reports/robustness/`.
- Added ADR-011 and the Onda 2R regime ontology repair plan, separating causal
  physical regimes from ex-post late Tmax timing events.
- Added `docs/regime_ontology_design.md` as the design reference for causal
  regimes, late-Tmax targets, and Onda 4 R2/R7/R9 semantics.
- Added `docs/regime_model_card.md` and
  `reports/regime/2026-06-06-regime-clustering-report.md` for the Onda 2R
  regime evidence/model-card trail.
- Added `python -m solarstorm regime-diagnostics` cooling-rule experiment
  artifacts under `reports/regime/`.
- Added `python -m solarstorm onda2e` to parse the official
  `reports/onda2e/thesis_atlas_v1.md` base atlas, audit thesis testability, and
  generate prerequisite EDA tables for Onda 2E.
- Added Onda 2E monthly wind-rose and cooling-mechanism taxonomy prerequisite
  artifacts, generated from pre-CP METAR observations.
- Added ADR-012 Evidence-to-Decision Gate and P6 (`Evidence Must Become
  Decisions`) so Onda 2E findings cannot become unused reports or be promoted
  by intuition.
- Added Onda 2E-Gate artifact generation to `python -m solarstorm onda2e`:
  `evidence_decision_register.csv`, `regime_design_queue.csv`,
  `feature_candidate_queue.csv`, `rejection_register.csv`,
  `quarantined_baseline_register.csv`, and `onda2e_decision_report.md`.
- Added Onda 2E timing-domain and cooling-regime domain artifacts:
  `domain_timing_*`, `onda2e_timing_report.md`,
  `cooling_event_taxonomy_by_day_cp.csv`,
  `cooling_effects_by_month_regime_cp.csv`,
  `cooling_power_leakage_audit.csv`, `regime_repair_candidates.csv`, and
  `cooling_regime_domain_report.md`.
- Added Onda 2E FOEHN and WIND domain artifacts, including
  `domain_foehn_score_bins_by_month_cp.csv`, `foehn_false_positive_audit.csv`,
  `foehn_regime_repair_candidates.csv`, `foehn_domain_report.md`,
  `wind_direction_reliability_by_day_cp.csv`,
  `wind_sector_effects_by_month_cp.csv`, `wind_regime_repair_candidates.csv`,
  and `wind_domain_report.md`.

### Changed

- Onda 4 is now defined as robustness hardening, not readiness/shadow-decision
  work. Financial execution, EV, position sizing, shadow trading, and
  Polymarket API work remain on hold until a production model proves predictive
  skill, calibrated uncertainty, and stay-out behavior.
- Added Onda 4 scope controls for anti-nowcast lead-time checks, physical
  Tmax-hour stratification, continuous METAR processing, and late-spike
  evidence for future Open-Meteo/NWP model research.
- Feature validation records the real train-only best null per CP/result slice,
  including calibrated CP mean remaining-warming nulls.
- `validated_feature_contract.json` includes `best_null_name` and
  `best_null_mae`.
- Leaderboard artifacts are timestamped (`YYYY-MM-DDTHHMMZ`) with `latest-*`
  convenience aliases.
- ADR-006 is superseded for promoted regime semantics. `late_warming` is now
  treated as a timing-risk target, not a causal regime.
- Replaced the promoted causal regime family with `calm_radiative`,
  `standard_nw`, `strong_nw_foehn`, and `southerly_disrupted`.
- Onda 4 R7/R9 now audits month/regime Tmax timing norms and a separate
  late-Tmax risk baseline.
- Intraday state changes are documented as future feature/risk descriptors,
  not new regime labels, until the base physical regimes pass R2.
- Onda 2E now treats `reports/onda2e/thesis_atlas_v1.md` as the official EDA
  base with 251 thesis IDs. The earlier design spec is retained as context, not
  the source of truth.
- Current and legacy regime rules are now documented as quarantined baselines
  unless ADR-012 decision records explicitly retain, adapt, reject, or replace
  them.
- The Onda 2E-Gate register generated on 2026-06-07 now has 256 rows: 251
  thesis decisions and 5 baseline-rule decisions. Decision counts are
  `ADAPTED` 3, `BLOCKED` 245, `PROMOTED_TO_REGIME_DESIGN` 3,
  `QUARANTINED_BASELINE` 2, and `SUPPORTED` 3.
- Onda 2E-Gate domain EDA now covers `TIMING`, `COOLING`, `FOEHN`, and `WIND`:
  `WCT-TIMING-001`, `WCT-COOL-001`, and `WCT-WIND-006` are `SUPPORTED`;
  `WCT-COOL-003`, `WCT-FOEHN-001`, and `WCT-WIND-019` are
  `PROMOTED_TO_REGIME_DESIGN`; and
  `RULE_LATE_WARMING_FIXED_18`, `RULE_COOLING_FIXED_MINUS_2_C_PER_H`, and
  `RULE_FOEHN_SCORE_FIXED_60` are adapted diagnostic comparators, not
  production truth.
- The Onda 2E-Gate regime design queue now has 8 items: 5 baseline comparators
  plus the three promoted thesis decisions. Feature candidate and rejection
  registers remain empty; no feature, model, classifier, or regime is promoted
  to production, and Onda 3 remains blocked pending data-backed Onda 4
  robustness/regime repair.
- Added the v2.2 calm/radiative restoration sprint. It writes
  `regime_candidate_assignments_v2_2.csv`, `regime_candidate_ontology_v2_2.csv`,
  `regime_calm_radiative_reassignment_audit_v1.*`,
  `regime_candidate_r2_validation_v2_2.csv`,
  `regime_candidate_v21_v22_comparison.csv`, and
  `regime_candidate_v22_validation_report.md`.
- Added the v2.3 calm/radiative failure diagnostic sprint. It writes
  `regime_calm_radiative_failure_diagnostics_v1.*` and
  `regime_v23_next_experiments.csv`, recording
  `CALM_RADIATIVE_VALIDATION_TARGET_GAP` as the current blocker.
- Added `CEXP-CALM-RADIATIVE-001` target diagnostics. It writes
  `regime_calm_radiative_target_diagnostics_v1.*` with train-window
  macro x month x CP remaining-warming and Tmax-hour target distributions.
- Added `CEXP-CALM-RADIATIVE-002` feature-hypothesis diagnostics. It writes
  `regime_calm_radiative_feature_hypotheses_v1.*`, screens 8 train-window
  calm-specific features, and records 1 preliminary candidate signal
  (`cloud_cover_suppression`) as `EXPERIMENT_ONLY`.
- Added `CEXP-CALM-RADIATIVE-002B` cloud-signal validation. It writes
  `regime_calm_radiative_cloud_signal_validation_v1.*` and records
  `SURVIVES_CAUSAL_ROBUSTNESS_SCREEN` for `cloud_cover_suppression`; CEXP-003
  demote/split is not triggered in the current train window.
- The active Onda C artifacts now evaluate v2.2 as the candidate under review.
  v2.2 restores `macro_calm_radiative` with 2,572 rows, but R2 blocks promotion
  because `macro_calm_radiative` has 0/92 passing R2 rows. The active Onda C
  verdict is `BLOCK_ONDA_C_PROMOTION`; Onda 3 remains blocked.
- v2.3 keeps Onda 3 blocked and converts the calm/radiative blocker into three
  experiment-only follow-ups: target diagnostics, calm-specific feature
  hypotheses, and macro-versus-subtype/split comparison.
- CEXP-001 found that calm/radiative has median p50 remaining warming of
  3.5 C across month x CP cells, but 20/48 calm/radiative cells are
  underpowered; CEXP-002 then found only one preliminary feature signal; and
  CEXP-002B validates that signal as pre-CP cloud evidence rather than
  proxy/artifact. The next step is an experiment-only baseline/validation pass
  for the surviving cloud signal, not Onda 3 promotion.

### Fixed

- Global `ruff check .` passes under the project CI settings.
- Replaced stale Onda 4 readiness/live-shadow docs with model-first robustness
  documentation.
- Prevented full-day late Tmax from overriding causal `regime_label` in feature
  generation.
- Regenerated `data/features.parquet`, validation artifacts, and Onda 4
  robustness artifacts under Onda 2R semantics.
- Reduced repeated full-data scans in `build_features` by partitioning
  observations by local date before the per-CP causal loop.
- Added a regime trigger diagnostic artifact showing that the current
  `southerly_disrupted` imbalance is driven by cooling triggers, not light
  precipitation.
- Added an offline cooling-rule experiment showing that removing cooling as a
  standalone disruption trigger would move 13,367 rows out of
  `southerly_disrupted`; this is diagnostic only and does not change production
  labels or gates.
- Added an Onda 2E registry audit that preserves 251 thesis entries, flags 6
  external-data blocks, and identifies 22 registry-detail gaps in the source
  atlas.
- Fixed Onda 2E cooling-rate calculations to use fractional hours from METAR
  minute deltas, preventing half-hour observations from being truncated to zero
  hours and creating false infinite/NaN cooling evidence.

### Pre-Onda 2R Onda 4 Result

- The 2026-06-06 robustness run produced
  `reports/robustness/2026-06-06-robustness-report.md` and returned NO-GO.
  R1, R3, R4, R5, R6, R7, and R8 passed; R2 blocked because the old regime
  ontology treated `late_warming` as a regime even though it is an ex-post
  timing event.

### Post-Onda 2R Onda 4 Result

- Fresh `features`, `validate`, and `robustness` artifacts were generated on
  2026-06-06. Validation produced 28 validated entries, 60 rejected, and 4
  blocked.
- The repaired Onda 4 report remains NO-GO. R1, R3, R4, R5, R6, R7, R8, and R9
  passed; R2 blocks because `calm_radiative` and `standard_nw` have no passing
  feature in the physical-regime sensitivity rerun.

## [v0.1.0] - 2026-06-05

### Documentation

- Created comprehensive documentation suite: architecture, principles, 10 ADRs,
  replication guide, bug register, glossary, feature contracts.
- Rewrote README with documentation index and quick-start commands.
- Organized CHANGELOG with version headers and Onda methodology definition.

## [v0.1.0-alpha] - 2026-06-04

### Added (Bridge: CLI wiring + leaderboard feature nulls)

- CLI `features` command: loads obs/labels, calls `build_features`, writes
  `features.parquet` and coverage manifest.
- CLI `validate` command: calls `validate_hypotheses`, exports
  hypothesis_results.json/md and validated_feature_contract.json.
- Extended `leaderboard` command: L1 (dminus1) via self-join, L4 (empirical
  conditional) via `predict_dist` mode, baseline+feature null rows from
  validated contract via OLS challenger.
- `export_leaderboard` supports `feature_nulls` in the board dict and UTF-8
  encoding on all `write_text` calls.

### Added (Onda 0+1 complete)

- METAR ingestion 2009-2026 (IEM ASOS, parquet cache).
- Labels: Tmax/CP, k_cp, remaining_warming, risco_de_flip, 24h scan.
- Baselines L0-L4: persistence, dminus1, climatology DOY+CP-month,
  empirical conditional.
- Walk-forward harness: expanding splits, holdout windows 7/14/30d.
- Frozen gates G1-G5 (G4 anti-nowcaster hard, non-demotable).
- Historical regime classifier: calm/transition/late_warming/foehn_nw/disrupted
  (superseded by Onda 2R for promoted semantics).
- Hypothesis catalog H1-H23 with bootstrap CI framework.
- CLI: ingest, baselines, leaderboard, eda.
- Leaderboard artifact: JSON+MD auto-generated per run (P5).

### Added (Project bootstrap)

- Repo scaffold, pyproject.toml, README, CHANGELOG.
- 122 passing non-network tests as of the Onda 4 robustness audit.
