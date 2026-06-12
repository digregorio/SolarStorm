from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm._config import ICAO, TZ_NAME
from solarstorm.open_meteo._client import build_request_url, hash_text

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
WELLINGTON_LATITUDE = -41.3272
WELLINGTON_LONGITUDE = 174.8053
OPEN_METEO_FILENAMES = {
    "source_registry": "open_meteo_source_registry_v1.csv",
    "probe_plan": "open_meteo_probe_plan_v1.csv",
    "probe_results": "open_meteo_probe_results_v1.csv",
    "availability_by_source": "open_meteo_availability_by_source_v1.csv",
    "availability_by_year_month_cp": "open_meteo_availability_by_year_month_cp_v1.csv",
    "causal_selection_audit": "open_meteo_causal_selection_audit_v1.csv",
    "blocked_source_register": "open_meteo_blocked_source_register_v1.csv",
    "decision_update": "open_meteo_decision_update_v1.csv",
}
PROBE_PLAN_SCHEMA = {
    "probe_id": pl.String,
    "station": pl.String,
    "source_id": pl.String,
    "endpoint": pl.String,
    "endpoint_url": pl.String,
    "model": pl.String,
    "variable_group": pl.String,
    "date_local": pl.Date,
    "calendar_year": pl.Int64,
    "month": pl.String,
    "cp": pl.String,
    "cp_utc": pl.String,
    "target_valid_time_utc": pl.String,
    "selected_run_time_utc": pl.String,
    "selected_available_time_utc": pl.String,
    "selected_lead_h": pl.Int64,
    "causal_class": pl.String,
    "request_params_json": pl.String,
    "request_url": pl.String,
    "request_url_sha256": pl.String,
    "request_params_sha256": pl.String,
    "production_status": pl.String,
}
PROBE_RESULTS_SCHEMA = {
    **PROBE_PLAN_SCHEMA,
    "success": pl.Boolean,
    "status_code": pl.Int64,
    "n_hourly_times": pl.Int64,
    "response_sha256": pl.String,
    "error": pl.String,
}
AVAILABILITY_BY_SOURCE_SCHEMA = {
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "causal_class": pl.String,
    "n_probes": pl.Int64,
    "n_success": pl.Int64,
    "n_success_years": pl.Int64,
    "has_run_metadata": pl.Boolean,
    "has_lead_metadata": pl.Boolean,
    "success_pct": pl.Float64,
    "production_status": pl.String,
}
AVAILABILITY_BY_YEAR_MONTH_CP_SCHEMA = {
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "calendar_year": pl.Int64,
    "month": pl.String,
    "cp": pl.String,
    "causal_class": pl.String,
    "n_probes": pl.Int64,
    "n_success": pl.Int64,
    "success_pct": pl.Float64,
    "production_status": pl.String,
}
CAUSAL_SELECTION_AUDIT_SCHEMA = {
    "probe_id": pl.String,
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "date_local": pl.Date,
    "cp": pl.String,
    "cp_utc": pl.String,
    "target_valid_time_utc": pl.String,
    "selected_run_time_utc": pl.String,
    "selected_available_time_utc": pl.String,
    "selected_lead_h": pl.Int64,
    "causal_class": pl.String,
    "success": pl.Boolean,
    "error": pl.String,
    "production_status": pl.String,
}
DECISION_UPDATE_SCHEMA = {
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "causal_class": pl.String,
    "n_probes": pl.Int64,
    "n_success": pl.Int64,
    "n_success_years": pl.Int64,
    "has_run_metadata": pl.Boolean,
    "has_lead_metadata": pl.Boolean,
    "success_pct": pl.Float64,
    "decision_status": pl.String,
    "pilot_scope_note": pl.String,
    "production_status": pl.String,
}
DEFAULT_VARIABLES = (
    "temperature_2m",
    "dew_point_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "pressure_msl",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
)
PREVIOUS_RUNS_GFS_TEMPERATURE_VARIABLES = (
    "temperature_2m_previous_day1",
    "dew_point_2m_previous_day1",
    "cloud_cover_previous_day1",
    "cloud_cover_low_previous_day1",
    "pressure_msl_previous_day1",
    "wind_speed_10m_previous_day1",
    "wind_gusts_10m_previous_day1",
    "wind_direction_10m_previous_day1",
)


