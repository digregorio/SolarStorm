from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc
from solarstorm.open_meteo._availability import PRODUCTION_STATUS
from solarstorm.open_meteo._client import hash_text

FEATURE_ELIGIBILITY_SCHEMA = {
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "causal_class": pl.String,
    "decision_status": pl.String,
    "n_success": pl.Int64,
    "feature_generation_allowed": pl.Boolean,
    "feature_generation_reason": pl.String,
    "production_status": pl.String,
}
OPEN_METEO_FEATURE_FILENAMES = {
    "open_meteo_feature_manifest_v1": "open_meteo_feature_manifest_v1.csv",
    "open_meteo_feature_coverage_v1": "open_meteo_feature_coverage_v1.csv",
    "open_meteo_feature_source_eligibility_v1": (
        "open_meteo_feature_source_eligibility_v1.csv"
    ),
    "open_meteo_feature_blocked_sources_v1": (
        "open_meteo_feature_blocked_sources_v1.csv"
    ),
}
RAW_RESPONSE_CACHE_SCHEMA = {
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "date_local": pl.Date,
    "success": pl.Boolean,
    "status_code": pl.Int64,
    "request_url": pl.String,
    "request_url_sha256": pl.String,
    "response_sha256": pl.String,
    "response_text": pl.String,
    "error": pl.String,
    "production_status": pl.String,
}


def _feature_decision(row: dict[str, object]) -> tuple[bool, str]:
    source_id = str(row["source_id"])
    causal_class = str(row["causal_class"])
    decision_status = str(row["decision_status"])
    n_success = int(row["n_success"] or 0)
    has_run_metadata = bool(row.get("has_run_metadata", False))
    has_lead_metadata = bool(row.get("has_lead_metadata", False))

    if causal_class == "fixed_lead_forecast":
        if (
            source_id == "previous_runs_gfs_temperature"
            and decision_status == "OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT"
            and n_success > 0
        ):
            return True, "fixed_lead_forecast_pilot_allowed"
        return False, "fixed_lead_forecast_no_success"
    if causal_class == "forecast_snapshot":
        if (
            decision_status == "OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT"
            and n_success > 0
            and has_run_metadata
            and has_lead_metadata
        ):
            return True, "forecast_snapshot_pilot_allowed"
        return False, "forecast_snapshot_not_available"
    if causal_class == "reanalysis_not_forecast":
        return False, "reanalysis_blocked_as_predictor"
    if causal_class == "seamless_historical_forecast":
        return False, "seamless_historical_forecast_lacks_run_metadata"
    if causal_class == "live_seamless_forecast":
        return False, "live_forecast_forward_collection_only"
    return False, f"unknown_causal_class:{causal_class}"


