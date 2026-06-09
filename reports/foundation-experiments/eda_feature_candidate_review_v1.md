# EDA Feature Candidate Review - 2026-06-08

This artifact is an experiment-only bridge. It does not promote features, baselines, regimes, or thresholds to production.

- Reviewed rows: 25
- Feature-ready experiments: 1
- Direct feature queue rows: 0

## Disposition Counts

| Disposition | Rows |
|---|---:|
| baseline_only | 9 |
| feature_ready_experiment | 1 |
| regime_design_only | 11 |
| threshold_calibration_only | 4 |

## Review Matrix

| Experiment | Domain | Disposition | Runner | Queue | Result | Required Artifact | Recommended Experiment |
|---|---|---|---|---|---|---|---|
| BEXP-COOLING-MECHANISM-001 | COOLING | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Implement cooling-mechanism baseline adjustment as an experiment-only comparator. |
| BEXP-L2-MONTH-REGIME-001 | BASELINE | baseline_only | not_feature_runner_scope | queue_empty | passed | foundation_experiment_results_v1.csv | Implement train-only month/regime climatology baseline and compare on leaderboard. |
| BEXP-L4-MONTH-CP-REGIME-001 | BASELINE | baseline_only | not_feature_runner_scope | queue_empty | passed | foundation_experiment_results_v1.csv | Add empirical conditional baseline variant for month/CP/candidate-regime strata. |
| BEXP-LATE-TMAX-Q90-001 | TIMING | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Replace fixed late-hour diagnostic with train-only month/regime q90 experiment. |
| BEXP-QUAR-COOLING-FIXED-001 | COOLING | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Use cooling taxonomy EDA to decide mechanism-specific and month-aware cooling rules. |
| BEXP-QUAR-FOEHN-FIXED-001 | FOEHN | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Run foehn-domain EDA and decide calibrated thresholds or continuous alternatives. |
| BEXP-QUAR-LATE-TMAX-001 | TIMING | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Compute train-only month/regime Tmax-hour distributions and decide retain/adapt/reject. |
| BEXP-QUAR-ONDA2R-REGIME-FAMILY-001 | REGIME | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Resolve regime, wind, cooling, timing, rain, pressure, and foehn thesis decisions first. |
| BEXP-QUAR-REGIME-CLASSIFIER-001 | REGIME | baseline_only | not_feature_runner_scope | queue_empty | not_run | foundation_experiment_results_v1.csv | Run Onda 2E domain EDA and promote only supported/adapted rules into regime design. |
| FEXP-FOEHN-CONTINUOUS-001 | FOEHN | feature_ready_experiment | runner_available | queue_empty | failed | feature_probe_result + validated_feature_contract.json after gates | Test continuous and binned foehn_score variants before any threshold promotion. |
| REXP-COOLING-RDQ-006 | COOLING | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Design a replacement regime candidate that separates cooling mechanisms before Onda 4 rerun. |
| REXP-DEAD-MARITIME-001 | REGIME | regime_design_only | not_feature_runner_scope | queue_empty | passed | regime design validation + Onda 4 robustness review | Repair maritime/cloudy assignment by splitting calm/radiative and cloudy maritime cases. |
| REXP-DEAD-MIXED-001 | REGIME | regime_design_only | not_feature_runner_scope | queue_empty | passed | regime design validation + Onda 4 robustness review | Split or merge mixed/transition family before rerunning candidate R2 validation. |
| REXP-FOEHN-RDQ-007 | FOEHN | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Design a regime-repair candidate using month/CP calibration or continuous FOEHN score; no feature candidate is promoted. |
| REXP-REGIME-RDQ-001 | REGIME | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Run Onda 2E domain EDA and promote only supported/adapted rules into regime design. |
| REXP-REGIME-RDQ-005 | REGIME | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Resolve regime, wind, cooling, timing, rain, pressure, and foehn thesis decisions first. |
| REXP-REGIME-RDQ-008 | REGIME | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Enter regime_design_queue only; run Onda 4 robustness and final physical interpretation before any production classifier change. |
| REXP-REPAIR-FRR-001 | FOEHN | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Review month/CP bins and continuous-score calibration before changing any production regime classifier. |
| REXP-REPAIR-WRR-001 | WIND | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Review wind-sector and southerly-count splits before changing the production regime classifier. |
| REXP-WIND-RDQ-009 | WIND | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Evaluate southerly-count/depth as a regime-design split, not as a promoted model feature. |
| TEXP-COOLING-MECHANISM-001 | COOLING | threshold_calibration_only | not_feature_runner_scope | queue_empty | not_run | threshold calibration result with train-only assignment | Calibrate cooling thresholds by mechanism/month/CP inside candidate regime design only. |
| TEXP-COOLING-RDQ-003 | COOLING | threshold_calibration_only | not_feature_runner_scope | queue_empty | not_run | threshold calibration result with train-only assignment | Use cooling taxonomy EDA to decide mechanism-specific and month-aware cooling rules. |
| TEXP-FOEHN-RDQ-004 | FOEHN | threshold_calibration_only | not_feature_runner_scope | queue_empty | not_run | threshold calibration result with train-only assignment | Run foehn-domain EDA and decide calibrated thresholds or continuous alternatives. |
| TEXP-TIMING-RDQ-002 | TIMING | threshold_calibration_only | not_feature_runner_scope | queue_empty | not_run | threshold calibration result with train-only assignment | Compute train-only month/regime Tmax-hour distributions and decide retain/adapt/reject. |
| WEXP-SOUTHERLY-DEPTH-001 | WIND | regime_design_only | not_feature_runner_scope | queue_empty | not_run | regime design validation + Onda 4 robustness review | Evaluate southerly count/depth as regime-design split, not as production feature. |