@dataclass(frozen=True)
class OpenMeteoSource:
    source_id: str
    endpoint: str
    endpoint_url: str
    model: str
    causal_class: str
    nominal_available_from: dt.date | None
    expected_run_cadence_h: int | None
    expected_horizon_h: int | None
    default_decision: str
    variables: tuple[str, ...] = DEFAULT_VARIABLES


SOURCE_REGISTRY: tuple[OpenMeteoSource, ...] = (
    OpenMeteoSource(
        source_id="forecast_api_best_match",
        endpoint="forecast",
        endpoint_url="https://api.open-meteo.com/v1/forecast",
        model="best_match",
        causal_class="live_seamless_forecast",
        nominal_available_from=None,
        expected_run_cadence_h=None,
        expected_horizon_h=168,
        default_decision="USE_LIVE_FORWARD_COLLECTION_ONLY",
    ),
    OpenMeteoSource(
        source_id="historical_forecast_best_match",
        endpoint="historical_forecast",
        endpoint_url="https://historical-forecast-api.open-meteo.com/v1/forecast",
        model="best_match",
        causal_class="seamless_historical_forecast",
        nominal_available_from=dt.date(2021, 1, 1),
        expected_run_cadence_h=None,
        expected_horizon_h=None,
        default_decision="AUDIT_ONLY_UNTIL_CAUSAL_METADATA_PROVEN",
    ),
    OpenMeteoSource(
        source_id="previous_runs_gfs_temperature",
        endpoint="previous_runs",
        endpoint_url="https://previous-runs-api.open-meteo.com/v1/forecast",
        model="gfs_seamless",
        causal_class="fixed_lead_forecast",
        nominal_available_from=dt.date(2021, 3, 23),
        expected_run_cadence_h=6,
        expected_horizon_h=168,
        default_decision="FIXED_LEAD_SKILL_AUDIT_ONLY",
        variables=PREVIOUS_RUNS_GFS_TEMPERATURE_VARIABLES,
    ),
    OpenMeteoSource(
        source_id="single_runs_ecmwf_ifs_hres",
        endpoint="single_runs",
        endpoint_url="https://single-runs-api.open-meteo.com/v1/forecast",
        model="ecmwf_ifs025",
        causal_class="forecast_snapshot",
        nominal_available_from=dt.date(2024, 3, 14),
        expected_run_cadence_h=6,
        expected_horizon_h=240,
        default_decision="PRIMARY_CAUSAL_PILOT_CANDIDATE",
    ),
    OpenMeteoSource(
        source_id="historical_weather_era5",
        endpoint="historical_weather",
        endpoint_url="https://archive-api.open-meteo.com/v1/archive",
        model="era5",
        causal_class="reanalysis_not_forecast",
        nominal_available_from=dt.date(1940, 1, 1),
        expected_run_cadence_h=None,
        expected_horizon_h=None,
        default_decision="DIAGNOSTIC_ONLY_BLOCKED_AS_CAUSAL_PREDICTOR",
    ),
)


def _to_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("select_latest_eligible_run requires UTC-aware datetimes")
    return value.astimezone(dt.UTC)


def cp_local_to_utc(
    date_local: dt.date,
    cp: str,
    tz_name: str = TZ_NAME,
) -> dt.datetime:
    cp_time = dt.time.fromisoformat(cp)
    local = dt.datetime.combine(date_local, cp_time, tzinfo=ZoneInfo(tz_name))
    return local.astimezone(dt.UTC)


def _local_anchor_to_utc(date_local: dt.date, hour: int) -> dt.datetime:
    local = dt.datetime.combine(
        date_local,
        dt.time(hour, 0),
        tzinfo=ZoneInfo(TZ_NAME),
    )
    return local.astimezone(dt.UTC)


def _candidate_run_times_for_date(date_local: dt.date) -> list[dt.datetime]:
    start = dt.datetime.combine(
        date_local - dt.timedelta(days=1),
        dt.time(0, 0),
        tzinfo=dt.UTC,
    )
    return [start + dt.timedelta(hours=6 * offset) for offset in range(9)]


