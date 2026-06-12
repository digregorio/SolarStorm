from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm._config import ICAO, TZ_NAME
from solarstorm.data._calendar import cp_to_utc
from solarstorm.open_meteo._availability import (
    PRODUCTION_STATUS,
    WELLINGTON_LATITUDE,
    WELLINGTON_LONGITUDE,
    select_latest_eligible_run,
)
from solarstorm.open_meteo._client import build_request_url, hash_text

PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
SINGLE_RUNS_URL = "https://single-runs-api.open-meteo.com/v1/forecast"
PREVIOUS_RUNS_VARIABLES = (
    "temperature_2m_previous_day1",
    "dew_point_2m_previous_day1",
    "cloud_cover_previous_day1",
    "cloud_cover_low_previous_day1",
    "pressure_msl_previous_day1",
    "wind_speed_10m_previous_day1",
    "wind_gusts_10m_previous_day1",
    "wind_direction_10m_previous_day1",
)
SINGLE_RUNS_VARIABLES = (
    "temperature_2m",
    "dew_point_2m",
    "cloud_cover",
    "cloud_cover_low",
    "pressure_msl",
    "wind_speed_10m",
    "wind_gusts_10m",
    "wind_direction_10m",
)
OPEN_METEO_MULTI_PROVIDER_FILENAMES = {
    "open_meteo_multi_provider_registry_v1": (
        "open_meteo_multi_provider_registry_v1.csv"
    ),
    "open_meteo_multi_provider_probe_plan_v1": (
        "open_meteo_multi_provider_probe_plan_v1.csv"
    ),
    "open_meteo_multi_provider_probe_results_v1": (
        "open_meteo_multi_provider_probe_results_v1.csv"
    ),
    "open_meteo_multi_provider_availability_matrix_v1": (
        "open_meteo_multi_provider_availability_matrix_v1.csv"
    ),
    "open_meteo_multi_provider_decision_update_v1": (
        "open_meteo_multi_provider_decision_update_v1.csv"
    ),
}


@dataclass(frozen=True)
class ProviderCandidate:
    model: str
    provider: str
    provider_family: str
    endpoint_priority: str
    coverage_expectation: str
    causal_role: str
    priority_rank: int


PROVIDER_CANDIDATES: tuple[ProviderCandidate, ...] = (
    ProviderCandidate(
        "gfs_seamless",
        "NOAA",
        "NOAA_GFS",
        "previous_runs,single_runs",
        "global_candidate",
        "fixed_lead_and_snapshot_candidate",
        10,
    ),
    ProviderCandidate(
        "ecmwf_ifs025",
        "ECMWF",
        "ECMWF_IFS",
        "single_runs,previous_runs",
        "global_candidate",
        "snapshot_preferred_candidate",
        20,
    ),
    ProviderCandidate(
        "ecmwf_aifs025_single",
        "ECMWF",
        "ECMWF_AIFS",
        "single_runs,previous_runs",
        "global_candidate",
        "snapshot_preferred_candidate",
        30,
    ),
    ProviderCandidate(
        "icon_seamless",
        "DWD",
        "DWD_ICON",
        "previous_runs,single_runs",
        "global_candidate",
        "fixed_lead_and_snapshot_candidate",
        40,
    ),
    ProviderCandidate(
        "icon_eu",
        "DWD",
        "DWD_ICON",
        "previous_runs,single_runs",
        "regional_expected_missing_for_wellington",
        "coverage_probe_only",
        41,
    ),
    ProviderCandidate(
        "icon_d2",
        "DWD",
        "DWD_ICON",
        "previous_runs,single_runs",
        "regional_expected_missing_for_wellington",
        "coverage_probe_only",
        42,
    ),
    ProviderCandidate(
        "gem_seamless",
        "ECCC",
        "ECCC_GEM",
        "previous_runs,single_runs",
        "global_candidate",
        "fixed_lead_and_snapshot_candidate",
        50,
    ),
    ProviderCandidate(
        "gem_global",
        "ECCC",
        "ECCC_GEM",
        "previous_runs,single_runs",
        "global_candidate",
        "fixed_lead_and_snapshot_candidate",
        51,
    ),
    ProviderCandidate(
        "gem_regional",
        "ECCC",
        "ECCC_GEM",
        "previous_runs,single_runs",
        "regional_expected_missing_for_wellington",
        "coverage_probe_only",
        52,
    ),
    ProviderCandidate(
        "gem_hrdps_continental",
        "ECCC",
        "ECCC_GEM",
        "previous_runs,single_runs",
        "regional_expected_missing_for_wellington",
        "coverage_probe_only",
        53,
    ),
    ProviderCandidate(
        "jma_seamless",
        "JMA",
        "JMA_GSM",
        "previous_runs,single_runs",
        "global_candidate",
        "fixed_lead_and_snapshot_candidate",
        60,
    ),
)


