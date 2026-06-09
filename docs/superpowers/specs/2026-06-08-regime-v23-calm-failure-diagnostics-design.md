# Regime v2.3 Calm/Radiative Failure Diagnostics Design

## Context

Regime Ontology v2.2 restored `macro_calm_radiative` as a protected
experiment-only macro, but R2 still blocks promotion with 0/92 passing rows.
The project needs evidence explaining whether this is a support problem, a
feature/target validation problem, or a sign that calm/radiative should not be
a production-eligible macro.

## Goal

Create an experiment-only diagnostic surface that explains the v2.2
calm/radiative blocker and converts it into concrete next experiments without
promoting Onda 3, changing the production classifier, or training a model.

## Inputs

- `reports/regime-design/regime_candidate_assignments_v2_2.csv`
- `reports/regime-design/regime_candidate_r2_validation_v2_2.csv`
- `data/features.parquet`
- `data/labels.parquet`

## Outputs

- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_failure_diagnostics_v1.md`
- `reports/regime-design/regime_v23_next_experiments.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.csv`
- `reports/regime-design/regime_calm_radiative_target_diagnostics_v1.md`
- `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.csv`
- `reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.md`
- `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.csv`
- `reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.md`

## Behavior

The diagnostic summarizes each v2.2 macro by assignment support, unique days,
CP support, reassignment provenance, R2 pass rows, R2 median/min/max `n_days`,
tested feature coverage, target summary, and a deterministic diagnosis.

For `macro_calm_radiative`, sufficient assignment support plus zero R2 pass rows
must produce `CALM_RADIATIVE_VALIDATION_TARGET_GAP`, not production promotion.
The next-experiment queue must contain calm-specific target diagnostics,
feature-hypothesis diagnostics, and a macro-versus-subtype/split comparison.

`CEXP-CALM-RADIATIVE-001` then creates a train-window target diagnostic by
`macro_regime_label x month x CP`. It computes
`remaining_warming = tmax_int - k_cp__cp_XXXX`, Tmax-hour quantiles, target
bucket shares, and power flags. These full-day targets are audit evidence only:
they may guide feature and ontology hypotheses, but they must not become CP
features or production regime labels.

`CEXP-CALM-RADIATIVE-002` then creates a train-window calm/radiative
feature-hypothesis diagnostic. It joins v2.2 assignments, `data/features`, and
target labels only for audit, screens calm-specific candidate features against
`remaining_warming`, and records `causal_role` for every row. Any
`remaining_warming` or `tmax_*` target/proxy candidate is blocked as
`FULL_DAY_TARGET_OR_PROXY_AUDIT_ONLY`. The first real run screens 8 features
and finds 1 preliminary candidate signal, `cloud_cover_suppression`; this is a
follow-up hypothesis, not a promoted feature.

`CEXP-CALM-RADIATIVE-002B` then validates that candidate signal against
proxy/artifact risk. It must test pre-CP lineage, expected negative slope,
CP and month x CP stability, retention after physical controls, and correlation
against known target/proxy columns. If the signal fails, CEXP-003 emits a
demote/split matrix comparing protected macro, subtype/audit demotion, and
radiative-clear/cloudy split. In the first real run, `cloud_cover_suppression`
survives the screen and CEXP-003 is not triggered.

## Gates

- All generated rows keep `production_status = EXPERIMENT_ONLY`.
- The CLI only reads existing v2.2 artifacts and writes v2.3 diagnostics.
- The implementation must not overwrite `data/features.parquet`.
- The implementation must not create Onda 3 model files or estimators.
- CEXP-002 must not promote `cloud_cover_suppression`; it can only nominate
  causal robustness testing before CEXP-003 demote/split decisions.
- CEXP-002B may retain `cloud_cover_suppression` as an experiment-only causal
  candidate, but it still cannot promote production features or Onda 3.
