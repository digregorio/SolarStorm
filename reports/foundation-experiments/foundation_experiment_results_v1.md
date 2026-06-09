# Foundation Experiment Results - 2026-06-08

These are experiment-only results. They do not promote a baseline, feature, model, or regime classifier.

- Result rows: 25
- Runnable rows completed: 5

## Status Counts

| Status | Rows |
|---|---:|
| failed | 1 |
| not_run | 20 |
| passed | 4 |

## Baseline Results

| Experiment | Status | Production | Baseline MAE | Candidate MAE | Effect | CI low | CI high | Rows | Notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| BEXP-L2-MONTH-REGIME-001 | passed | EXPERIMENT_ONLY | 1.8256093374527977 | 1.5119292825266049 | 0.3136800549261929 | 0.2926536216958464 | 0.3363414006179195 | 11652 | Train-only month x candidate-regime climatology. candidate_rmse=1.984; candidate_bias=-0.251. |
| BEXP-L4-MONTH-CP-REGIME-001 | passed | EXPERIMENT_ONLY | 1.7523171987641606 | 1.17610710607621 | 0.5762100926879505 | 0.5445417095777549 | 0.6074515104703053 | 11652 | Train-only month x CP x candidate-regime remaining-warming baseline. candidate_rmse=1.578; candidate_bias=0.020. |

## Feature Probe Results

| Experiment | Status | Production | Baseline MAE | Candidate MAE | Effect | CI low | CI high | Rows | Notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| FEXP-FOEHN-CONTINUOUS-001 | failed | EXPERIMENT_ONLY | 1.227857878475798 | 1.243906625472022 | -0.01604874699622383 | -0.024459320288362507 | -0.007893494679024995 | 11652 | Experiment-only binned foehn_score probe versus RULE_FOEHN_SCORE_FIXED_60 comparator; candidate_rmse=1.637; candidate_bias=0.079; fallback_rows=2770. |

## Regime R2 Results

| Experiment | Status | Production | Dead Regimes | Support Rows | Notes |
|---|---|---|---:|---:|---|
| REXP-DEAD-MARITIME-001 | passed | EXPERIMENT_ONLY | 0 | 0 | v2.1 comparison ready for full Onda 4 rerun. |
| REXP-DEAD-MIXED-001 | passed | EXPERIMENT_ONLY | 0 | 0 | v2.1 comparison ready for full Onda 4 rerun. |