def build_multi_provider_registry() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "station": ICAO,
                "latitude": WELLINGTON_LATITUDE,
                "longitude": WELLINGTON_LONGITUDE,
                "model": candidate.model,
                "provider": candidate.provider,
                "provider_family": candidate.provider_family,
                "endpoint_priority": candidate.endpoint_priority,
                "coverage_expectation": candidate.coverage_expectation,
                "causal_role": candidate.causal_role,
                "priority_rank": candidate.priority_rank,
                "production_status": PRODUCTION_STATUS,
            }
            for candidate in PROVIDER_CANDIDATES
        ],
        strict=False,
    ).sort("priority_rank")


def _endpoint_url(endpoint: str) -> str:
    if endpoint == "previous_runs":
        return PREVIOUS_RUNS_URL
    if endpoint == "single_runs":
        return SINGLE_RUNS_URL
    raise ValueError(f"unsupported Open-Meteo multi-provider endpoint: {endpoint}")


def _endpoint_variables(endpoint: str) -> tuple[str, ...]:
    if endpoint == "previous_runs":
        return PREVIOUS_RUNS_VARIABLES
    if endpoint == "single_runs":
        return SINGLE_RUNS_VARIABLES
    raise ValueError(f"unsupported Open-Meteo multi-provider endpoint: {endpoint}")


def _target_valid_time_utc(date_local: dt.date) -> dt.datetime:
    local_23 = dt.datetime.combine(
        date_local,
        dt.time(23, 0),
        tzinfo=ZoneInfo(TZ_NAME),
    )
    return local_23.astimezone(dt.UTC)


def _candidate_run_times_for_date(date_local: dt.date) -> list[dt.datetime]:
    start = dt.datetime.combine(
        date_local - dt.timedelta(days=1),
        dt.time(0, 0),
        tzinfo=dt.UTC,
    )
    return [start + dt.timedelta(hours=6 * offset) for offset in range(9)]


def _selected_run_for_endpoint(
    *,
    endpoint: str,
    date_local: dt.date,
    cp: str,
) -> dict[str, str | int] | None:
    if endpoint != "single_runs":
        return None
    return select_latest_eligible_run(
        cp_utc=cp_to_utc(date_local, cp, TZ_NAME),
        valid_time_utc=_target_valid_time_utc(date_local),
        candidate_run_times_utc=_candidate_run_times_for_date(date_local),
        availability_lag_h=6,
        safety_margin_minutes=10,
    )


def _request_params(
    *,
    endpoint: str,
    model: str,
    date_local: dt.date,
    selected_run: dict[str, str | int] | None,
) -> dict[str, object]:
    params: dict[str, object] = {
        "latitude": WELLINGTON_LATITUDE,
        "longitude": WELLINGTON_LONGITUDE,
        "hourly": ",".join(_endpoint_variables(endpoint)),
        "models": model,
        "start_date": date_local.isoformat(),
        "end_date": date_local.isoformat(),
        "timezone": "auto",
    }
    if endpoint == "single_runs" and selected_run is not None:
        run_dt = dt.datetime.fromisoformat(str(selected_run["selected_run_time_utc"]))
        params["run"] = run_dt.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M")
    return params


