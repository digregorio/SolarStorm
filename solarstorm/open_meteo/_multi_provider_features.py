from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl

from solarstorm.open_meteo._availability import PRODUCTION_STATUS
from solarstorm.open_meteo._client import hash_text
from solarstorm.open_meteo._features import (
    _parse_response_text,
    build_previous_runs_feature_rows,
)

READY_STATUS = "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS"
MULTI_PROVIDER_READY = "OPEN_METEO_MULTI_PROVIDER_FEATURES_READY"
MULTI_PROVIDER_BLOCKED_BY_COVERAGE = "BLOCK_MULTI_PROVIDER_FEATURES_BY_COVERAGE"

MULTI_PROVIDER_FEATURE_FILENAMES = {
    "open_meteo_multi_provider_feature_manifest_v1": (
        "open_meteo_multi_provider_feature_manifest_v1.csv"
    ),
    "open_meteo_multi_provider_feature_coverage_v1": (
        "open_meteo_multi_provider_feature_coverage_v1.csv"
    ),
    "open_meteo_multi_provider_feature_source_selection_v1": (
        "open_meteo_multi_provider_feature_source_selection_v1.csv"
    ),
    "open_meteo_multi_provider_feature_decision_v1": (
        "open_meteo_multi_provider_feature_decision_v1.csv"
    ),
}

BACKFILL_FEASIBILITY_FILENAMES = {
    "open_meteo_backfill_feasibility_v1": (
        "open_meteo_backfill_feasibility_v1.csv"
    ),
    "open_meteo_backfill_feasibility_decision_v1": (
        "open_meteo_backfill_feasibility_decision_v1.csv"
    ),
}


