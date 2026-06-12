# Changelog

**Onda** (Portuguese: "wave") is the phased development methodology used by
SolarStorm. Each onda depends on and validates the previous. See
[ADR-010](docs/decisions/010-onda-waves.md).

---

## [Unreleased] - 2026-06-12

### Added

- Implemented the P0 honest evaluation harness under `solarstorm/honest_eval/`
  plus the `honest-evaluation` CLI. The first full run generated
  `reports/honest-evaluation/` and kept Onda 3F blocked with
  `BLOCK_MODEL_PROMOTION_HONEST_NULL`; the persistence-block ablation reports
  MAE degradation of roughly +0.34/+0.32/+0.26 for 2023/2024/2025.
- Implemented the P1 horizon hybrid model in
  `solarstorm/onda3/_hybrid_iteration.py` plus the
  `onda3-hybrid-model-iteration` CLI. The first generated run wrote
  `reports/onda3-hybrid/`, judged all candidates with the P0 harness, produced
  zero physical-floor violations by construction, and returned
  `READY_FOR_P2_DISTRIBUTION_DESIGN` while remaining `EXPERIMENT_ONLY`.
- Added the forensic investigation v2 report
  (`reports/forensic-investigation-v2.md`): adversarial nowcast/leakage audit
  of the current repo with reproducible calculations. Key verified findings:
  the M3 train-mean null (MAE 2.812) is a strawman versus the honest
  `k_cp + train-only climatological remaining warming` null (MAE
  1.62/1.39/1.10/0.85 at CPs 20:00-23:00, beating Onda 3F at CP 23:00); at
  CP 23:00, 26.1% of days already realized Tmax and 62.0% have <= 1 C
  remaining; the M7 anti-nowcast gate is hardcoded PASS; the abstention rule
  is a non-executable string; `k_cp` never reaches the Onda 3F design matrix;
  6.8-9.0% of best-candidate predictions violate `prediction >= k_cp`;
  Open-Meteo policies repeat one prediction per day across all four CPs.
- Recorded that the earlier `reports/forensic-investigation-report.md` mixed
  evidence from the quarantined old project (CQR, LightGBM, "Fase 5",
  empirical serving) that does not exist in this repo, and that the untracked
  `solarstorm/serving/`, `solarstorm/calib/`, and `scripts/` files are
  unaudited drafts from that session.
- Added the Production Roadmap P0-P5 to `ROADMAP.md`, superseding the
  previous "next technical sprint order": P0 honest evaluation harness, P1
  horizon hybrid model (remaining-warming target, physical floor by
  construction, lead-aware NWP anchor), P2 calibrated distribution
  (EMOS/CRPS or Analog Ensemble), P3 late-spike risk plus executable
  abstention, P4 data expansion (OM-M15 + MetService Point Forecast API +
  UKMO/ACCESS-G), P5 realized-EV harness and shadow trading, with explicit
  exit gates from `EXPERIMENT_ONLY`.
- Added the P0 honest evaluation design spec and TDD implementation plan:
  `docs/superpowers/specs/2026-06-12-p0-honest-evaluation-design.md` and
  `docs/superpowers/plans/2026-06-12-p0-honest-evaluation.md` (gates H1-H4
  frozen ex-ante; pre-registered expectation that Onda 3F blocks on H1).
- Added the P1 horizon hybrid model design spec and TDD implementation plan:
  `docs/superpowers/specs/2026-06-12-p1-horizon-hybrid-model-design.md` and
  `docs/superpowers/plans/2026-06-12-p1-horizon-hybrid-model.md`
  (candidates `hybrid_local_only` and `hybrid_om_augmented`, judged by the
  P0 honest gates plus a pre-registered same-row MAE comparison on identical
  covered rows).

### Changed

- The next allowed technical work is P0, then P1. OM-M15 forward collection
  continues as the P4 data track. No production, EV, pricing, shadow trading,
  or execution work is unlocked.

### Fixed (post-implementation verification, 2026-06-12)