def build_feature_source_eligibility(decision_update: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for row in decision_update.iter_rows(named=True):
        allowed, reason = _feature_decision(row)
        rows.append(
            {
                "source_id": row["source_id"],
                "endpoint": row["endpoint"],
                "model": row["model"],
                "causal_class": row["causal_class"],
                "decision_status": row["decision_status"],
                "n_success": row["n_success"],
                "feature_generation_allowed": allowed,
                "feature_generation_reason": reason,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, schema=FEATURE_ELIGIBILITY_SCHEMA).sort("source_id")


def ensure_source_allowed_for_features(
    eligibility: pl.DataFrame,
    source_id: str,
) -> str:
    rows = eligibility.filter(pl.col("source_id") == source_id)
    if rows.is_empty():
        raise ValueError(f"missing Open-Meteo source decision for {source_id}")
    row = rows.row(0, named=True)
    if not bool(row["feature_generation_allowed"]):
        raise ValueError(
            f"Open-Meteo source {source_id} is blocked for feature generation: "
            f"{row['feature_generation_reason']}"
        )
    return str(row["feature_generation_reason"])


def build_raw_response_cache(
    *,
    probe_plan: pl.DataFrame,
    eligibility: pl.DataFrame,
    client: object,
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for probe in probe_plan.iter_rows(named=True):
        source_id = str(probe["source_id"])
        source_rows = eligibility.filter(pl.col("source_id") == source_id)
        if source_rows.is_empty():
            continue
        if not bool(source_rows.row(0, named=True)["feature_generation_allowed"]):
            continue
        params = json.loads(str(probe["request_params_json"]))
        if not isinstance(params, dict):
            continue
        try:
            response = client.get(str(probe["endpoint_url"]), params)
            success = bool(response.ok)
            rows.append(
                {
                    "source_id": source_id,
                    "endpoint": probe["endpoint"],
                    "model": probe["model"],
                    "date_local": probe["date_local"],
                    "success": success,
                    "status_code": int(response.status_code),
                    "request_url": response.request_url,
                    "request_url_sha256": response.request_url_sha256,
                    "response_sha256": response.response_sha256,
                    "response_text": response.text,
                    "error": None if success else f"http_{response.status_code}",
                    "production_status": PRODUCTION_STATUS,
                }
            )
        except Exception as exc:
            request_url = str(probe.get("request_url", ""))
            rows.append(
                {
                    "source_id": source_id,
                    "endpoint": probe["endpoint"],
                    "model": probe["model"],
                    "date_local": probe["date_local"],
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
    return pl.DataFrame(rows, schema=RAW_RESPONSE_CACHE_SCHEMA)


def _series(hourly: dict[str, object], name: str) -> list[float | None]:
    values = hourly.get(name, [])
    if not isinstance(values, list):
        return []
    return [None if value is None else float(value) for value in values]


def _mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def _max(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return max(clean) if clean else None


def _min(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return min(clean) if clean else None


def _circular_mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    sin_sum = sum(math.sin(math.radians(value)) for value in clean)
    cos_sum = sum(math.cos(math.radians(value)) for value in clean)
    if abs(sin_sum) < 1e-12 and abs(cos_sum) < 1e-12:
        return None
    return math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0


def _hour_index(hourly: dict[str, object]) -> dict[int, int]:
    times = hourly.get("time", [])
    if not isinstance(times, list):
        return {}
    result: dict[int, int] = {}
    for index, value in enumerate(times):
        if not isinstance(value, str):
            continue
        result[dt.datetime.fromisoformat(value).hour] = index
    return result


def _at(values: list[float | None], index: int | None) -> float | None:
    if index is None or index < 0 or index >= len(values):
        return None
    return values[index]


def _cp_local_hour(date_local: dt.date, cp: str) -> int:
    return cp_to_utc(date_local, cp, TZ_NAME).astimezone(ZoneInfo(TZ_NAME)).hour


def _foehn_support(
    *,
    wind_speed_mean: float | None,
    wind_dir_mean: float | None,
    dewpoint_depression_23: float | None,
) -> float | None:
    if wind_speed_mean is None or wind_dir_mean is None:
        return None
    if dewpoint_depression_23 is None:
        return None
    nw_component = 1.0 if wind_dir_mean >= 270.0 or wind_dir_mean <= 45.0 else 0.0
    return wind_speed_mean * dewpoint_depression_23 * nw_component


def _stratus_support(
    *,
    cloud_low_mean: float | None,
    dewpoint_depression_23: float | None,
) -> float | None:
    if cloud_low_mean is None or dewpoint_depression_23 is None:
        return None
    moist_factor = max(0.0, 10.0 - dewpoint_depression_23)
    return cloud_low_mean * moist_factor / 10.0


def build_previous_runs_feature_rows(
    *,
    payload: dict[str, object],
    source_id: str,
    endpoint: str,
    model: str,
    date_local: dt.date,
    cps: list[str] | tuple[str, ...],
    request_url_sha256: str,
    response_sha256: str,
) -> pl.DataFrame:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("Open-Meteo Previous Runs payload is missing hourly data")

    hour_to_index = _hour_index(hourly)
    temp = _series(hourly, "temperature_2m_previous_day1")
    dewpoint = _series(hourly, "dew_point_2m_previous_day1")
    cloud = _series(hourly, "cloud_cover_previous_day1")
    cloud_low = _series(hourly, "cloud_cover_low_previous_day1")
    pressure = _series(hourly, "pressure_msl_previous_day1")
    wind_speed = _series(hourly, "wind_speed_10m_previous_day1")
    wind_gusts = _series(hourly, "wind_gusts_10m_previous_day1")
    wind_dir = _series(hourly, "wind_direction_10m_previous_day1")

    idx23 = hour_to_index.get(23)
    temp23 = _at(temp, idx23)
    dew23 = _at(dewpoint, idx23)
    wind_dir_mean = _circular_mean(wind_dir)
    wind_speed_mean = _mean(wind_speed)
    cloud_low_mean = _mean(cloud_low)
    dewpoint_depression_23 = (
        temp23 - dew23 if temp23 is not None and dew23 is not None else None
    )
    rows: list[dict[str, object]] = []
    for cp in cps:
        cp_index = hour_to_index.get(_cp_local_hour(date_local, cp))
        temp_cp = _at(temp, cp_index)
        rows.append(
            {
                "date_local": date_local,
                "cp": cp,
                "om_source_id": source_id,
                "om_endpoint": endpoint,
                "om_model": model,
                "om_causal_class": "fixed_lead_forecast",
                "om_feature_status": "fixed_lead_forecast_pilot_allowed",
                "om_request_url_sha256": request_url_sha256,
                "om_response_sha256": response_sha256,
                "om_run_time_utc": None,
                "om_available_time_utc": None,
                "om_valid_time_utc": None,
                "om_lead_h": None,
                "om_fixed_lead_days": 1,
                "om_fixed_lead_hours": 24,
                "om_prev_d1_temp_23_local_c": temp23,
                "om_prev_d1_temp_cp_c": temp_cp,
                "om_prev_d1_remaining_warming_c": (
                    temp23 - temp_cp
                    if temp23 is not None and temp_cp is not None
                    else None
                ),
                "om_prev_d1_day_max_c": _max(temp),
                "om_prev_d1_day_min_c": _min(temp),
                "om_prev_d1_cloud_cover_mean_pct": _mean(cloud),
                "om_prev_d1_cloud_cover_low_mean_pct": cloud_low_mean,
                "om_prev_d1_pressure_msl_mean_hpa": _mean(pressure),
                "om_prev_d1_wind_speed_10m_mean": wind_speed_mean,
                "om_prev_d1_wind_gusts_10m_max": _max(wind_gusts),
                "om_prev_d1_wind_dir_10m_circular_mean": wind_dir_mean,
                "om_prev_d1_dewpoint_depression_23_local_c": (
                    dewpoint_depression_23
                ),
                "om_prev_d1_foehn_support": _foehn_support(
                    wind_speed_mean=wind_speed_mean,
                    wind_dir_mean=wind_dir_mean,
                    dewpoint_depression_23=dewpoint_depression_23,
                ),
                "om_prev_d1_stratus_support": _stratus_support(
                    cloud_low_mean=cloud_low_mean,
                    dewpoint_depression_23=dewpoint_depression_23,
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _empty_features() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "date_local": pl.Date,
            "cp": pl.String,
            "production_status": pl.String,
        }
    )


def _parse_response_text(text: str) -> dict[str, object]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Open-Meteo response payload must be a JSON object")
    return payload


def _feature_manifest(features: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for column in features.columns:
        if column in {"date_local", "cp", "production_status"}:
            continue
        rows.append(
            {
                "feature": column,
                "feature_source": "open_meteo_previous_runs",
                "non_null_rows": features.height - features[column].null_count(),
                "n_rows": features.height,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _feature_coverage(features: pl.DataFrame) -> pl.DataFrame:
    if features.is_empty():
        return pl.DataFrame(
            [
                {
                    "n_feature_rows": 0,
                    "n_dates": 0,
                    "n_cps": 0,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    return pl.DataFrame(
        [
            {
                "n_feature_rows": features.height,
                "n_dates": features["date_local"].n_unique(),
                "n_cps": features["cp"].n_unique(),
                "min_date": features["date_local"].min(),
                "max_date": features["date_local"].max(),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def _duplicate_key_count(features: pl.DataFrame) -> int:
    if features.is_empty():
        return 0
    return features.height - features.select(["date_local", "cp"]).unique().height


def _blocked_sources_frame(rows: list[dict[str, object]]) -> pl.DataFrame:
    if rows:
        return pl.DataFrame(rows, strict=False)
    return pl.DataFrame(
        schema={
            "source_id": pl.String,
            "endpoint": pl.String,
            "model": pl.String,
            "blocked_reason": pl.String,
            "production_status": pl.String,
        }
    )


def build_open_meteo_feature_artifacts(
    *,
    raw_responses: pl.DataFrame,
    decision_update: pl.DataFrame,
    cps: list[str] | tuple[str, ...],
) -> dict[str, pl.DataFrame]:
    eligibility = build_feature_source_eligibility(decision_update)
    feature_frames: list[pl.DataFrame] = []
    blocked_rows: list[dict[str, object]] = []

    for row in raw_responses.iter_rows(named=True):
        source_id = str(row["source_id"])
        source_rows = eligibility.filter(pl.col("source_id") == source_id)
        if source_rows.is_empty():
            reason = "missing_source_decision"
            allowed = False
        else:
            source_decision = source_rows.row(0, named=True)
            reason = str(source_decision["feature_generation_reason"])
            allowed = bool(source_decision["feature_generation_allowed"])

        if not allowed:
            blocked_rows.append(
                {
                    "source_id": source_id,
                    "endpoint": row["endpoint"],
                    "model": row["model"],
                    "blocked_reason": reason,
                    "production_status": PRODUCTION_STATUS,
                }
            )
            continue

        if source_id == "previous_runs_gfs_temperature":
            feature_frames.append(
                build_previous_runs_feature_rows(
                    payload=_parse_response_text(str(row["response_text"])),
                    source_id=source_id,
                    endpoint=str(row["endpoint"]),
                    model=str(row["model"]),
                    date_local=row["date_local"],
                    cps=cps,
                    request_url_sha256=str(row["request_url_sha256"]),
                    response_sha256=str(row["response_sha256"]),
                )
            )

    features = (
        pl.concat(feature_frames, how="diagonal_relaxed")
        if feature_frames
        else _empty_features()
    )
    if _duplicate_key_count(features):
        raise ValueError("duplicate Open-Meteo feature keys for date_local, cp")

    return {
        "open_meteo_features_v1": features,
        "open_meteo_feature_manifest_v1": _feature_manifest(features),
        "open_meteo_feature_coverage_v1": _feature_coverage(features),
        "open_meteo_feature_source_eligibility_v1": eligibility,
        "open_meteo_feature_blocked_sources_v1": _blocked_sources_frame(
            blocked_rows
        ),
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


def render_open_meteo_feature_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Feature Build Report",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Historical Weather and Historical Forecast remain blocked as "
                "causal predictors."
            ),
            "Previous Runs features are fixed-lead experiment-only predictors.",
            "## Coverage",
            _markdown_table(artifacts["open_meteo_feature_coverage_v1"]),
            "## Source Eligibility",
            _markdown_table(artifacts["open_meteo_feature_source_eligibility_v1"]),
            "## Feature Manifest",
            _markdown_table(artifacts["open_meteo_feature_manifest_v1"]),
            "## Blocked Sources",
            _markdown_table(artifacts["open_meteo_feature_blocked_sources_v1"]),
        ]
    ) + "\n"


def write_open_meteo_feature_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    data_dir: Path,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    features_path = data_dir / "open_meteo_features.parquet"
    artifacts["open_meteo_features_v1"].write_parquet(features_path)
    paths["open_meteo_features_parquet"] = features_path

    for key, filename in OPEN_METEO_FEATURE_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path

    report_path = output_dir / "open_meteo_feature_report_v1.md"
    report_path.write_text(
        render_open_meteo_feature_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_feature_report_md"] = report_path
    return paths