def select_multi_provider_feature_sources(
    provider_decision_update: pl.DataFrame,
) -> pl.DataFrame:
    if provider_decision_update.is_empty():
        return pl.DataFrame()
    required = {
        "endpoint",
        "model",
        "provider_family",
        "decision_status",
        "production_status",
    }
    missing = required - set(provider_decision_update.columns)
    if missing:
        raise ValueError(
            "provider decision update missing columns: " + ", ".join(sorted(missing))
        )
    columns = [
        column
        for column in [
            "endpoint",
            "model",
            "provider",
            "provider_family",
            "decision_status",
            "feature_gate_scope",
            "production_status",
        ]
        if column in provider_decision_update.columns
    ]
    return (
        provider_decision_update.filter(
            (pl.col("endpoint") == "previous_runs")
            & (pl.col("decision_status") == READY_STATUS)
        )
        .select(columns)
        .sort(["endpoint", "model"])
    )


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _with_provider_metadata(
    rows: pl.DataFrame,
    *,
    raw_row: dict[str, object],
    source_row: dict[str, object],
) -> pl.DataFrame:
    renamed = rows.rename(
        {
            "om_endpoint": "endpoint",
            "om_model": "model",
            "om_prev_d1_day_max_c": "om_provider_tmax_pred_c",
            "om_run_time_utc": "om_provider_run_time_utc",
            "om_available_time_utc": "om_provider_available_time_utc",
            "om_lead_h": "om_provider_lead_hours",
            "om_request_url_sha256": "request_url_sha256",
            "om_response_sha256": "response_sha256",
        }
    )
    return renamed.with_columns(
        pl.lit(str(raw_row.get("provider") or source_row.get("provider") or "")).alias(
            "provider"
        ),
        pl.lit(str(source_row["provider_family"])).alias("provider_family"),
        pl.lit(str(source_row["decision_status"])).alias("source_decision_status"),
        pl.lit(str(source_row.get("feature_gate_scope") or "")).alias(
            "feature_gate_scope"
        ),
        pl.lit(24).alias("om_provider_lead_hours"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )


def _duplicate_key_count(features: pl.DataFrame) -> int:
    if features.is_empty():
        return 0
    key_columns = ["date_local", "cp", "endpoint", "model"]
    return features.height - features.select(key_columns).unique().height


def _payload_dates(payload: dict[str, object]) -> list[dt.date]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return []
    times = hourly.get("time")
    if not isinstance(times, list):
        return []
    dates: list[dt.date] = []
    for value in times:
        if not isinstance(value, str):
            continue
        date_value = dt.datetime.fromisoformat(value).date()
        if date_value not in dates:
            dates.append(date_value)
    return dates


def _slice_payload_for_date(
    payload: dict[str, object],
    date_local: dt.date,
) -> dict[str, object]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return payload
    times = hourly.get("time")
    if not isinstance(times, list):
        return payload
    indices = [
        index
        for index, value in enumerate(times)
        if isinstance(value, str) and dt.datetime.fromisoformat(value).date() == date_local
    ]
    if len(indices) == len(times):
        return payload
    sliced_hourly: dict[str, object] = {}
    for key, values in hourly.items():
        if isinstance(values, list):
            sliced_hourly[key] = [values[index] for index in indices if index < len(values)]
        else:
            sliced_hourly[key] = values
    return {**payload, "hourly": sliced_hourly}


def build_multi_provider_previous_runs_features(
    *,
    cache: pl.DataFrame,
    provider_decision_update: pl.DataFrame,
    dates: list[dt.date] | tuple[dt.date, ...] | None,
    cps: list[str] | tuple[str, ...],
    models: list[str] | tuple[str, ...] | None,
) -> pl.DataFrame:
    sources = select_multi_provider_feature_sources(provider_decision_update)
    if sources.is_empty() or cache.is_empty():
        return pl.DataFrame(
            schema={
                "date_local": pl.Date,
                "cp": pl.String,
                "endpoint": pl.String,
                "model": pl.String,
                "provider": pl.String,
                "provider_family": pl.String,
                "om_provider_tmax_pred_c": pl.Float64,
                "production_status": pl.String,
            }
        )
    cache = _ensure_date(cache)
    if "success" in cache.columns:
        cache = cache.filter(pl.col("success").cast(pl.Boolean))
    if dates is not None:
        cache = cache.filter(pl.col("date_local").is_in(list(dates)))
    if models is not None:
        cache = cache.filter(pl.col("model").is_in(list(models)))

    selected = cache.join(
        sources,
        on=["endpoint", "model"],
        how="inner",
        suffix="_source",
    )
    frames: list[pl.DataFrame] = []
    for row in selected.iter_rows(named=True):
        payload = _parse_response_text(str(row["response_text"]))
        has_range_metadata = row.get("start_date") is not None or row.get("end_date") is not None
        candidate_dates = (
            _payload_dates(payload) or [row["date_local"]]
            if has_range_metadata
            else [row["date_local"]]
        )
        if dates is not None:
            requested = set(dates)
            candidate_dates = [date_value for date_value in candidate_dates if date_value in requested]
        for date_value in candidate_dates:
            raw_features = build_previous_runs_feature_rows(
                payload=_slice_payload_for_date(payload, date_value),
                source_id=f"previous_runs_{row['model']}_temperature",
                endpoint=str(row["endpoint"]),
                model=str(row["model"]),
                date_local=date_value,
                cps=cps,
                request_url_sha256=str(row["request_url_sha256"]),
                response_sha256=str(row["response_sha256"]),
            )
            frames.append(
                _with_provider_metadata(raw_features, raw_row=row, source_row=row)
            )

    features = pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()
    if _duplicate_key_count(features):
        raise ValueError("duplicate Open-Meteo multi-provider feature keys")
    if features.is_empty():
        return features
    ordered_columns = [
        "date_local",
        "cp",
        "endpoint",
        "model",
        "provider",
        "provider_family",
        "om_source_id",
        "om_causal_class",
        "feature_gate_scope",
        "om_provider_tmax_pred_c",
        "om_provider_run_time_utc",
        "om_provider_available_time_utc",
        "om_provider_lead_hours",
        "request_url_sha256",
        "response_sha256",
        "source_decision_status",
        *[
            column
            for column in features.columns
            if column.startswith("om_prev_d1_")
            and column
            not in {
                "om_prev_d1_day_max_c",
            }
        ],
        "production_status",
    ]
    return features.select([column for column in ordered_columns if column in features.columns])


def _feature_manifest(features: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    metadata = {
        "date_local",
        "cp",
        "endpoint",
        "model",
        "provider",
        "provider_family",
        "production_status",
    }
    for column in features.columns:
        if column in metadata:
            continue
        rows.append(
            {
                "feature": column,
                "feature_source": "open_meteo_multi_provider_previous_runs",
                "non_null_rows": features.height - features[column].null_count(),
                "n_rows": features.height,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _coverage(features: pl.DataFrame) -> pl.DataFrame:
    if features.is_empty():
        return pl.DataFrame(
            [
                {
                    "n_feature_rows": 0,
                    "n_dates": 0,
                    "n_cps": 0,
                    "n_models": 0,
                    "n_provider_families": 0,
                    "n_overlapping_provider_families": 0,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    overlap = (
        features.group_by(["date_local", "cp"])
        .agg(pl.col("provider_family").n_unique().alias("n_provider_families"))
        .select(pl.col("n_provider_families").max())
        .item()
    )
    return pl.DataFrame(
        [
            {
                "n_feature_rows": features.height,
                "n_dates": features["date_local"].n_unique(),
                "n_cps": features["cp"].n_unique(),
                "n_models": features["model"].n_unique(),
                "n_provider_families": features["provider_family"].n_unique(),
                "n_overlapping_provider_families": int(overlap or 0),
                "min_date": features["date_local"].min(),
                "max_date": features["date_local"].max(),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def _decision(coverage: pl.DataFrame) -> pl.DataFrame:
    row = coverage.row(0, named=True)
    n_overlap = int(row["n_overlapping_provider_families"] or 0)
    status = (
        MULTI_PROVIDER_READY
        if n_overlap >= 2
        else MULTI_PROVIDER_BLOCKED_BY_COVERAGE
    )
    reason = (
        "at_least_two_provider_families_overlap"
        if n_overlap >= 2
        else "fewer_than_two_provider_families_overlap"
    )
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_reason": reason,
                "n_feature_rows": row["n_feature_rows"],
                "n_provider_families": row["n_provider_families"],
                "n_overlapping_provider_families": n_overlap,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_multi_provider_feature_artifacts(
    *,
    raw_responses: pl.DataFrame,
    provider_decision_update: pl.DataFrame,
    dates: list[dt.date] | tuple[dt.date, ...] | None,
    cps: list[str] | tuple[str, ...],
    models: list[str] | tuple[str, ...] | None,
) -> dict[str, pl.DataFrame]:
    sources = select_multi_provider_feature_sources(provider_decision_update)
    features = build_multi_provider_previous_runs_features(
        cache=raw_responses,
        provider_decision_update=provider_decision_update,
        dates=dates,
        cps=cps,
        models=models,
    )
    coverage = _coverage(features)
    return {
        "open_meteo_multi_provider_features_v1": features,
        "open_meteo_multi_provider_feature_manifest_v1": _feature_manifest(features),
        "open_meteo_multi_provider_feature_coverage_v1": coverage,
        "open_meteo_multi_provider_feature_source_selection_v1": sources,
        "open_meteo_multi_provider_feature_decision_v1": _decision(coverage),
    }


def _date_count_by_year(start: dt.date, end: dt.date) -> dict[int, int]:
    counts: dict[int, int] = {}
    current = start
    while current <= end:
        counts[current.year] = counts.get(current.year, 0) + 1
        current += dt.timedelta(days=1)
    return counts


def _source_lookup(provider_decision_update: pl.DataFrame) -> dict[str, dict[str, object]]:
    if provider_decision_update.is_empty():
        return {}
    rows = provider_decision_update.filter(pl.col("endpoint") == "previous_runs")
    return {str(row["model"]): row for row in rows.iter_rows(named=True)}


def _backfill_status(
    *,
    ready: bool,
    observed_dates: int,
    requested_dates: int,
) -> tuple[str, str]:
    missing_dates = max(requested_dates - observed_dates, 0)
    if not ready:
        return "BLOCKED_REQUEST_CONTRACT", "provider_not_ready_for_previous_runs"
    if observed_dates == 0:
        return "READY_FOR_BACKFILL", "missing_all_requested_dates"
    if missing_dates > 0:
        return "PARTIAL_BACKFILL_WITH_GAPS", "missing_some_requested_dates"
    return "READY_FOR_BACKFILL", ""


def build_multi_provider_backfill_feasibility(
    *,
    provider_features: pl.DataFrame,
    provider_decision_update: pl.DataFrame,
    requested_start: dt.date,
    requested_end: dt.date,
    cps: list[str] | tuple[str, ...],
    models: list[str] | tuple[str, ...],
) -> pl.DataFrame:
    if requested_end < requested_start:
        raise ValueError("requested_end must be on or after requested_start")
    features = _ensure_date(provider_features) if not provider_features.is_empty() else provider_features
    date_counts = _date_count_by_year(requested_start, requested_end)
    sources = _source_lookup(provider_decision_update)
    rows: list[dict[str, object]] = []
    for year in sorted(date_counts):
        requested_dates = date_counts[year]
        for cp in cps:
            for model in models:
                source = sources.get(str(model), {})
                ready = source.get("decision_status") == READY_STATUS
                provider_family = str(source.get("provider_family") or "")
                observed_dates = 0
                if not features.is_empty() and {"date_local", "cp", "model"}.issubset(
                    set(features.columns)
                ):
                    observed_dates = (
                        features.filter(
                            (pl.col("date_local").dt.year() == year)
                            & (pl.col("cp") == cp)
                            & (pl.col("model") == model)
                        )
                        .select("date_local")
                        .unique()
                        .height
                    )
                status, blocker = _backfill_status(
                    ready=ready,
                    observed_dates=observed_dates,
                    requested_dates=requested_dates,
                )
                missing_dates = max(requested_dates - observed_dates, 0)
                rows.append(
                    {
                        "year": year,
                        "cp": cp,
                        "endpoint": "previous_runs",
                        "model": str(model),
                        "provider_family": provider_family,
                        "requested_dates": requested_dates,
                        "observed_dates": observed_dates,
                        "missing_dates": missing_dates,
                        "coverage_pct": (
                            float(observed_dates) * 100.0 / float(requested_dates)
                            if requested_dates
                            else None
                        ),
                        "coverage_status": status,
                        "blocker": blocker,
                        "production_status": PRODUCTION_STATUS,
                    }
                )
    return pl.DataFrame(rows, strict=False)


def _backfill_feasibility_decision(feasibility: pl.DataFrame) -> pl.DataFrame:
    if feasibility.is_empty():
        status = "BLOCK_OPEN_METEO_2022_BACKFILL_NO_FEASIBILITY_ROWS"
        rationale = "No feasibility rows were produced for the requested backfill scope."
        ready_rows = partial_rows = blocked_rows = 0
    else:
        ready_rows = feasibility.filter(
            pl.col("coverage_status") == "READY_FOR_BACKFILL"
        ).height
        partial_rows = feasibility.filter(
            pl.col("coverage_status") == "PARTIAL_BACKFILL_WITH_GAPS"
        ).height
        blocked_rows = feasibility.filter(
            pl.col("coverage_status") == "BLOCKED_REQUEST_CONTRACT"
        ).height
        years = set(feasibility["year"].to_list())
        has_2022 = 2022 in years
        blocked_2022 = (
            feasibility.filter(
                (pl.col("year") == 2022)
                & (pl.col("coverage_status") == "BLOCKED_REQUEST_CONTRACT")
            ).height
            > 0
        )
        if has_2022 and not blocked_2022:
            status = "OPEN_METEO_2022_BACKFILL_FEASIBILITY_READY"
            rationale = (
                "Previous Runs provider decisions allow a 2022 backfill attempt; "
                "dry-run did not mutate the current feature parquet."
            )
        else:
            status = "BLOCK_OPEN_METEO_2022_BACKFILL_BY_REQUEST_CONTRACT"
            rationale = "One or more requested 2022 provider/model rows are blocked by request contract."
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "ready_rows": ready_rows,
                "partial_rows": partial_rows,
                "blocked_rows": blocked_rows,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def _markdown_table(frame: pl.DataFrame, max_rows: int = 40) -> str:
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


def render_multi_provider_feature_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Multi-Provider Feature Build Report",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "This report builds causal Previous Runs features and audits "
                "provider-family overlap. It does not train, blend, calibrate, "
                "or approve production use."
            ),
            "## Feature Decision",
            _markdown_table(artifacts["open_meteo_multi_provider_feature_decision_v1"]),
            "## Coverage",
            _markdown_table(artifacts["open_meteo_multi_provider_feature_coverage_v1"]),
            "## Source Selection",
            _markdown_table(
                artifacts["open_meteo_multi_provider_feature_source_selection_v1"]
            ),
            "## Feature Manifest",
            _markdown_table(artifacts["open_meteo_multi_provider_feature_manifest_v1"]),
        ]
    ) + "\n"


def render_multi_provider_backfill_feasibility_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo 2022 Backfill Feasibility Report",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Dry-run audit for causal Previous Runs historical backfill. "
                "This report does not overwrite current Open-Meteo feature tables."
            ),
            "## Decision",
            _markdown_table(artifacts["open_meteo_backfill_feasibility_decision_v1"]),
            "## Feasibility",
            _markdown_table(
                artifacts["open_meteo_backfill_feasibility_v1"],
                max_rows=80,
            ),
        ]
    ) + "\n"


def build_multi_provider_backfill_feasibility_artifacts(
    *,
    provider_features: pl.DataFrame,
    provider_decision_update: pl.DataFrame,
    requested_start: dt.date,
    requested_end: dt.date,
    cps: list[str] | tuple[str, ...],
    models: list[str] | tuple[str, ...],
) -> dict[str, pl.DataFrame]:
    feasibility = build_multi_provider_backfill_feasibility(
        provider_features=provider_features,
        provider_decision_update=provider_decision_update,
        requested_start=requested_start,
        requested_end=requested_end,
        cps=cps,
        models=models,
    )
    return {
        "open_meteo_backfill_feasibility_v1": feasibility,
        "open_meteo_backfill_feasibility_decision_v1": (
            _backfill_feasibility_decision(feasibility)
        ),
    }


def write_multi_provider_feature_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_features_path: Path,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_features_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    artifacts["open_meteo_multi_provider_features_v1"].write_parquet(
        output_features_path
    )
    paths["open_meteo_multi_provider_features_parquet"] = output_features_path
    for key, filename in MULTI_PROVIDER_FEATURE_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_multi_provider_feature_report_v1.md"
    report_path.write_text(
        render_multi_provider_feature_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_multi_provider_feature_report_md"] = report_path
    return paths


def write_multi_provider_backfill_feasibility_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in BACKFILL_FEASIBILITY_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_backfill_feasibility_report_v1.md"
    report_path.write_text(
        render_multi_provider_backfill_feasibility_report(
            artifacts,
            today=today,
        ),
        encoding="utf-8",
    )
    paths["open_meteo_backfill_feasibility_report_md"] = report_path
    return paths


def build_multi_provider_raw_response_cache(
    *,
    probe_plan: pl.DataFrame,
    provider_decision_update: pl.DataFrame,
    client: object,
    window_days: int = 1,
) -> pl.DataFrame:
    sources = select_multi_provider_feature_sources(provider_decision_update)
    if sources.is_empty() or probe_plan.is_empty():
        return pl.DataFrame()
    if window_days < 1:
        raise ValueError("window_days must be >= 1")
    selected = probe_plan.join(
        sources.select(["endpoint", "model"]),
        on=["endpoint", "model"],
        how="inner",
    ).unique(
        subset=["endpoint", "model", "date_local"],
        keep="first",
        maintain_order=True,
    )
    rows: list[dict[str, object]] = []
    for (_endpoint, _model), group in selected.group_by(["endpoint", "model"]):
        group = group.sort("date_local")
        group_rows = list(group.iter_rows(named=True))
        for start_index in range(0, len(group_rows), window_days):
            window = group_rows[start_index : start_index + window_days]
            probe = window[0]
            start_date = min(row["date_local"] for row in window)
            end_date = max(row["date_local"] for row in window)
            params = json.loads(str(probe["request_params_json"]))
            params["start_date"] = start_date.isoformat()
            params["end_date"] = end_date.isoformat()
            try:
                response = client.get(str(probe["endpoint_url"]), params)
            except Exception as exc:
                request_url = str(probe.get("request_url", ""))
                rows.append(
                    {
                        "endpoint": probe["endpoint"],
                        "model": probe["model"],
                        "provider": probe.get("provider"),
                        "provider_family": probe.get("provider_family"),
                        "date_local": start_date,
                        "start_date": start_date,
                        "end_date": end_date,
                        "success": False,
                        "status_code": None,
                        "request_url": request_url,
                        "request_url_sha256": hash_text(request_url),
                        "response_sha256": None,
                        "response_text": "",
                        "error": type(exc).__name__,
                        "production_status": PRODUCTION_STATUS,
                    }
                )
                continue
            rows.append(
                {
                    "endpoint": probe["endpoint"],
                    "model": probe["model"],
                    "provider": probe.get("provider"),
                    "provider_family": probe.get("provider_family"),
                    "date_local": start_date,
                    "start_date": start_date,
                    "end_date": end_date,
                    "success": bool(response.ok),
                    "status_code": int(response.status_code),
                    "request_url": response.request_url,
                    "request_url_sha256": response.request_url_sha256,
                    "response_sha256": response.response_sha256,
                    "response_text": response.text,
                    "error": None if response.ok else f"http_{response.status_code}",
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)