def select_latest_eligible_run(
    *,
    cp_utc: dt.datetime,
    valid_time_utc: dt.datetime,
    candidate_run_times_utc: list[dt.datetime] | tuple[dt.datetime, ...],
    availability_lag_h: int,
    safety_margin_minutes: int,
) -> dict[str, str | int] | None:
    cp_utc = _to_utc(cp_utc)
    valid_time_utc = _to_utc(valid_time_utc)
    availability_delta = dt.timedelta(
        hours=availability_lag_h,
        minutes=safety_margin_minutes,
    )

    selected: tuple[dt.datetime, dt.datetime] | None = None
    for candidate_run_time in candidate_run_times_utc:
        run_time_utc = _to_utc(candidate_run_time)
        if valid_time_utc <= run_time_utc:
            continue

        available_time_utc = run_time_utc + availability_delta
        if available_time_utc > cp_utc:
            continue

        if selected is None or run_time_utc > selected[0]:
            selected = (run_time_utc, available_time_utc)

    if selected is None:
        return None

    run_time_utc, available_time_utc = selected
    lead_h = int((valid_time_utc - run_time_utc).total_seconds() // 3600)
    return {
        "selected_run_time_utc": run_time_utc.isoformat(),
        "selected_available_time_utc": available_time_utc.isoformat(),
        "selected_valid_time_utc": valid_time_utc.isoformat(),
        "selected_lead_h": lead_h,
        "cp_utc": cp_utc.isoformat(),
    }


def build_source_registry_frame(
    *,
    station: str = ICAO,
    latitude: float = WELLINGTON_LATITUDE,
    longitude: float = WELLINGTON_LONGITUDE,
) -> pl.DataFrame:
    rows = []
    for source in SOURCE_REGISTRY:
        rows.append(
            {
                "station": station,
                "latitude": latitude,
                "longitude": longitude,
                "source_id": source.source_id,
                "endpoint": source.endpoint,
                "endpoint_url": source.endpoint_url,
                "model": source.model,
                "causal_class": source.causal_class,
                "nominal_available_from": source.nominal_available_from,
                "expected_run_cadence_h": source.expected_run_cadence_h,
                "expected_horizon_h": source.expected_horizon_h,
                "variables": ",".join(source.variables),
                "default_decision": source.default_decision,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows)


def build_blocked_source_register(registry: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for row in registry.iter_rows(named=True):
        source_id = str(row["source_id"])
        causal_class = str(row["causal_class"])
        if causal_class == "forecast_snapshot":
            allowed = True
            reason = "run_initialisation_preserved"
        elif causal_class == "fixed_lead_forecast":
            allowed = False
            reason = "fixed_lead_audit_only"
        elif causal_class == "seamless_historical_forecast":
            allowed = False
            reason = "seamless_no_run_metadata_until_proven"
        elif causal_class == "live_seamless_forecast":
            allowed = False
            reason = "live_seamless_no_historical_runs"
        elif causal_class == "reanalysis_not_forecast":
            allowed = False
            reason = "reanalysis_not_forecast"
        else:
            allowed = False
            reason = f"unknown_causal_class:{causal_class}"

        rows.append(
            {
                "source_id": source_id,
                "endpoint": row["endpoint"],
                "model": row["model"],
                "causal_class": causal_class,
                "causal_feature_allowed": allowed,
                "blocked_reason": reason,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows)


def _source_request_params(
    row: dict[str, object],
    *,
    date_local: dt.date,
    selected_run: dict[str, str | int] | None,
) -> dict[str, object]:
    params: dict[str, object] = {
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "hourly": row["variables"],
        "start_date": date_local.isoformat(),
        "end_date": date_local.isoformat(),
        "timezone": "auto",
    }
    model = str(row["model"])
    endpoint = str(row["endpoint"])
    if model != "best_match":
        params["models"] = model
    if endpoint == "single_runs" and selected_run is not None:
        run_dt = dt.datetime.fromisoformat(str(selected_run["selected_run_time_utc"]))
        params["run"] = run_dt.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M")
    return params


def build_probe_plan(
    registry: pl.DataFrame,
    *,
    years: list[int] | tuple[int, ...] = (2022, 2023, 2024, 2025),
    cps: list[str] | tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    month_days: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (
        (1, 15),
        (4, 15),
        (7, 15),
        (10, 15),
    ),
    include_live_forecast: bool = False,
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for source in registry.iter_rows(named=True):
        if source["endpoint"] == "forecast" and not include_live_forecast:
            continue

        nominal_from = source["nominal_available_from"]
        for year in years:
            for month, day in month_days:
                date_local = dt.date(int(year), int(month), int(day))
                if nominal_from is not None and date_local < nominal_from:
                    continue

                for cp in cps:
                    cp_utc = cp_local_to_utc(date_local, cp)
                    target_valid_time_utc = _local_anchor_to_utc(date_local, 23)
                    selected_run = None
                    if source["causal_class"] == "forecast_snapshot":
                        selected_run = select_latest_eligible_run(
                            cp_utc=cp_utc,
                            valid_time_utc=target_valid_time_utc,
                            candidate_run_times_utc=_candidate_run_times_for_date(
                                date_local
                            ),
                            availability_lag_h=6,
                            safety_margin_minutes=10,
                        )
                        if selected_run is None:
                            continue

                    request_params = _source_request_params(
                        source,
                        date_local=date_local,
                        selected_run=selected_run,
                    )
                    request_params_json = json.dumps(
                        request_params,
                        sort_keys=True,
                    )
                    request_url = build_request_url(
                        str(source["endpoint_url"]),
                        request_params,
                    )
                    probe_index = len(rows) + 1
                    rows.append(
                        {
                            "probe_id": f"om_probe_{probe_index:05d}",
                            "station": source["station"],
                            "source_id": source["source_id"],
                            "endpoint": source["endpoint"],
                            "endpoint_url": source["endpoint_url"],
                            "model": source["model"],
                            "variable_group": "initial_physical_tmax_set",
                            "date_local": date_local,
                            "calendar_year": date_local.year,
                            "month": f"{date_local:%Y-%m}",
                            "cp": cp,
                            "cp_utc": cp_utc.isoformat(),
                            "target_valid_time_utc": (
                                target_valid_time_utc.isoformat()
                            ),
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
                            "causal_class": source["causal_class"],
                            "request_params_json": request_params_json,
                            "request_url": request_url,
                            "request_url_sha256": hash_text(request_url),
                            "request_params_sha256": hash_text(request_params_json),
                            "production_status": PRODUCTION_STATUS,
                        }
                    )

    return pl.DataFrame(rows, schema=PROBE_PLAN_SCHEMA)


def _safe_json_loads(text: str) -> dict[str, object]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _request_params_from_json(text: str) -> dict[str, object] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _hourly_count(response_text: str) -> int:
    payload = _safe_json_loads(response_text)
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return 0
    times = hourly.get("time")
    return len(times) if isinstance(times, list) else 0


def run_probe_plan(
    probe_plan: pl.DataFrame,
    *,
    client: object | None,
    live: bool,
) -> pl.DataFrame:
    if probe_plan.is_empty():
        return pl.DataFrame(schema=PROBE_RESULTS_SCHEMA)

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

        params = _request_params_from_json(str(probe["request_params_json"]))
        if params is None:
            rows.append(
                {
                    **base,
                    "success": False,
                    "status_code": None,
                    "n_hourly_times": 0,
                    "response_sha256": None,
                    "error": "invalid_request_params_json",
                    "production_status": PRODUCTION_STATUS,
                }
            )
            continue

        try:
            response = client.get(str(probe["endpoint_url"]), params)
            n_hourly_times = _hourly_count(response.text)
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
    return pl.DataFrame(rows, schema=PROBE_RESULTS_SCHEMA)


def _availability_by_source(
    registry: pl.DataFrame,
    probe_results: pl.DataFrame,
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for source in registry.iter_rows(named=True):
        source_results = probe_results.filter(
            pl.col("source_id") == source["source_id"]
        )
        n_probes = source_results.height
        success_rows = [
            row for row in source_results.iter_rows(named=True) if bool(row["success"])
        ]
        n_success = len(success_rows)
        n_success_years = len({row["calendar_year"] for row in success_rows})
        has_run_metadata = any(
            row["selected_run_time_utc"] is not None
            for row in source_results.iter_rows(named=True)
        )
        has_lead_metadata = any(
            row["selected_lead_h"] is not None
            for row in source_results.iter_rows(named=True)
        )
        rows.append(
            {
                "source_id": source["source_id"],
                "endpoint": source["endpoint"],
                "model": source["model"],
                "causal_class": source["causal_class"],
                "n_probes": n_probes,
                "n_success": n_success,
                "n_success_years": n_success_years,
                "has_run_metadata": has_run_metadata,
                "has_lead_metadata": has_lead_metadata,
                "success_pct": (n_success / n_probes * 100.0) if n_probes else 0.0,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, schema=AVAILABILITY_BY_SOURCE_SCHEMA).sort("source_id")


def _availability_by_year_month_cp(probe_results: pl.DataFrame) -> pl.DataFrame:
    if probe_results.is_empty():
        return pl.DataFrame(schema=AVAILABILITY_BY_YEAR_MONTH_CP_SCHEMA)
    return (
        probe_results.group_by(
            [
                "source_id",
                "endpoint",
                "model",
                "calendar_year",
                "month",
                "cp",
                "causal_class",
            ]
        )
        .agg(
            pl.len().alias("n_probes"),
            pl.col("success").cast(pl.Int64).sum().alias("n_success"),
        )
        .with_columns(
            (pl.col("n_success") / pl.col("n_probes") * 100.0).alias("success_pct"),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .select(AVAILABILITY_BY_YEAR_MONTH_CP_SCHEMA.keys())
        .sort(["source_id", "calendar_year", "month", "cp"])
    )


def _causal_selection_audit(probe_results: pl.DataFrame) -> pl.DataFrame:
    if probe_results.is_empty():
        return pl.DataFrame(schema=CAUSAL_SELECTION_AUDIT_SCHEMA)
    return probe_results.select(
        CAUSAL_SELECTION_AUDIT_SCHEMA.keys()
    )


def build_availability_summaries(
    registry: pl.DataFrame,
    probe_plan: pl.DataFrame,
    probe_results: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    return {
        "source_registry": registry,
        "probe_plan": probe_plan,
        "probe_results": probe_results,
        "availability_by_source": _availability_by_source(registry, probe_results),
        "availability_by_year_month_cp": _availability_by_year_month_cp(
            probe_results
        ),
        "causal_selection_audit": _causal_selection_audit(probe_results),
        "blocked_source_register": build_blocked_source_register(registry),
    }


def _decision_for_source(row: dict[str, object]) -> tuple[str, str]:
    causal_class = str(row["causal_class"])
    n_success = int(row["n_success"] or 0)
    n_success_years = int(row["n_success_years"] or 0)
    has_run_metadata = bool(row["has_run_metadata"])
    has_lead_metadata = bool(row["has_lead_metadata"])

    if causal_class == "reanalysis_not_forecast":
        return (
            "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA",
            "diagnostic_only_reanalysis",
        )
    if causal_class == "live_seamless_forecast":
        return (
            "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA",
            "live_forward_collection_only",
        )
    if causal_class == "seamless_historical_forecast":
        return (
            "OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY",
            "requires_run_metadata_before_causal_use",
        )
    if causal_class == "fixed_lead_forecast":
        if n_success > 0:
            return (
                "OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT",
                "fixed_lead_skill_audit_only",
            )
        return ("OPEN_METEO_BLOCKED_BY_AVAILABILITY", "no_successful_probe")
    if causal_class == "forecast_snapshot":
        if n_success == 0:
            return ("OPEN_METEO_BLOCKED_BY_AVAILABILITY", "no_successful_probe")
        if has_run_metadata and has_lead_metadata:
            pilot_scope_note = (
                "full_nested_window_candidate"
                if n_success_years >= 2
                else "narrow_to_available_window"
            )
            return ("OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT", pilot_scope_note)
        return (
            "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA",
            "missing_run_or_lead_metadata",
        )
    return ("OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA", "unknown_causal_class")


def build_decision_update(availability_by_source: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for row in availability_by_source.iter_rows(named=True):
        decision_status, pilot_scope_note = _decision_for_source(row)
        rows.append(
            {
                "source_id": row["source_id"],
                "endpoint": row["endpoint"],
                "model": row["model"],
                "causal_class": row["causal_class"],
                "n_probes": row["n_probes"],
                "n_success": row["n_success"],
                "n_success_years": row["n_success_years"],
                "has_run_metadata": row["has_run_metadata"],
                "has_lead_metadata": row["has_lead_metadata"],
                "success_pct": row["success_pct"],
                "decision_status": decision_status,
                "pilot_scope_note": pilot_scope_note,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, schema=DECISION_UPDATE_SCHEMA).sort("source_id")


def assert_no_open_meteo_features_created(
    output_dir: Path,
    *,
    data_dir: Path | None = None,
) -> None:
    blocked_paths = [output_dir / "open_meteo_features.parquet"]
    if data_dir is not None:
        blocked_paths.append(data_dir / "open_meteo_features.parquet")
    for feature_path in blocked_paths:
        if not feature_path.exists():
            continue
        raise AssertionError(
            "Open-Meteo feature generation is blocked; "
            f"unexpected feature file exists at {feature_path}"
        )


def _markdown_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        text = f"{value:.2f}"
    elif isinstance(value, dt.date | dt.datetime):
        text = value.isoformat()
    else:
        text = str(value)
    return text.replace("|", "\\|")


def _markdown_table(
    frame: pl.DataFrame,
    columns: list[str] | tuple[str, ...],
    limit: int = 20,
) -> str:
    if frame.is_empty():
        return "No rows."

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| "
        + " | ".join(_markdown_cell(row[column]) for column in columns)
        + " |"
        for row in frame.select(columns).head(limit).iter_rows(named=True)
    ]
    if frame.height > limit:
        truncation_cells = ["...", f"{frame.height - limit} more rows"]
        truncation_cells.extend("" for _ in range(len(columns) - 2))
        rows.append("| " + " | ".join(truncation_cells) + " |")
    return "\n".join([header, separator, *rows])


def render_availability_report(
    summaries: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    decision_update = summaries["decision_update"]
    availability_by_source = summaries["availability_by_source"]
    blocked_source_register = summaries["blocked_source_register"]

    sections = [
        f"# Open-Meteo Availability Report - {today.isoformat()}",
        "",
        f"production_status: {PRODUCTION_STATUS}",
        "",
        "This is an audit-only availability report. It does not write "
        "Open-Meteo causal features or promote any source by itself.",
        "",
        "Historical Weather / reanalysis is blocked from causal feature generation.",
        "Historical Forecast remains audit-only unless CP-causal run metadata is proven.",
        "Single Runs can narrow a pilot to its available history instead of changing "
        "the Onda 3H baseline.",
        "This availability audit does not write open_meteo_features.parquet.",
        "",
        "## Decision Update",
        "",
        _markdown_table(
            decision_update,
            [
                "source_id",
                "endpoint",
                "model",
                "causal_class",
                "n_probes",
                "n_success",
                "n_success_years",
                "success_pct",
                "decision_status",
                "pilot_scope_note",
                "production_status",
            ],
        ),
        "",
        "## Availability by Source",
        "",
        _markdown_table(
            availability_by_source,
            [
                "source_id",
                "endpoint",
                "model",
                "causal_class",
                "n_probes",
                "n_success",
                "n_success_years",
                "has_run_metadata",
                "has_lead_metadata",
                "success_pct",
                "production_status",
            ],
        ),
        "",
        "## Blocked Source Register",
        "",
        _markdown_table(
            blocked_source_register,
            [
                "source_id",
                "endpoint",
                "model",
                "causal_class",
                "causal_feature_allowed",
                "blocked_reason",
                "production_status",
            ],
        ),
        "",
    ]
    return "\n".join(sections)


def write_open_meteo_availability_artifacts(
    summaries: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
    data_dir: Path = Path("data"),
) -> dict[str, Path]:
    artifact_frames = dict(summaries)
    if (
        "decision_update" not in artifact_frames
        and "availability_by_source" in artifact_frames
    ):
        artifact_frames["decision_update"] = build_decision_update(
            artifact_frames["availability_by_source"]
        )

    missing = sorted(set(OPEN_METEO_FILENAMES) - set(artifact_frames))
    if missing:
        raise ValueError(
            "missing Open-Meteo artifact summaries: " + ", ".join(missing)
        )

    assert_no_open_meteo_features_created(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    for artifact_key, filename in OPEN_METEO_FILENAMES.items():
        path = output_dir / filename
        artifact_frames[artifact_key].write_csv(path)
        paths[artifact_key] = path

    report_path = output_dir / "open_meteo_availability_report_v1.md"
    report_path.write_text(
        render_availability_report(artifact_frames, today=today),
        encoding="utf-8",
    )
    paths["availability_report_md"] = report_path

    assert_no_open_meteo_features_created(output_dir)
    return paths
