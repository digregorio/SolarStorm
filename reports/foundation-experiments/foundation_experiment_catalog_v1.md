# Foundation Experiment Catalog - 2026-06-07

This is not a production promotion.
Every row is an experiment candidate and keeps `production_status = EXPERIMENT_ONLY`.

- Catalog rows: 25
- Families: 4
- Domains: 6

## Counts By Family

| Family | Rows |
|---|---:|
| baseline | 9 |
| feature | 1 |
| regime | 11 |
| threshold | 4 |

## Counts By Domain

| Domain | Rows |
|---|---:|
| BASELINE | 2 |
| COOLING | 5 |
| FOEHN | 5 |
| REGIME | 7 |
| TIMING | 3 |
| WIND | 3 |

## Counts By Weakness Target

| Weakness Target | Rows |
|---|---:|
| dead_regime | 2 |
| fixed_threshold | 10 |
| high_mae | 2 |
| quarantined_baseline | 2 |
| regime_design_review | 6 |
| regime_repair | 2 |
| regime_split | 1 |

## Counts By Candidate Surface

| Candidate Surface | Rows |
|---|---:|
| baseline_ladder | 9 |
| feature_builder | 1 |
| regime_assignment | 12 |
| validation_harness | 3 |

## Priority Experiments

| Experiment | Family | Domain | Target | Comparator | Next action |
|---|---|---|---|---|---|
| BEXP-L2-MONTH-REGIME-001 | baseline | BASELINE | high_mae | L2 | Implement train-only month/regime climatology baseline and compare on leaderboard. |
| BEXP-L4-MONTH-CP-REGIME-001 | baseline | BASELINE | high_mae | L4 | Add empirical conditional baseline variant for month/CP/candidate-regime strata. |
| FEXP-FOEHN-CONTINUOUS-001 | feature | FOEHN | fixed_threshold | RULE_FOEHN_SCORE_FIXED_60 | Test continuous and binned foehn_score variants before any threshold promotion. |
| REXP-DEAD-MARITIME-001 | regime | REGIME | dead_regime | RULE_ONDA2R_PHYSICAL_REGIME_FAMILY | Repair maritime/cloudy assignment by splitting calm/radiative and cloudy maritime cases. |
| REXP-DEAD-MIXED-001 | regime | REGIME | dead_regime | RULE_ONDA2R_PHYSICAL_REGIME_FAMILY | Split or merge mixed/transition family before rerunning candidate R2 validation. |
| TEXP-COOLING-MECHANISM-001 | threshold | COOLING | fixed_threshold | RULE_COOLING_FIXED_MINUS_2_C_PER_H | Calibrate cooling thresholds by mechanism/month/CP inside candidate regime design only. |
| WEXP-SOUTHERLY-DEPTH-001 | regime | WIND | regime_split | REGIME_CLASSIFIER_CURRENT | Evaluate southerly count/depth as regime-design split, not as production feature. |

## Missing Optional Artifacts

| Artifact | Status | Detail |
|---|---|---|
| none | PASS | All optional artifacts found. |

## Production Guard

The catalog can guide implementation experiments, but it does not promote a feature, baseline, model, or regime classifier to production. Experiment results must be recorded separately before ADR-012 can advance any candidate.