# Open-Meteo Stabilized Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize Open-Meteo calibration after OM-M6 by testing less-global bias corrections and a defensive selector that falls back to `open_meteo_augmented_onda3f` when calibrated candidates degrade `macro_non_southerly`.

**Architecture:** Keep the current Onda 3F local baseline, current Open-Meteo augmented baseline, and OM-M4/OM-M5 artifacts immutable. Add experiment-only OM-M7 candidates and OM-M8 selection diagnostics on top of existing provider calibration and calibrated nested-validation modules. No production, pricing, EV, or execution behavior is unlocked by these sprints.

**Tech Stack:** Python 3.12, Polars, NumPy ridge utilities already used by `solarstorm.onda3`, Typer, pytest, Ruff.

---

## Current State

- `open_meteo_augmented_onda3f` is the current strongest integrated experimental baseline.
- OM-M6 showed calibrated `om_family_recent_bias_corrected` is not uniformly bad, but unstable:
  - 2024 improves vs augmented: MAE delta `-0.0423 C`, exact delta `+0.36 pp`.
  - 2025 degrades vs augmented: MAE delta `+0.0628 C`, exact delta `-2.88 pp`.
  - Worst critical slice: `2025|macro_non_southerly`, MAE delta `+0.1065 C`, exact delta `-6.47 pp`.
- The next work must remain `EXPERIMENT_ONLY`.

Implementation status on 2026-06-10:

- OM-M7A is implemented with TDD. Stabilized candidates
  `om_family_month_bias_corrected` and
  `om_family_season_bias_corrected` are generated under
  `reports/open-meteo-provider-calibration-stabilized/`.
- OM-M7B is implemented with TDD. Support/fallback audit output
  `open_meteo_stabilized_calibration_support_v1.csv` is generated and flags
  support/adjustment risks by year, month, season, CP, and binary macro regime.
- OM-M8A is implemented with TDD. The defensive selector mode
  `validation_mae_then_non_southerly_guard_then_cp23` and guardrail artifact
  `onda3_open_meteo_defensive_selection_guardrail_v1.csv` are generated under
  `reports/onda3-open-meteo-defensive-selection/`.
- OM-M8B is implemented. Stabilized nested revalidation and paired forensics
  are generated under `reports/onda3-open-meteo-defensive-selection/` and
  `reports/open-meteo-forensics-stabilized/`.
- OM-M9 is implemented. Decision:
  `KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE`. Stabilized
  calibration is not promoted because it fails the success gate despite
  improving exact bracket modestly.

## Sprint Sequence

| Sprint | Name | Primary Question | Measurable Exit Artifact |
| --- | --- | --- | --- |
| OM-M7A | Monthly and seasonal bias candidates | Does less-global causal calibration reduce the 2025 `macro_non_southerly` failure without losing 2024 gains? | `reports/open-meteo-provider-calibration-stabilized/` |
| OM-M7B | Calibration support audit | Are monthly/seasonal corrections supported enough to trust, or are they just smaller overfit buckets? | `open_meteo_stabilized_calibration_support_v1.csv` |
| OM-M8A | Defensive selector | Can the selector choose calibrated candidates only when validation proves `macro_non_southerly` stability, otherwise falling back to augmented Onda 3F? | `reports/onda3-open-meteo-defensive-selection/` |
| OM-M8B | Nested revalidation and forensics refresh | Does the new candidate/selector improve same-row results versus current augmented and current calibrated baselines? | `reports/open-meteo-forensics-stabilized/` |
| OM-M9 | Decision gate | Should stabilized calibration advance, stay in review, or be rejected in favor of augmented Onda 3F? | Updated decision row in roadmap/changelog |

---

## Sprint OM-M7A: Monthly and Seasonal Bias Candidates

**Files:**
- Modify: `solarstorm/open_meteo/_provider_calibration.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_open_meteo_provider_calibration.py`
- Test: `tests/test_open_meteo_provider_calibration_cli.py`
- Generate: `reports/open-meteo-provider-calibration-stabilized/`

**Deliverables:**
- Add candidate `om_family_month_bias_corrected`.
- Add candidate `om_family_season_bias_corrected`.
- Add candidate metadata columns:
  - `calibration_bucket`
  - `calibration_bucket_type`
  - `fallback_reason`
  - `bias_samples`
  - `bias_adjustment`
- Preserve existing OM-M4 candidates unchanged.

**Measurable Exit Criteria:**
- Candidate table contains both new candidate IDs across covered 2023-2025 rows.
- All new rows have `production_status = EXPERIMENT_ONLY`.
- No duplicate `(date_local, cp, candidate_id)` keys.
- New candidates have support/fallback metadata for 100% of rows.
- Tests:
  - `uv run pytest tests/test_open_meteo_provider_calibration.py tests/test_open_meteo_provider_calibration_cli.py -q`
  - `uv run ruff check solarstorm/open_meteo tests/test_open_meteo_provider_calibration.py tests/test_open_meteo_provider_calibration_cli.py`

**Initial Technical Defaults:**
- Monthly correction:
  - bucket: calendar month number.
  - lookback: previous 730 days.
  - min samples: 60.
  - shrinkage denominator: 60.
  - max absolute adjustment: `1.25 C`.