def build_multi_provider_probe_plan(
    *,
    dates: list[dt.date] | tuple[dt.date, ...],
    cps: list[str] | tuple[str, ...],
    models: list[str] | tuple[str, ...],
    endpoints: list[str] | tuple[str, ...],
) -> pl.DataFrame:
    registry = build_multi_provider_registry()
    model_rows = {
        str(row["model"]): row for row in registry.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for date_local in dates:
        for cp in cps:
            cp_utc = cp_to_utc(date_local, cp, TZ_NAME)
            valid_time_utc = _target_valid_time_utc(date_local)
            for endpoint in endpoints:
                for model in models:
                    provider = model_rows.get(model)
                    if provider is None:
                        raise ValueError(f"unknown Open-Meteo provider model: {model}")
                    selected_run = _selected_run_for_endpoint(
                        endpoint=endpoint,
                        date_local=date_local,
                        cp=cp,
                    )
                    if endpoint == "single_runs" and selected_run is None:
                        continue
                    params = _request_params(
                        endpoint=endpoint,
                        model=model,
                        date_local=date_local,
                        selected_run=selected_run,
                    )
                    endpoint_url = _endpoint_url(endpoint)
                    request_params_json = json.dumps(params, sort_keys=True)
                    request_url = build_request_url(endpoint_url, params)
                    probe_index = len(rows) + 1
                    rows.append(
                        {
                            "probe_id": f"om_multi_provider_{probe_index:05d}",
                            "station": ICAO,
                            "endpoint": endpoint,
                            "endpoint_url": endpoint_url,
                            "model": model,
                            "provider": provider["provider"],
                            "provider_family": provider["provider_family"],
                            "coverage_expectation": provider[
                                "coverage_expectation"
                            ],
                            "causal_role": provider["causal_role"],
                            "variable_group": "tmax_provider_error_atlas",
                            "date_local": date_local,
                            "calendar_year": date_local.year,
                            "month": f"{date_local:%Y-%m}",
                            "cp": cp,
                            "cp_utc": cp_utc.isoformat(),
                            "target_valid_time_utc": valid_time_utc.isoformat(),
                            "selected_run_time_utc": (
                                selected_run["selected_run_time_utc"]
                                if selected_run is not None
                                else None
                            ),
                            "selected_available_time_utc": (
                                selected_run["selected_available_time_utc"]
                                if selected_run is not None
                                else None
                            ),
                            "selected_lead_h": (
                                selected_run["selected_lead_h"]
                                if selected_run is not None
                                else None
                            ),
                            "request_params_json": request_params_json,
                            "request_url": request_url,
                            "request_url_sha256": hash_text(request_url),
                            "request_params_sha256": hash_text(request_params_json),
                            "production_status": PRODUCTION_STATUS,
                        }
                    )
    return pl.DataFrame(rows, strict=False)


def _safe_hourly_count(text: str) -> int:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return 0
    times = hourly.get("time")
    return len(times) if isinstance(times, list) else 0


def run_multi_provider_probe_plan(
    probe_plan: pl.DataFrame,
    *,
    client: object | None,
    live: bool,
) -> pl.DataFrame:
    if probe_plan.is_empty():
        return pl.DataFrame()
    if live and client is None:
        raise ValueError("client is required when live=True")
    rows: list[dict[str, object]] = []
    for probe in probe_plan.iter_rows(named=True):
        base = dict(probe)
        if not live:
            rows.append(
                {
                    **base,
                    "success": False,
                    "status_code": None,
                    "n_hourly_times": 0,
                    "response_sha256": None,
                    "error": "plan_only_not_requested",
                    "production_status": PRODUCTION_STATUS,
                }
            )
            continue
        params = json.loads(str(probe["request_params_json"]))
        try:
            response = client.get(str(probe["endpoint_url"]), params)
            n_hourly_times = _safe_hourly_count(response.text)
            success = bool(response.ok and n_hourly_times > 0)
            if response.ok and n_hourly_times == 0:
                error = "missing_hourly_time"
            elif response.ok:
                error = None
            else:
                error = f"http_{response.status_code}"
            rows.append(
                {
                    **base,
                    "success": success,
                    "status_code": int(response.status_code),
                    "n_hourly_times": n_hourly_times,
                    "request_url": response.request_url,
                    "request_url_sha256": response.request_url_sha256,
                    "response_sha256": response.response_sha256,
                    "error": error,
                    "production_status": PRODUCTION_STATUS,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    **base,
                    "success": False,
                    "status_code": None,
                    "n_hourly_times": 0,
                    "response_sha256": None,
                    "error": type(exc).__name__,
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _availability_matrix(probe_results: pl.DataFrame) -> pl.DataFrame:
    if probe_results.is_empty():
        return pl.DataFrame()
    return (
        probe_results.group_by(
            [
                "endpoint",
                "model",
                "provider_family",
                "calendar_year",
                "month",
                "cp",
            ]
        )
        .agg(
            pl.len().alias("n_probes"),
            pl.col("success").cast(pl.Int64).sum().alias("n_success"),
            pl.col("selected_run_time_utc").is_not_null().any().alias(
                "has_run_metadata"
            ),
            pl.col("selected_lead_h").is_not_null().any().alias(
                "has_lead_metadata"
            ),
        )
        .with_columns(
            (pl.col("n_success") / pl.col("n_probes") * 100.0).alias("success_pct"),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .sort(["endpoint", "model", "calendar_year", "month", "cp"])
    )


def _decision_status(row: dict[str, object]) -> tuple[str, str]:
    endpoint = str(row["endpoint"])
    n_success = int(row["n_success"] or 0)
    has_run_metadata = bool(row["has_run_metadata"])
    has_lead_metadata = bool(row["has_lead_metadata"])
    errors = str(row.get("errors") or "")
    coverage_expectation = str(row.get("coverage_expectation") or "")

    if n_success > 0 and endpoint == "previous_runs":
        return (
            "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
            "fixed_lead_provider_error_atlas",
        )
    if n_success > 0 and endpoint == "single_runs":
        if has_run_metadata and has_lead_metadata:
            return (
                "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "snapshot_provider_error_atlas",
            )
        return (
            "OPEN_METEO_PROVIDER_BLOCKED_BY_CAUSALITY_METADATA",
            "missing_run_or_lead_metadata",
        )
    if endpoint == "single_runs":
        return (
            "OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT",
            "single_runs_request_contract_not_proven",
        )
    if coverage_expectation == "regional_expected_missing_for_wellington":
        return (
            "OPEN_METEO_PROVIDER_BLOCKED_BY_AVAILABILITY",
            "regional_model_not_available_for_wellington",
        )
    if "http_400" in errors:
        return (
            "OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT",
            "http_400_request_contract_failure",
        )
    return ("OPEN_METEO_PROVIDER_BLOCKED_BY_AVAILABILITY", "no_successful_probe")


def _decision_update(
    registry: pl.DataFrame,
    probe_results: pl.DataFrame,
) -> pl.DataFrame:
    if probe_results.is_empty():
        return pl.DataFrame()
    grouped = (
        probe_results.group_by(
            [
                "endpoint",
                "model",
                "provider",
                "provider_family",
                "coverage_expectation",
                "causal_role",
            ]
        )
        .agg(
            pl.len().alias("n_probes"),
            pl.col("success").cast(pl.Int64).sum().alias("n_success"),
            pl.col("calendar_year")
            .filter(pl.col("success"))
            .n_unique()
            .alias("n_success_years"),
            pl.col("selected_run_time_utc").is_not_null().any().alias(
                "has_run_metadata"
            ),
            pl.col("selected_lead_h").is_not_null().any().alias(
                "has_lead_metadata"
            ),
            pl.col("error").drop_nulls().unique().cast(pl.String).str.join(",").alias(
                "errors"
            ),
        )
        .with_columns(
            (pl.col("n_success") / pl.col("n_probes") * 100.0).alias("success_pct")
        )
    )
    rows: list[dict[str, object]] = []
    for row in grouped.iter_rows(named=True):
        decision_status, feature_gate_scope = _decision_status(row)
        rows.append(
            {
                **row,
                "decision_status": decision_status,
                "feature_gate_scope": feature_gate_scope,
                "production_status": PRODUCTION_STATUS,
            }
        )
    priority = registry.select(["model", "priority_rank"])
    return (
        pl.DataFrame(rows, strict=False)
        .join(priority, on="model", how="left")
        .sort(["priority_rank", "endpoint"])
        .drop("priority_rank")
    )


def build_multi_provider_availability_artifacts(
    *,
    registry: pl.DataFrame,
    probe_plan: pl.DataFrame,
    probe_results: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    return {
        "open_meteo_multi_provider_registry_v1": registry,
        "open_meteo_multi_provider_probe_plan_v1": probe_plan,
        "open_meteo_multi_provider_probe_results_v1": probe_results,
        "open_meteo_multi_provider_availability_matrix_v1": _availability_matrix(
            probe_results
        ),
        "open_meteo_multi_provider_decision_update_v1": _decision_update(
            registry,
            probe_results,
        ),
    }


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


def render_multi_provider_availability_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Multi-Provider Availability Report",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "This audit proves request contracts and availability only. It "
                "does not create model features or approve production use."
            ),
            "## Decision Update",
            _markdown_table(
                artifacts["open_meteo_multi_provider_decision_update_v1"]
            ),
            "## Availability Matrix",
            _markdown_table(
                artifacts["open_meteo_multi_provider_availability_matrix_v1"]
            ),
            "## Registry",
            _markdown_table(artifacts["open_meteo_multi_provider_registry_v1"]),
        ]
    ) + "\n"


def write_multi_provider_availability_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in OPEN_METEO_MULTI_PROVIDER_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_multi_provider_availability_report_v1.md"
    report_path.write_text(
        render_multi_provider_availability_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_multi_provider_availability_report_md"] = report_path
    return paths
