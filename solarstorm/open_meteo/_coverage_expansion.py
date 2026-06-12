from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo._availability import PRODUCTION_STATUS

OPEN_METEO_COVERAGE_EXPANSION_FILENAMES = {
    "open_meteo_coverage_expansion_scenarios_v1": (
        "open_meteo_coverage_expansion_scenarios_v1.csv"
    ),
    "open_meteo_coverage_expansion_fold_audit_v1": (
        "open_meteo_coverage_expansion_fold_audit_v1.csv"
    ),
    "open_meteo_single_runs_contract_audit_v1": (
        "open_meteo_single_runs_contract_audit_v1.csv"
    ),
    "open_meteo_coverage_expansion_decision_v1": (
        "open_meteo_coverage_expansion_decision_v1.csv"
    ),
}


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _normalize_cp_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return f"{value:02d}:00"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):02d}:00"
    text = str(value)
    if ":" in text:
        hour, minute, *_ = [*text.split(":"), "00"]
        return f"{int(hour):02d}:{int(minute):02d}"
    if text.isdigit():
        return f"{int(text):02d}:00"
    return text


def _key_frame(frame: pl.DataFrame) -> pl.DataFrame:
    if frame is None or frame.is_empty():
        return pl.DataFrame(
            schema={"date_local": pl.Date, "cp": pl.Utf8},
        )
    required = {"date_local", "cp"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing required coverage key columns: {sorted(missing)}")
    keyed = _ensure_date(frame).select(["date_local", "cp"]).unique()
    return keyed.with_columns(
        pl.col("cp").map_elements(_normalize_cp_value, return_dtype=pl.Utf8)
    ).sort(["date_local", "cp"])


def _strict_common_keys(
    *,
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
    multi_provider_features: pl.DataFrame,
    calibrated_candidates: pl.DataFrame,
) -> pl.DataFrame:
    common = _key_frame(local_features)
    for frame in [
        open_meteo_features,
        multi_provider_features,
        calibrated_candidates,
    ]:
        common = common.join(_key_frame(frame), on=["date_local", "cp"], how="inner")
    if common.is_empty() or "candidate_id" not in calibrated_candidates.columns:
        return common.unique().sort(["date_local", "cp"])

    candidates = _ensure_date(calibrated_candidates).with_columns(
        pl.col("cp").map_elements(_normalize_cp_value, return_dtype=pl.Utf8)
    )
    candidate_ids = sorted(candidates["candidate_id"].unique().to_list())
    for candidate_id in candidate_ids:
        candidate_keys = (
            candidates.filter(pl.col("candidate_id") == candidate_id)
            .select(["date_local", "cp"])
            .unique()
        )
        common = common.join(candidate_keys, on=["date_local", "cp"], how="inner")
    return common.unique().sort(["date_local", "cp"])


def _stage_row(
    keys: pl.DataFrame,
    *,
    scenario_id: str,
    outer_test_year: int,
    stage: str,
    evaluation_year: int,
    train_start: dt.date,
) -> dict[str, object]:
    scoped = keys.filter(pl.col("date_local") >= train_start)
    train = scoped.filter(pl.col("date_local").dt.year() < evaluation_year)
    evaluation = scoped.filter(pl.col("date_local").dt.year() == evaluation_year)
    valid = not train.is_empty() and not evaluation.is_empty()
    if valid:
        blocker = ""
    elif train.is_empty() and evaluation.is_empty():
        blocker = "missing_train_and_evaluation_rows"
    elif train.is_empty():
        blocker = "missing_prior_train_rows"
    else:
        blocker = "missing_evaluation_rows"
    return {
        "scenario_id": scenario_id,
        "outer_test_year": outer_test_year,
        "stage": stage,
        "evaluation_year": evaluation_year,
        "train_start": train_start,
        "train_end": train["date_local"].max() if not train.is_empty() else None,
        "n_train_rows": train.height,
        "n_evaluation_rows": evaluation.height,
        "fold_stage_valid": valid,
        "blocker": blocker,
        "leakage_status": "STRICT_COMMON_ROWS_NO_FUTURE_ROWS",
        "production_status": PRODUCTION_STATUS,
    }


def _fold_audit_for_scenario(
    keys: pl.DataFrame,
    *,
    scenario_id: str,
    test_years: list[int],
    train_start: dt.date,
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for outer_test_year in test_years:
        rows.append(
            _stage_row(
                keys,
                scenario_id=scenario_id,
                outer_test_year=outer_test_year,
                stage="validation",
                evaluation_year=outer_test_year - 1,
                train_start=train_start,
            )
        )
        rows.append(
            _stage_row(
                keys,
                scenario_id=scenario_id,
                outer_test_year=outer_test_year,
                stage="test",
                evaluation_year=outer_test_year,
                train_start=train_start,
            )
        )
    return pl.DataFrame(rows, strict=False)


def _valid_outer_folds(fold_audit: pl.DataFrame, scenario_id: str) -> int:
    if fold_audit.is_empty():
        return 0
    valid = fold_audit.filter(pl.col("scenario_id") == scenario_id)
    count = 0
    for outer_test_year in sorted(valid["outer_test_year"].unique().to_list()):
        fold = valid.filter(pl.col("outer_test_year") == outer_test_year)
        stages = set(fold.filter(pl.col("fold_stage_valid"))["stage"].to_list())
        if {"validation", "test"}.issubset(stages):
            count += 1
    return count


def _scenario_row(
    keys: pl.DataFrame,
    *,
    scenario_id: str,
    scenario_description: str,
    fold_audit: pl.DataFrame,
    data_source_status: str,
) -> dict[str, object]:
    n_valid = _valid_outer_folds(fold_audit, scenario_id)
    meets_gate = n_valid >= 2
    blockers = sorted(
        {
            row["blocker"]
            for row in fold_audit.filter(pl.col("scenario_id") == scenario_id).iter_rows(
                named=True
            )
            if row["blocker"]
        }
    )
    return {
        "scenario_id": scenario_id,
        "scenario_description": scenario_description,
        "data_source_status": data_source_status,
        "earliest_covered_date": keys["date_local"].min() if not keys.is_empty() else None,
        "latest_covered_date": keys["date_local"].max() if not keys.is_empty() else None,
        "n_common_dates": keys.select("date_local").unique().height,
        "n_common_rows": keys.height,
        "n_valid_outer_folds": n_valid,
        "meets_two_fold_gate": meets_gate,
        "leakage_status": "STRICT_COMMON_ROWS_NO_FUTURE_ROWS",
        "blocker": ";".join(blockers),
        "production_status": PRODUCTION_STATUS,
    }


def _single_runs_contract_audit(single_runs_probe_results: pl.DataFrame) -> pl.DataFrame:
    if single_runs_probe_results is None or single_runs_probe_results.is_empty():
        return pl.DataFrame(
            [
                {
                    "endpoint": "single_runs",
                    "n_probe_rows": 0,
                    "n_success": 0,
                    "n_http_400": 0,
                    "contract_status": "NO_SINGLE_RUNS_PROBE_EVIDENCE",
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    probes = single_runs_probe_results.filter(pl.col("endpoint") == "single_runs")
    if probes.is_empty():
        n_success = 0
        n_http_400 = 0
    else:
        n_success = int(probes["success"].cast(pl.Int64, strict=False).sum())
        n_http_400 = (
            int((probes["status_code"].cast(pl.Int64, strict=False) == 400).sum())
            if "status_code" in probes.columns
            else 0
        )
    if n_success > 0:
        status = "REQUEST_CONTRACT_HAS_SUCCESSFUL_PROBES"
    elif n_http_400 > 0:
        status = "BLOCKED_BY_REQUEST_CONTRACT"
    else:
        status = "NO_SINGLE_RUNS_SUCCESSFUL_PROBES"
    return pl.DataFrame(
        [
            {
                "endpoint": "single_runs",
                "n_probe_rows": probes.height,
                "n_success": n_success,
                "n_http_400": n_http_400,
                "contract_status": status,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def _decision(
    scenarios: pl.DataFrame,
    single_runs_audit: pl.DataFrame,
) -> pl.DataFrame:
    current = scenarios.filter(pl.col("scenario_id") == "current_strict_common_rows")
    previous_2022 = scenarios.filter(
        pl.col("scenario_id") == "previous_runs_history_from_2022"
    )
    current_meets = (
        bool(current.row(0, named=True)["meets_two_fold_gate"])
        if not current.is_empty()
        else False
    )
    previous_meets = (
        bool(previous_2022.row(0, named=True)["meets_two_fold_gate"])
        if not previous_2022.is_empty()
        else False
    )
    single_status = (
        single_runs_audit.row(0, named=True)["contract_status"]
        if not single_runs_audit.is_empty()
        else "NO_SINGLE_RUNS_PROBE_EVIDENCE"
    )
    if current_meets:
        status = "CURRENT_COVERAGE_SUPPORTS_TWO_STRICT_FOLDS"
        rationale = "Current strict common-row Open-Meteo coverage already supports at least two nested outer folds."
    elif previous_meets:
        status = "COVERAGE_EXPANSION_REQUIRES_2022_HISTORY"
        rationale = (
            "Current 2023+ strict common-row coverage supports only one full outer "
            "fold; a causal Previous Runs backfill to 2022 is the minimal path "
            "shown here to reach two folds without leakage."
        )
    elif single_status == "REQUEST_CONTRACT_HAS_SUCCESSFUL_PROBES":
        status = "COVERAGE_EXPANSION_REQUIRES_SINGLE_RUNS_BACKFILL"
        rationale = "Single Runs probes succeeded, but historical strict common-row coverage still needs to be materialized."
    else:
        status = "COVERAGE_EXPANSION_BLOCKED_BY_HISTORY"
        rationale = "No audited scenario currently reaches two strict common-row outer folds."
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "current_n_valid_outer_folds": (
                    current.row(0, named=True)["n_valid_outer_folds"]
                    if not current.is_empty()
                    else 0
                ),
                "single_runs_contract_status": single_status,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_coverage_expansion_artifacts(
    *,
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
    multi_provider_features: pl.DataFrame,
    calibrated_candidates: pl.DataFrame,
    single_runs_probe_results: pl.DataFrame,
    test_years: list[int],
    train_start: dt.date = dt.date(2012, 1, 1),
    history_start: dt.date = dt.date(2022, 1, 1),
) -> dict[str, pl.DataFrame]:
    current_keys = _strict_common_keys(
        local_features=local_features,
        open_meteo_features=open_meteo_features,
        multi_provider_features=multi_provider_features,
        calibrated_candidates=calibrated_candidates,
    )
    local_keys = _key_frame(local_features)
    hypothetical_2022_keys = local_keys.filter(pl.col("date_local") >= history_start)

    scenarios_def = [
        (
            "current_strict_common_rows",
            current_keys,
            "Observed strict common rows across local, Open-Meteo features, multi-provider features and calibrated candidates.",
            "observed_current_cache",
        ),
        (
            "previous_runs_history_from_2022",
            hypothetical_2022_keys,
            "Counterfactual causal Previous Runs history materialized from 2022 on local feature keys.",
            "requires_additional_historical_fetch",
        ),
        (
            "alternate_fixed_leads_current_cache",
            current_keys,
            "Alternate fixed leads over the current cache; lead choice cannot create pre-2023 dates.",
            "observed_current_cache_no_date_expansion",
        ),
    ]

    fold_frames = [
        _fold_audit_for_scenario(
            keys,
            scenario_id=scenario_id,
            test_years=test_years,
            train_start=train_start,
        )
        for scenario_id, keys, _, _ in scenarios_def
    ]
    fold_audit = pl.concat(fold_frames, how="diagonal_relaxed")
    scenarios = pl.DataFrame(
        [
            _scenario_row(
                keys,
                scenario_id=scenario_id,
                scenario_description=description,
                fold_audit=fold_audit,
                data_source_status=data_source_status,
            )
            for scenario_id, keys, description, data_source_status in scenarios_def
        ],
        strict=False,
    )
    single_runs = _single_runs_contract_audit(single_runs_probe_results)
    return {
        "open_meteo_coverage_expansion_scenarios_v1": scenarios,
        "open_meteo_coverage_expansion_fold_audit_v1": fold_audit,
        "open_meteo_single_runs_contract_audit_v1": single_runs,
        "open_meteo_coverage_expansion_decision_v1": _decision(scenarios, single_runs),
    }


def _markdown_table(frame: pl.DataFrame, max_rows: int = 30) -> str:
    if frame.is_empty():
        return "_No rows._"
    header = "| " + " | ".join(frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| "
        + " | ".join("" if row[col] is None else str(row[col]) for col in frame.columns)
        + " |"
        for row in frame.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *rows])


def render_open_meteo_coverage_expansion_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Coverage/Fold Expansion Report",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Audit of whether extra causal Open-Meteo history, alternate fixed "
                "leads, or a repaired Single Runs request contract can create at "
                "least two strict common-row outer folds without leakage."
            ),
            "## Decision",
            _markdown_table(artifacts["open_meteo_coverage_expansion_decision_v1"]),
            "## Scenario Coverage",
            _markdown_table(
                artifacts["open_meteo_coverage_expansion_scenarios_v1"],
                max_rows=20,
            ),
            "## Fold Audit",
            _markdown_table(
                artifacts["open_meteo_coverage_expansion_fold_audit_v1"],
                max_rows=80,
            ),
            "## Single Runs Request Contract",
            _markdown_table(artifacts["open_meteo_single_runs_contract_audit_v1"]),
        ]
    ) + "\n"


def write_open_meteo_coverage_expansion_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in OPEN_METEO_COVERAGE_EXPANSION_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_coverage_expansion_report_v1.md"
    report_path.write_text(
        render_open_meteo_coverage_expansion_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_coverage_expansion_report_md"] = report_path
    return paths