- The P1 decision gate in `judge_hybrid_candidates` now enforces the
  pre-registered spec success criterion 2: `READY_FOR_P2_DISTRIBUTION_DESIGN`
  additionally requires `hybrid_om_augmented` to beat
  `hybrid_local_only_covered_rows` on same-row overall MAE. The decision
  artifact now records `om_same_row_mae` (0.7263), `reference_same_row_mae`
  (0.9506) and `om_beats_reference_same_row`; the regenerated decision is
  unchanged (`READY_FOR_P2_DISTRIBUTION_DESIGN`). Previously the gate could
  promote an OM candidate that passed H1-H4 while losing to the local
  reference. Pinned by three new decision-matrix tests.
- `judge_hybrid_candidates` now rejects calls where any judged `test_year`
  falls inside the honest-null training window (`<= train_end_year`),
  preventing silent null leakage on misuse.
- Declared `scikit-learn>=1.4` in `pyproject.toml`: `solarstorm/onda2e/`
  imports sklearn but the dependency was never declared, so the full test
  suite was uncollectable in a clean `uv sync` environment (48 collection
  errors). Full suite after the fix: 512 passed.
- Independent numeric re-verification of the generated artifacts: P0 by-CP
  model/null MAEs, the 359 raw floor violations, and the walk-forward
  provenance of `onda3_pooled_predictions_v1.csv` all reproduce; P1 has zero
  predictions below `k_cp` for all three candidates and exact same-row
  alignment (2848 rows) between the OM candidate and the covered-rows
  reference. The OM anchor `om_prev_d1_day_max_c` alone scores MAE 1.42 with
  a -1.20 cold bias against realized Tmax — the signature of a genuine D-1
  `fixed_lead_forecast`, not leaked observations.
- Moved the unaudited drafts from the quarantined-project session
  (`solarstorm/serving/`, `solarstorm/calib/`, `scripts/`,
  `tests/test_in_play_monitor.py`, `tmp_forensic/`) into the gitignored
  `quarentena/` directory and removed the undocumented `forecast` CLI command
  that imported them. They remain on disk for a future audited P2/P5 rewrite
  but are not project infrastructure.

---

## [Unreleased] - 2026-06-10

### Added

- Added Onda 3 baseline-first design spec:
  `docs/superpowers/specs/2026-06-09-onda3-baseline-model-design.md`.
- Added Onda 3 baseline-first implementation plan:
  `docs/superpowers/plans/2026-06-09-onda3-baseline-model.md`.
- Added `solarstorm.onda3` with causal feature manifest, design matrix audit,
  NumPy ridge challenger, slice diagnostics, uncertainty/abstention reporting,
  artifact writer, and `onda3-baseline-model` CLI.
- Generated the first Onda 3 baseline artifacts under `reports/onda3/`.
- Added Onda 4 model robustness review design spec:
  `docs/superpowers/specs/2026-06-09-onda4-model-robustness-review-design.md`.
- Added Onda 4 model robustness review implementation plan:
  `docs/superpowers/plans/2026-06-09-onda4-model-robustness-review.md`.
- Added `solarstorm.robustness._model_review` and the
  `onda4-model-review` CLI to evaluate Onda 3 model artifacts with M1-M8 model
  robustness gates.
- Generated the first Onda 4M model review artifacts under
  `reports/onda4-model/`.
- Added Onda 3B next-model-iteration design spec and implementation plan:
  `docs/superpowers/specs/2026-06-09-onda3-next-model-iteration-design.md`
  and `docs/superpowers/plans/2026-06-09-onda3-next-model-iteration.md`.
- Added `onda3-next-model-iteration` CLI with CP-specific ridge evaluation,
  train-only binary-macro one-hot encoding, predictions, slice diagnostics, and
  uncertainty/abstention outputs under `reports/onda3-next/`.
- Extended `onda4-model-review` with an artifact prefix option so Onda 4M can
  review both `onda3` and `onda3_next` artifact surfaces without overwriting
  earlier review outputs.
- Generated the Onda 4M review of Onda 3B under
  `reports/onda4-model-next/`.
- Added `onda3-rolling-model-iteration` CLI for Onda 3C rolling annual temporal
  validation and generated outputs under `reports/onda3-rolling/`.
