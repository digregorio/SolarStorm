# Regime v2.3 Calm/Radiative Failure Diagnostics - 2026-06-08

This is not a production classifier.
v2.3 explains the v2.2 calm/radiative R2 blocker and converts it into experiment-only follow-up work.

- Calm/radiative diagnosis: CALM_RADIATIVE_VALIDATION_TARGET_GAP
- Calm/radiative assignment rows: 2572
- Calm/radiative R2 pass rows: 0
- Calm/radiative R2 median n_days: 27.0

## Macro Diagnostics

| Macro | Assignments | Smallest CP | R2 pass rows | R2 median n_days | Diagnosis |
|---|---:|---:|---:|---:|---|
| macro_calm_radiative | 2572 | 502 | 0 | 27.0 | CALM_RADIATIVE_VALIDATION_TARGET_GAP |
| macro_nw_continuum | 13726 | 3294 | 23 | 210.0 | R2_SIGNAL_PRESENT |
| macro_southerly_flow | 5526 | 1379 | 47 | 110.0 | R2_SIGNAL_PRESENT |

## Next Experiments

| Experiment | Domain | Blocker | Required artifact |
|---|---|---|---|
| CEXP-CALM-RADIATIVE-001 | REGIME_CALM_RADIATIVE | CALM_RADIATIVE_VALIDATION_TARGET_GAP | reports/regime-design/regime_calm_radiative_target_diagnostics_v1.csv |
| CEXP-CALM-RADIATIVE-002 | FEATURE_HYPOTHESIS | CALM_RADIATIVE_VALIDATION_TARGET_GAP | reports/regime-design/regime_calm_radiative_feature_hypotheses_v1.csv |
| CEXP-CALM-RADIATIVE-003 | REGIME_ONTOLOGY | CALM_RADIATIVE_VALIDATION_TARGET_GAP | reports/regime-design/regime_calm_radiative_demote_or_split_v1.csv |

## Decision

Onda 3 remains blocked. v2.3 does not promote v2.2; it defines the next data-backed experiments needed before another regime promotion attempt.