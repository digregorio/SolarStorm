# Open-Meteo Coverage/Fold Expansion Report

Generated: 2026-06-10

production_status: EXPERIMENT_ONLY

Audit of whether extra causal Open-Meteo history, alternate fixed leads, or a repaired Single Runs request contract can create at least two strict common-row outer folds without leakage.

## Decision

| decision_status | decision_rationale | current_n_valid_outer_folds | single_runs_contract_status | production_status |
| --- | --- | --- | --- | --- |
| COVERAGE_EXPANSION_REQUIRES_2022_HISTORY | Current 2023+ strict common-row coverage supports only one full outer fold; a causal Previous Runs backfill to 2022 is the minimal path shown here to reach two folds without leakage. | 1 | BLOCKED_BY_REQUEST_CONTRACT | EXPERIMENT_ONLY |

## Scenario Coverage

| scenario_id | scenario_description | data_source_status | earliest_covered_date | latest_covered_date | n_common_dates | n_common_rows | n_valid_outer_folds | meets_two_fold_gate | leakage_status | blocker | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_strict_common_rows | Observed strict common rows across local, Open-Meteo features, multi-provider features and calibrated candidates. | observed_current_cache | 2023-01-01 | 2025-12-31 | 1076 | 4304 | 1 | False | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | missing_prior_train_rows | EXPERIMENT_ONLY |
| previous_runs_history_from_2022 | Counterfactual causal Previous Runs history materialized from 2022 on local feature keys. | requires_additional_historical_fetch | 2022-01-01 | 2026-06-03 | 1615 | 6460 | 2 | True | STRICT_COMMON_ROWS_NO_FUTURE_ROWS |  | EXPERIMENT_ONLY |
| alternate_fixed_leads_current_cache | Alternate fixed leads over the current cache; lead choice cannot create pre-2023 dates. | observed_current_cache_no_date_expansion | 2023-01-01 | 2025-12-31 | 1076 | 4304 | 1 | False | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | missing_prior_train_rows | EXPERIMENT_ONLY |

## Fold Audit

| scenario_id | outer_test_year | stage | evaluation_year | train_start | train_end | n_train_rows | n_evaluation_rows | fold_stage_valid | blocker | leakage_status | production_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_strict_common_rows | 2024 | validation | 2023 | 2012-01-01 |  | 0 | 1456 | False | missing_prior_train_rows | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| current_strict_common_rows | 2024 | test | 2024 | 2012-01-01 | 2023-12-30 | 1456 | 1388 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| current_strict_common_rows | 2025 | validation | 2024 | 2012-01-01 | 2023-12-30 | 1456 | 1388 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| current_strict_common_rows | 2025 | test | 2025 | 2012-01-01 | 2024-12-31 | 2844 | 1460 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| previous_runs_history_from_2022 | 2024 | validation | 2023 | 2012-01-01 | 2022-12-31 | 1460 | 1460 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| previous_runs_history_from_2022 | 2024 | test | 2024 | 2012-01-01 | 2023-12-31 | 2920 | 1464 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| previous_runs_history_from_2022 | 2025 | validation | 2024 | 2012-01-01 | 2023-12-31 | 2920 | 1464 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| previous_runs_history_from_2022 | 2025 | test | 2025 | 2012-01-01 | 2024-12-31 | 4384 | 1460 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| alternate_fixed_leads_current_cache | 2024 | validation | 2023 | 2012-01-01 |  | 0 | 1456 | False | missing_prior_train_rows | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| alternate_fixed_leads_current_cache | 2024 | test | 2024 | 2012-01-01 | 2023-12-30 | 1456 | 1388 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| alternate_fixed_leads_current_cache | 2025 | validation | 2024 | 2012-01-01 | 2023-12-30 | 1456 | 1388 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |
| alternate_fixed_leads_current_cache | 2025 | test | 2025 | 2012-01-01 | 2024-12-31 | 2844 | 1460 | True |  | STRICT_COMMON_ROWS_NO_FUTURE_ROWS | EXPERIMENT_ONLY |

## Single Runs Request Contract

| endpoint | n_probe_rows | n_success | n_http_400 | contract_status | production_status |
| --- | --- | --- | --- | --- | --- |
| single_runs | 24 | 0 | 24 | BLOCKED_BY_REQUEST_CONTRACT | EXPERIMENT_ONLY |