- Generated the Onda 4M review of Onda 3C under
  `reports/onda4-model-rolling/`.
- Added `onda3-interaction-model-iteration` CLI for Onda 3D binary-macro
  interaction experiments and generated outputs under
  `reports/onda3-interactions/`.
- Generated the Onda 4M review of Onda 3D under
  `reports/onda4-model-interactions/`.
- Added `onda3-train-start-sensitivity` CLI for Onda 3E train-start sensitivity
  experiments comparing the sparse 2009-start local-data window with the
  continuous 2012-start window.
- Generated Onda 3E train-start sensitivity artifacts under
  `reports/onda3-train-start-sensitivity/`.
- Added `onda3-pooled-model-iteration` CLI for Onda 3F pooled temporal/regime
  experiments with CP and seasonality encoded as cyclic features.
- Generated Onda 3F pooled temporal/regime artifacts under
  `reports/onda3-pooled/`.
- Added `onda3-audit-comparison` CLI for Onda 3G audit comparison across
  persisted Onda 3D, Onda 3E, and Onda 3F local-data artifacts.
- Generated Onda 3G audit comparison artifacts under
  `reports/onda3-audit-comparison/`.
- Added Onda 3H nested validation design spec and implementation plan:
  `docs/superpowers/specs/2026-06-09-onda3h-nested-validation-design.md`
  and `docs/superpowers/plans/2026-06-09-onda3h-nested-validation.md`.
- Added `onda3-nested-validation` CLI for the pre-Open-Meteo nested
  walk-forward model-selection gate comparing Onda 3D and Onda 3F.
- Generated Onda 3H nested validation artifacts under
  `reports/onda3-nested-validation/`.
- Added the Open-Meteo availability-first design spec and implementation plan:
  `docs/superpowers/specs/2026-06-09-open-meteo-availability-first-design.md`
  and `docs/superpowers/plans/2026-06-09-open-meteo-availability-first.md`.
- Added `solarstorm.open_meteo` with source taxonomy, CP-to-UTC causality
  helpers, bounded probe planning, injectable HTTP client, availability
  summaries, blocked-source register, decision artifacts, and a no-features
  guard.
- Added `open-meteo-availability-audit` CLI. Plan-only mode writes audit
  artifacts without network access; live probing is explicit via `--live`.
- Generated the first Open-Meteo plan-only availability artifacts under
  `reports/open-meteo-availability/`.
- Added the Open-Meteo causal feature integration design spec and
  implementation plan:
  `docs/superpowers/specs/2026-06-10-open-meteo-causal-feature-integration-design.md`
  and
  `docs/superpowers/plans/2026-06-10-open-meteo-causal-feature-integration.md`.
- Added experiment-only Open-Meteo feature tooling:
  `open-meteo-fetch` for gated raw response caches and
  `open-meteo-build-features` for `data/open_meteo_features.parquet`.
- Added `onda3-open-meteo-pilot` to compare the local-only Onda 3 reference
  against an Open-Meteo-augmented candidate on identical covered rows.
- Generated the first gated Open-Meteo Previous Runs day-1 feature artifact
  under `data/open_meteo_features.parquet` and feature reports under
  `reports/open-meteo-features/`.
- Generated the first Onda 3 Open-Meteo pilot artifacts under
  `reports/onda3-open-meteo-pilot/`.
- Added the Open-Meteo multi-provider calibration sprint plan:
  `docs/superpowers/plans/2026-06-10-open-meteo-multi-provider-calibration-sprints.md`.
- Added `open-meteo-multi-provider-availability` with provider registry,
  bounded Previous Runs/Single Runs probe planning, plan-only/live probe
  execution, availability matrix, decision update, and report artifacts under
  `reports/open-meteo-multi-provider-availability/`.
- Added `open-meteo-provider-error-atlas` with raw provider prediction dataset,
  MAE/RMSE/signed-bias/exact-bracket metrics, support warnings, and report
  artifacts under `reports/open-meteo-provider-error-atlas/`.