- Seasonal correction:
  - buckets: DJF, MAM, JJA, SON.
  - lookback: previous 730 days.
  - min samples: 90.
  - shrinkage denominator: 90.
  - max absolute adjustment: `1.25 C`.
- Fallback:
  - if bucket support fails, fall back to raw family mean, not global recent bias.

---

## Sprint OM-M7B: Calibration Support Audit

**Files:**
- Modify: `solarstorm/open_meteo/_provider_calibration.py`
- Test: `tests/test_open_meteo_provider_calibration.py`
- Generate: `reports/open-meteo-provider-calibration-stabilized/open_meteo_stabilized_calibration_support_v1.csv`

**Deliverables:**
- Support report by:
  - candidate ID
  - year
  - month
  - season
  - CP
  - binary macro regime
- Columns:
  - `n_rows`
  - `mean_bias_samples`
  - `min_bias_samples`
  - `fallback_pct`
  - `mean_abs_bias_adjustment`
  - `production_status`

**Measurable Exit Criteria:**
- Report proves whether each bucket has enough support.
- Any bucket with `fallback_pct > 40%` is explicitly flagged.
- Any bucket with `mean_abs_bias_adjustment > 1.0 C` is explicitly flagged.
- No candidate can be considered for OM-M8 unless support report exists.

---

## Sprint OM-M8A: Defensive Selector

**Files:**
- Modify: `solarstorm/open_meteo/_calibrated_nested.py`
- Test: `tests/test_open_meteo_calibrated_nested.py`
- Test: `tests/test_open_meteo_calibrated_nested_cli.py`
- Generate: `reports/onda3-open-meteo-defensive-selection/`

**Deliverables:**
- Add optional selector mode:
  - `validation_mae_then_non_southerly_guard_then_cp23`
- Add selection diagnostic artifact:
  - `onda3_open_meteo_defensive_selection_guardrail_v1.csv`
- Guardrail compares each calibrated candidate against `open_meteo_augmented_onda3f` on validation rows.

**Measurable Exit Criteria:**
- Calibrated candidate is eligible only if validation `macro_non_southerly` satisfies:
  - MAE delta vs augmented `<= +0.025 C`.
  - exact bracket delta vs augmented `>= -1.0 pp`.
- If no calibrated candidate passes, selected candidate is `open_meteo_augmented_onda3f`.
- Selection report explains every blocked candidate with:
  - `blocked_by_non_southerly_mae`
  - `blocked_by_non_southerly_exact`
  - `selected_fallback_candidate_id`
- Tests prove the selector falls back to augmented when `macro_non_southerly` is unstable.

---

## Sprint OM-M8B: Nested Revalidation and Forensics Refresh

**Files:**
- Reuse: `solarstorm/open_meteo/_calibrated_nested.py`
- Reuse: `solarstorm/open_meteo/_forensics.py`
- Generate: `reports/onda3-open-meteo-defensive-selection/`
- Generate: `reports/open-meteo-forensics-stabilized/`

**Deliverables:**
- Run nested validation on:
  - local-only Onda 3F
  - current `open_meteo_augmented_onda3f`
  - raw GFS Previous Runs
  - existing OM-M4 candidates
  - new monthly/seasonal candidates
- Refresh pairwise forensics for selected stabilized candidate vs augmented baseline.

**Measurable Exit Criteria:**
- Same-row comparison table includes 2024 and 2025 test rows where coverage permits.
- Report includes:
  - overall MAE and exact bracket
  - year deltas
  - CP deltas
  - month deltas
  - `macro_non_southerly` and `macro_southerly_flow` deltas
- Stabilized calibration is considered successful only if it beats or ties augmented by:
  - overall mean MAE delta `<= -0.010 C`, or
  - exact bracket delta `>= +1.0 pp`,
  - while keeping `macro_non_southerly` MAE delta `<= +0.025 C`.

---

## Sprint OM-M9: Decision Gate

**Files:**
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Optional: `docs/superpowers/specs/2026-06-10-open-meteo-causal-feature-integration-design.md`

**Deliverables:**
- One explicit decision:
  - `PROMOTE_STABILIZED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION`
  - `KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE`
  - `REJECT_STABILIZED_CALIBRATION_FOR_NOW`
- Decision must cite OM-M7/OM-M8 artifact paths and exact metric deltas.

**Measurable Exit Criteria:**
- Roadmap contains the selected status.
- Changelog contains generated artifact list.
- No production status changes unless a later, separate production-readiness gate is created and passed.

---

## Execution Order

1. Implement OM-M7A in TDD.
2. Generate stabilized calibration candidates.
3. Implement OM-M7B support audit in TDD.
4. Run support audit and review fallback/support flags.
5. Implement OM-M8A defensive selector in TDD.
6. Run OM-M8B nested revalidation and forensics refresh.
7. Complete OM-M9 decision gate.

## Stop Conditions

- Stop if monthly/seasonal candidates have insufficient support in more than 40% of rows.
- Stop if defensive selection requires using test-year metrics to choose candidates.
- Stop if the only improvement is in MAE while exact bracket degrades more than 2 pp.
- Stop if `macro_non_southerly` degradation remains above `+0.025 C` versus augmented baseline.