- Added OM-M1 and OM-M2 TDD coverage:
  `tests/test_open_meteo_multi_provider_availability.py`,
  `tests/test_open_meteo_multi_provider_availability_cli.py`,
  `tests/test_open_meteo_provider_error_atlas.py`, and
  `tests/test_open_meteo_provider_error_atlas_cli.py`.
- Added `open-meteo-build-multi-provider-features` for OM-M3 historical
  Previous Runs expansion across provider families, with fixture/cache and live
  fetch paths.
- Added OM-M3 TDD coverage:
  `tests/test_open_meteo_multi_provider_features.py` and
  `tests/test_open_meteo_multi_provider_features_cli.py`.
- Generated the provider-keyed OM-M3 feature artifact under
  `data/open_meteo_multi_provider_features.parquet` and supporting reports
  under `reports/open-meteo-multi-provider-features/`.
- Generated the recalculated multi-provider provider-error atlas under
  `reports/open-meteo-provider-error-atlas-multi-provider/`.
- Added OM-M4 provider calibration tooling:
  `solarstorm/open_meteo/_provider_calibration.py`,
  `open-meteo-provider-calibration`, and TDD coverage in
  `tests/test_open_meteo_provider_calibration.py` and
  `tests/test_open_meteo_provider_calibration_cli.py`.
- Added OM-M5 calibrated nested-validation tooling:
  `solarstorm/open_meteo/_calibrated_nested.py`,
  `onda3-open-meteo-calibrated-nested-validation`, and TDD coverage in
  `tests/test_open_meteo_calibrated_nested.py` and
  `tests/test_open_meteo_calibrated_nested_cli.py`.
- Added OM-M6/OM-M8 forensic tooling:
  `solarstorm/open_meteo/_forensics.py`, `open-meteo-forensics`, and TDD
  coverage in `tests/test_open_meteo_forensics.py` and
  `tests/test_open_meteo_forensics_cli.py`.
- Added OM-M7 stabilized calibration candidates
  `om_family_month_bias_corrected` and
  `om_family_season_bias_corrected`, with bucket/fallback metadata and
  `open_meteo_stabilized_calibration_support_v1.csv`.
- Added OM-M8 defensive calibrated nested-selection mode
  `validation_mae_then_non_southerly_guard_then_cp23` and guardrail artifact
  `onda3_open_meteo_defensive_selection_guardrail_v1.csv`.
- Added OM-M10 coverage/fold expansion tooling:
  `solarstorm/open_meteo/_coverage_expansion.py`,
  `open-meteo-coverage-expansion`, and TDD coverage in
  `tests/test_open_meteo_coverage_expansion.py` and
  `tests/test_open_meteo_coverage_expansion_cli.py`.
- Added OM-M11 backfill feasibility tooling to the multi-provider feature
  builder, including `build_multi_provider_backfill_feasibility`,
  `--dry-run-feasibility`, report artifacts, and timeout-resilient live raw
  cache rows for failed provider/date windows.
- Added the OM-M11+ coverage expansion sprint plan:
  `docs/superpowers/plans/2026-06-10-open-meteo-coverage-expansion-next-sprints.md`.
- Added OM-M13 expanded-surface decision-review tooling:
  `solarstorm/open_meteo/_expanded_decision_review.py`,
  `open-meteo-expanded-decision-review`, and TDD coverage in
  `tests/test_open_meteo_expanded_decision_review.py` and
  `tests/test_open_meteo_expanded_decision_review_cli.py`.
- Added the OM-M14 live-forward Forecast API collection design and TDD plan:
  `docs/superpowers/specs/2026-06-11-open-meteo-forecast-forward-collection-design.md`
  and
  `docs/superpowers/plans/2026-06-11-open-meteo-forecast-forward-collection.md`.
- Added OM-M14 forward collection fixture-mode implementation:
  `solarstorm/open_meteo/_forward_collection.py`,
  `open-meteo-forward-collection`, fixture
  `tests/fixtures/open_meteo_forecast_fixture.json`, and TDD coverage in
  `tests/test_open_meteo_forward_collection.py`.
- Generated OM-M4 calibration artifacts under
  `reports/open-meteo-provider-calibration/`.
- Generated OM-M5 calibrated nested-validation artifacts under
  `reports/onda3-open-meteo-calibrated-nested-validation/`.
- Generated OM-M6 forensic artifacts under `reports/open-meteo-forensics/`.
- Generated OM-M7 stabilized calibration artifacts under
  `reports/open-meteo-provider-calibration-stabilized/`.
- Generated OM-M8 defensive selection artifacts under
  `reports/onda3-open-meteo-defensive-selection/`.
- Generated OM-M8 stabilized forensic artifacts under
  `reports/open-meteo-forensics-stabilized/`.
- Generated OM-M10 coverage/fold expansion artifacts under
  `reports/open-meteo-coverage-expansion/`.
- Generated OM-M11 2022 backfill artifacts under
  `reports/open-meteo-2022-backfill-feasibility/` and
  `reports/open-meteo-multi-provider-features-2022/`.
- Generated expanded 2022-2025 Open-Meteo feature surfaces:
  `data/open_meteo_multi_provider_features_2022_2025.parquet` and
  `data/open_meteo_features_2022_2025.parquet`, while preserving the original
  `data/open_meteo_multi_provider_features.parquet` and
  `data/open_meteo_features.parquet`.
- Generated OM-M12 refreshed artifacts under
  `reports/open-meteo-provider-error-atlas-2022-2025/`,
  `reports/open-meteo-provider-calibration-2022-2025/`,
  `reports/onda3-open-meteo-defensive-selection-2022-2025/`,
  `reports/open-meteo-forensics-2022-2025/`,
  `reports/open-meteo-forensics-2022-2025-season/`, and
  `reports/open-meteo-coverage-expansion-2022-2025/`.
- Generated OM-M13 policy-review artifacts under
  `reports/open-meteo-expanded-decision-review-2022-2025/`.
- Generated OM-M14 forward collection smoke artifacts under
  `reports/open-meteo-forward-collection/`.

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
- Updated project docs to make Onda 4 model robustness review the active next
  wave after the Onda 3 baseline. The review will use M1-M8 model gates,
  separate from historical R1-R9 regime/feature-null robustness, and will write
  under `reports/onda4-model/`.
- Recorded the first Onda 4M result as `EXPERIMENT_ONLY`: all M1-M8 gates pass
  and `onda4_model_decision_update_v1.csv` records
  `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Recorded the first Onda 3B result as `EXPERIMENT_ONLY`: all four CP-specific
  ridge challengers beat the CP train-mean null and
  `onda3_next_decision_update_v1.csv` records `READY_FOR_ONDA4_MODEL_RERUN`.
- Recorded the Onda 4M review of Onda 3B as `EXPERIMENT_ONLY`: M1-M8 all pass,
  M3 records null MAE 2.8120, challenger MAE 1.2708, lift 1.5411, and
  `onda4_model_decision_update_v1.csv` records
  `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Recorded the Onda 3C rolling temporal result as `EXPERIMENT_ONLY`: all 12
  year x CP ridge challengers beat their train-mean nulls across test years
  2023, 2024, and 2025.
- Recorded the Onda 4M review of Onda 3C as `EXPERIMENT_ONLY`: M1-M8 all pass,
  M3 records null MAE 2.9522, challenger MAE 1.2026, lift 1.7496, M4 records
  rolling temporal diagnostics for `2023,2024,2025`, and
  `onda4_model_decision_update_v1.csv` records
  `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Recorded the Onda 3D binary-macro interaction result as `EXPERIMENT_ONLY`:
  four continuous x macro interaction inputs were tested, all 12 year x CP
  challenger rows improved versus the Onda 3C no-interaction challenger, and
  mean MAE delta was -0.0300.
- Recorded the Onda 4M review of Onda 3D as `EXPERIMENT_ONLY`: M1-M8 all pass,
  M3 records null MAE 2.9522, challenger MAE 1.1726, lift 1.7796, M4 records
  rolling temporal diagnostics for `2023,2024,2025`, and
  `onda4_model_decision_update_v1.csv` records
  `READY_FOR_ONDA3_NEXT_MODEL_ITERATION`.
- Recorded the Onda 3E train-start sensitivity result as `EXPERIMENT_ONLY`:
  `continuous_2012_start` improves weighted challenger MAE by only 0.0021
  versus `legacy_2009_start`, while `any_cp_exact_pct` falls by 0.0912
  percentage points; decision status is
  `KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION`.
- Recorded the Onda 3F pooled temporal/regime result as `EXPERIMENT_ONLY`:
  weighted challenger MAE is 1.0619, daily `any_cp_exact_pct` is 44.4343%,
  final `23:00` exact rate is 31.4781%, and decision status is
  `READY_FOR_ONDA3_AUDIT_COMPARISON`.
- Recorded the Onda 3G audit comparison result as `EXPERIMENT_ONLY`: versus
  Onda 3D, Onda 3F changes MAE by -0.1107, daily `any_cp_exact_pct` by -0.7299
  percentage points, and final `23:00` exact rate by +1.5511 percentage points;
  decision status is `CARRY_ONDA3D_AND_ONDA3F_TO_NESTED_VALIDATION`.
- Recorded the Onda 3H nested validation result as `EXPERIMENT_ONLY`:
  validation selected Onda 3F for outer test years 2023, 2024, and 2025;
  selected mean test MAE is 1.0624 versus 1.1705 for always using Onda 3D, and
  decision status is `PROMOTE_NESTED_VALIDATION_AS_MODEL_SELECTION_HARNESS`.
- Recorded Open-Meteo integration as gated by availability and causality audit.
  Forecast API and Historical Weather are blocked as causal backtest inputs,
  Historical Forecast remains audit-only until run metadata is proven, Single
  Runs remains blocked by its current endpoint contract, and Previous Runs
  day-1 fixed-lead data is the first source allowed for experiment-only feature
  generation after a successful bounded live probe.
- Recorded the current Open-Meteo augmented pilot result as `EXPERIMENT_ONLY`:
  the daily all-CP pilot under `reports/onda3-open-meteo-pilot-daily-all-cp/`
  improved same-row MAE by -0.2801 versus the local-only reference on the
  covered 2024-2025 surface.
- Recorded the current Open-Meteo nested validation result as
  `EXPERIMENT_ONLY`: the run under
  `reports/onda3-open-meteo-nested-validation-daily-all-cp/` selected the
  Open-Meteo-augmented Onda 3F candidate in the only valid outer fold, with
  2025 test MAE 0.8508 versus 1.0809 for local-only on identical covered rows.
  Because coverage begins in 2023, the result advances only to the next
  experiment iteration and is not production evidence.
- Locked the next Open-Meteo direction to multi-provider availability,
  provider error/bias atlas, family-deduplicated ensemble calibration, and
  calibrated nested validation before any further model-complexity expansion.
- Updated the Open-Meteo multi-provider sprint plan to five steps: OM-M3 now
  explicitly builds a provider-keyed historical Previous Runs feature table
  before any family-deduplicated calibration or ensemble claim.
- Recorded OM-M1 live-smoke results as `EXPERIMENT_ONLY`: sampled
  `previous_runs` requests succeeded for GFS, ECMWF IFS, ECMWF AIFS, ICON,
  GEM, and JMA, while sampled `single_runs` requests returned HTTP 400 and
  remain blocked by request contract.
- Recorded OM-M2 provider-error atlas results as `EXPERIMENT_ONLY`: at the
  OM-M2 point-in-time, the historical feature table still contained only GFS
  Previous Runs rows, so the first atlas was GFS-only with 4,304 provider-error
  rows and 198 metric rows.
- Recorded OM-M3 historical multi-provider Previous Runs results as
  `EXPERIMENT_ONLY`: `data/open_meteo_multi_provider_features.parquet` covers
  2023-01-01 through 2025-12-31 with 26,304 provider-keyed rows, 1,096 dates,
  four CPs, and six provider families.
- Recorded the recalculated multi-provider atlas as `EXPERIMENT_ONLY`: 18,440
  non-null provider-error rows and 873 metric rows. Overall raw MAE ranks
  `icon_seamless` best at 1.0844 C, followed by `gem_global` at 1.1674 C,
  `ecmwf_ifs025` at 1.3987 C, `gfs_seamless` at 1.4207 C,
  `ecmwf_aifs025_single` at 1.7495 C, and `jma_seamless` at 1.7867 C.
- Updated the Open-Meteo sprint direction so the next technical work starts at
  OM-M4A raw family-deduplicated candidates, then OM-M4B signed-bias
  calibration, then OM-M5 calibrated nested validation.
- Recorded OM-M4 provider calibration as `EXPERIMENT_ONLY`: 26,224 candidate
  rows across raw GFS, raw family mean/median, inverse-MAE weighted, recent
  signed-bias-corrected, and regime-bias-corrected candidates. The best
  calibration-table candidate is `om_family_recent_bias_corrected` with MAE
  0.8225 C, signed bias -0.2741 C, and exact-bracket rate 38.41%.
- Recorded OM-M5 calibrated nested validation as `EXPERIMENT_ONLY`: the strict
  common-row comparison includes local-only Onda 3F, current
  `open_meteo_augmented_onda3f`, raw GFS Previous Runs, and calibrated
  multi-provider candidates. Only one outer fold is valid, so the decision is
  `KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW` even though validation
  selected `om_family_recent_bias_corrected`.
- Locked the next Open-Meteo work to OM-M6-style forensics: explain the gap
  between calibrated provider candidates and current GFS-augmented Onda 3F,
  investigate whether more causal coverage can create at least two strict
  common-row outer folds, and keep production/EV/pricing/execution blocked.
- Recorded OM-M6 forensics as `EXPERIMENT_ONLY`: paired 2024-2025 same-row
  MAE for `om_family_recent_bias_corrected` was 0.7726 C versus 0.7610 C for
  `open_meteo_augmented_onda3f`; exact bracket was 40.45% versus 41.75%, and
  the critical failure slice was `2025|macro_non_southerly` with MAE delta
  +0.1065 C and exact delta -6.47 pp.
- Recorded OM-M7 stabilized calibration as `EXPERIMENT_ONLY`: monthly and
  seasonal bucket corrections were generated with causal history and support
  audit metadata. `om_family_season_bias_corrected` was the strongest
  stabilized candidate for balanced paired forensics, but not enough to
  promote.
- Recorded OM-M8 defensive selection as `EXPERIMENT_ONLY`: the non-southerly
  validation guardrail blocks candidates that degrade validation
  `macro_non_southerly`, but the available validation fold still lets
  `om_family_recent_bias_corrected` through because its 2024 non-southerly
  slice looks strong. The guardrail therefore cannot resolve 2025 drift with
  only one strict common-row outer fold.
- Recorded OM-M8 stabilized forensics as `EXPERIMENT_ONLY`: compared with
  `open_meteo_augmented_onda3f`, `om_family_season_bias_corrected` nearly ties
  overall MAE, 0.7619 C versus 0.7610 C, and improves exact bracket by
  +0.81 pp, but fails the success gate because 2025 MAE worsens by +0.0200 C
  and `2025|macro_non_southerly` exact drops by -2.55 pp.
- Recorded OM-M9 decision:
  `KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE`. Stabilized
  calibration is not promoted; production, EV, pricing, shadow trading, and
  execution remain frozen.
- Recorded OM-M10 coverage/fold expansion as `EXPERIMENT_ONLY`: current strict
  common-row Open-Meteo coverage spans 2023-01-01 through 2025-12-31 with
  1,076 common dates and 4,304 common rows, yielding only one valid outer fold.
  A causal Previous Runs backfill beginning 2022-01-01 is the audited path to
  two folds; alternate fixed leads do not expand dates, and Single Runs remains
  blocked by request contract after 24/24 HTTP 400 sampled probes. Decision is
  `COVERAGE_EXPANSION_REQUIRES_2022_HISTORY`.
- Recorded OM-M11 historical backfill feasibility as `EXPERIMENT_ONLY`:
  dry-run decision is `OPEN_METEO_2022_BACKFILL_FEASIBILITY_READY`; live
  Previous Runs backfill for 2022 produced 8,760 multi-provider rows, 365
  dates, four CPs, six provider families, and no overwrite of the current
  Open-Meteo feature parquets.
- Recorded OM-M12 expanded two-fold refresh as `EXPERIMENT_ONLY`: coverage
  decision is `CURRENT_COVERAGE_SUPPORTS_TWO_STRICT_FOLDS` with 1,441 common
  dates, 5,764 strict common rows, and two valid outer folds. Defensive nested
  validation selects `om_family_season_bias_corrected` for 2024 and
  `om_family_recent_bias_corrected` for 2025, with selected mean test MAE
  0.7824 versus 0.8244 for always using `open_meteo_augmented_onda3f`.
- Recorded OM-M13 expanded-surface decision review as `EXPERIMENT_ONLY`.
  Decision is
  `PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`: selected
  policy MAE is 0.7835 versus 0.8239 for always-augmented, exact bracket
  improves by +1.30 pp, CP23 exact is unchanged, and both binary macro regimes
  improve in MAE. `always_season` is the strongest global observed policy at
  MAE 0.7616, so it must accompany the nested-selected policy in the next
  experiment-only iteration. Production, EV, pricing, shadow trading, and
  execution remain frozen.
- Recorded OM-M14 forward collection as `EXPERIMENT_ONLY`: fixture-mode writes
  a raw response cache manifest, normalized provider-feature parquet,
  maturity audit, causality audit, endpoint/model/horizon availability audit,
  duplicate-key report, and collection report. The generated smoke row is
  `pending`, passes `available_time_utc <= cp_utc`, and is excluded from
  nested validation until labels settle and the row becomes `mature`.
  Production, EV, pricing, shadow trading, and execution remain frozen.

### Fixed

- Fixed the binary macro validation gate so train/test splits with insufficient
  class variation no longer receive a fabricated `predictive_auc = 1.0`; they
  now block as `BLOCKED_INSUFFICIENT_CLASS_VARIATION`.
- Fixed Onda 3 ridge challenger handling of missing numeric features by using
  train-window mean imputation before fitting and prediction.
- Fixed Onda 4M challenger-lift gate aggregation so M3 blocks when any
  challenger row fails its train-mean null instead of checking only the first
  row.
- Fixed Onda 4M temporal gate reporting so M4 records optional rolling temporal
  diagnostics instead of always describing a single-year review.
- Fixed Onda 3F pooled temporal/regime robustness for edge inputs: CP values are
  normalized to canonical `HH:MM` before cyclic encoding and CLI assignment
  joins, and requested test years with no valid train/test fold now produce a
  controlled `KEEP_IN_ONDA3_EXPERIMENT_REVIEW` decision instead of a schema
  error.
- Fixed Onda 3G audit-comparison robustness after review: brackets are
  recomputed from `actual`/`prediction` regardless of persisted upstream
  bracket columns, all four canonical model surfaces are required, feature joins
  validate unique `date_local, cp` keys, and top-quartile feature slices now use
  top-25% row cardinality inside the audited prediction universe.
- Fixed Onda 3H robustness after review: the CLI now requires the binary macro
  assignment artifact, feature selection uses an explicit Onda 3H allowlist
  instead of the permissive generic manifest, and `cp23` summaries expose
  denominator fields before using final `23:00` exact rate as a tie-break
  guardrail.
- Fixed the Open-Meteo availability audit no-features guard so the audit still
  refuses report-local feature parquet output while coexisting with a
  previously generated gated `data/open_meteo_features.parquet`.
- Fixed Previous Runs multi-provider fetching to use date windows instead of
  duplicate per-CP daily requests, and made raw-cache parsing range-aware while
  preserving compatibility with older single-date cache rows.
- Fixed the provider error atlas input contract so it accepts both the original
  GFS-only schema (`om_endpoint`, `om_model`) and the OM-M3 provider-keyed
  schema (`endpoint`, `model`).
- Fixed OM-M5 candidate comparison to require identical covered rows across
  local-only Onda 3F, current GFS-augmented Onda 3F, raw GFS Previous Runs, and
  all calibrated candidates before counting a nested fold as valid.

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
