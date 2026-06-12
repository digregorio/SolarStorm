from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.open_meteo._availability import PRODUCTION_STATUS

OPEN_METEO_FORWARD_COLLECTION_FILENAMES = {
    "open_meteo_forward_raw_manifest_v1": "open_meteo_forward_raw_manifest_v1.csv",
    "open_meteo_forward_provider_features_v1": (
        "open_meteo_forward_provider_features_v1.parquet"
    ),
    "open_meteo_forward_maturity_audit_v1": "open_meteo_forward_maturity_audit_v1.csv",
    "open_meteo_forward_causality_audit_v1": "open_meteo_forward_causality_audit_v1.csv",
    "open_meteo_forward_availability_audit_v1": (
        "open_meteo_forward_availability_audit_v1.csv"
    ),
    "open_meteo_forward_duplicate_key_report_v1": (
        "open_meteo_forward_duplicate_key_report_v1.csv"
    ),
}

COLLECTION_KEY_COLUMNS = [
    "target_date_local",
    "cp",
    "endpoint",
    "model",
    "run_time_utc",
]

PROVIDER_FAMILIES = {
    "gfs_seamless": "NOAA_GFS",
    "ecmwf_ifs025": "ECMWF_IFS",
    "ecmwf_aifs025_single": "ECMWF_AIFS",
    "icon_seamless": "DWD_ICON",
    "gem_global": "ECCC_GEM",
    "jma_seamless": "JMA_GSM",
}


@dataclass(frozen=True)
class ForwardCollectionArtifacts:
    raw_manifest_path: Path
    provider_features_path: Path
    maturity_audit_path: Path
    causality_audit_path: Path
    availability_audit_path: Path
    duplicate_key_report_path: Path
    report_path: Path
    raw_response_path: Path


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(response: dict[str, object]) -> str:
    return json.dumps(response, sort_keys=True, separators=(",", ":"))


def _parse_date(value: str | dt.date) -> dt.date:
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    return dt.date.fromisoformat(str(value))


def _parse_utc(value: object) -> dt.datetime:
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def _format_utc(value: dt.datetime) -> str:
    return value.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def _cp_utc(target_date_local: str | dt.date, cp: str) -> dt.datetime:
    hour, minute = [int(part) for part in str(cp).split(":", maxsplit=1)]
    local = dt.datetime.combine(
        _parse_date(target_date_local),
        dt.time(hour, minute),
        ZoneInfo(TZ_NAME),
    )
    return local.astimezone(dt.UTC)


def _valid_time_utc(time_value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(str(time_value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(TZ_NAME))
    return parsed.astimezone(dt.UTC)


def _provider_family(model: str) -> str:
    return PROVIDER_FAMILIES.get(model, model)


def _collection_key_hash(
    *,
    target_date_local: str,
    cp: str,
    endpoint: str,
    model: str,
    run_time_utc: str,
) -> str:
    return _sha256_text("|".join([target_date_local, cp, endpoint, model, run_time_utc]))


def validate_new_collection_key(
    *,
    existing_manifest: pl.DataFrame | None,
    target_date_local: str,
    cp: str,
    endpoint: str,
    model: str,
    run_time_utc: str,
) -> None:
    if existing_manifest is None or existing_manifest.is_empty():
        return
    missing = [column for column in COLLECTION_KEY_COLUMNS if column not in existing_manifest.columns]
    if missing:
        raise ValueError(f"missing collection key columns: {missing}")
    duplicate = existing_manifest.filter(
        (pl.col("target_date_local").cast(pl.Utf8) == str(target_date_local))
        & (pl.col("cp").cast(pl.Utf8) == str(cp))
        & (pl.col("endpoint").cast(pl.Utf8) == str(endpoint))
        & (pl.col("model").cast(pl.Utf8) == str(model))
        & (pl.col("run_time_utc").cast(pl.Utf8) == str(run_time_utc))
    )
    if duplicate.height:
        raise ValueError(
            "duplicate collection key: "
            f"{target_date_local}|{cp}|{endpoint}|{model}|{run_time_utc}"
        )


def _settled_lookup(settled_labels: pl.DataFrame) -> dict[str, dict[str, object]]:
    if settled_labels.is_empty() or "target_date_local" not in settled_labels.columns:
        return {}
    return {str(row["target_date_local"]): row for row in settled_labels.iter_rows(named=True)}


def build_forward_provider_features(
    *,
    target_date_local: str,
    cp: str,
    endpoint: str,
    model: str,
    run_time_utc: str,
    available_time_utc: str,
    retrieved_at_utc: str,
    response: dict[str, object],
    settled_labels: pl.DataFrame,
    request_url: str = "",
) -> pl.DataFrame:
    target = str(target_date_local)
    cp_time_utc = _cp_utc(target, cp)
    run_time = _parse_utc(run_time_utc)
    available_time = _parse_utc(available_time_utc)
    retrieved_at = _parse_utc(retrieved_at_utc)
    response_sha = _sha256_text(_canonical_json(response))
    request_url_sha = _sha256_text(request_url)
    key_hash = _collection_key_hash(
        target_date_local=target,
        cp=cp,
        endpoint=endpoint,
        model=model,
        run_time_utc=run_time_utc,
    )
    label = _settled_lookup(settled_labels).get(target)
    label_settled_at = label.get("label_settled_at_utc") if label else None
    label_source = label.get("label_source") if label else None

    hourly = response.get("hourly")
    if not isinstance(hourly, dict) or "time" not in hourly:
        return pl.DataFrame()
    times = list(hourly["time"])  # type: ignore[index]
    rows: list[dict[str, object]] = []
    for variable, values in hourly.items():
        if variable == "time":
            continue
        for index, value in enumerate(values):  # type: ignore[union-attr]
            valid_time = _valid_time_utc(str(times[index]))
            if available_time > cp_time_utc:
                row_status = "blocked_by_causality"
            elif label_settled_at is None:
                row_status = "pending"
            else:
                row_status = "mature"
            rows.append(
                {
                    "target_date_local": target,
                    "cp": cp,
                    "cp_utc": _format_utc(cp_time_utc),
                    "endpoint": endpoint,
                    "model": model,
                    "provider_family": _provider_family(model),
                    "run_time_utc": _format_utc(run_time),
                    "available_time_utc": _format_utc(available_time),
                    "retrieved_at_utc": _format_utc(retrieved_at),
                    "valid_time_utc": _format_utc(valid_time),
                    "horizon_hours": round(
                        (valid_time - run_time).total_seconds() / 3600.0
                    ),
                    "variable": str(variable),
                    "feature_name": f"{model}_{variable}_forward",
                    "feature_value": float(value),
                    "collection_key_sha256": key_hash,
                    "request_url_sha256": request_url_sha,
                    "response_sha256": response_sha,
                    "row_status": row_status,
                    "duplicate_key_status": "unique",
                    "availability_status": "usable"
                    if row_status != "blocked_by_causality"
                    else "blocked",
                    "label_settled_at_utc": label_settled_at,
                    "label_source": label_source,
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def apply_forward_row_maturity(rows: pl.DataFrame, settled_labels: pl.DataFrame) -> pl.DataFrame:
    if rows.is_empty():
        return rows
    labels = _settled_lookup(settled_labels)
    output = []
    for row in rows.iter_rows(named=True):
        label = labels.get(str(row["target_date_local"]))
        if (
            row.get("row_status") == "pending"
            and label is not None
            and _parse_utc(row["available_time_utc"]) <= _parse_utc(row["cp_utc"])
        ):
            row["row_status"] = "mature"
            row["label_settled_at_utc"] = label.get("label_settled_at_utc")
            row["label_source"] = label.get("label_source")
        output.append(row)
    return pl.DataFrame(output, strict=False)


def _exclusion_reason(row: dict[str, object]) -> str | None:
    if row.get("row_status") != "mature":
        return str(row.get("row_status") or "not_mature")
    if row.get("production_status") != PRODUCTION_STATUS:
        return "not_experiment_only"
    if _parse_utc(row["available_time_utc"]) > _parse_utc(row["cp_utc"]):
        return "blocked_by_causality"
    if row.get("duplicate_key_status") == "duplicate":
        return "duplicate"
    if row.get("availability_status") != "usable":
        return "blocked_by_availability"
    return None


def filter_forward_rows_for_nested_validation(
    rows: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    if rows.is_empty():
        return rows, pl.DataFrame()
    eligible: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for row in rows.iter_rows(named=True):
        reason = _exclusion_reason(row)
        if reason is None:
            eligible.append(row)
        else:
            excluded.append(
                {
                    "target_date_local": row.get("target_date_local"),
                    "cp": row.get("cp"),
                    "model": row.get("model"),
                    "row_status": row.get("row_status"),
                    "exclusion_reason": reason,
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(eligible, strict=False), pl.DataFrame(excluded, strict=False)


def build_forward_availability_audit(rows: pl.DataFrame) -> pl.DataFrame:
    if rows.is_empty():
        return pl.DataFrame()
    frame = rows.with_columns(
        pl.col("target_date_local").cast(pl.Utf8).str.slice(0, 4).alias("target_year"),
        pl.col("target_date_local").cast(pl.Utf8).str.slice(5, 2).alias("target_month"),
    )
    group_cols = [
        "endpoint",
        "model",
        "horizon_hours",
        "variable",
        "cp",
        "target_year",
        "target_month",
        "row_status",
    ]
    return (
        frame.group_by(group_cols, maintain_order=True)
        .agg(
            pl.len().alias("requested_rows"),
            (pl.col("row_status") == "mature").sum().alias("usable_rows"),
            (pl.col("row_status") == "pending").sum().alias("pending_rows"),
            (pl.col("row_status").str.starts_with("blocked")).sum().alias("blocked_rows"),
        )
        .with_columns(
            (
                pl.col("usable_rows").cast(pl.Float64)
                * 100.0
                / pl.col("requested_rows").cast(pl.Float64)
            ).alias("coverage_pct"),
            pl.when(pl.col("blocked_rows") > 0)
            .then(pl.col("row_status"))
            .otherwise(pl.lit(None))
            .alias("blocker"),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .sort(group_cols)
    )


def _maturity_audit(rows: pl.DataFrame) -> pl.DataFrame:
    if rows.is_empty():
        return pl.DataFrame()
    return rows.group_by("row_status", maintain_order=True).agg(pl.len().alias("n_rows")).with_columns(
        pl.lit(PRODUCTION_STATUS).alias("production_status")
    )


def _causality_audit(rows: pl.DataFrame) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "target_date_local": row["target_date_local"],
                "cp": row["cp"],
                "model": row["model"],
                "available_time_utc": row["available_time_utc"],
                "cp_utc": row["cp_utc"],
                "causality_status": "pass"
                if _parse_utc(row["available_time_utc"]) <= _parse_utc(row["cp_utc"])
                else "blocked_by_causality",
                "production_status": PRODUCTION_STATUS,
            }
            for row in rows.iter_rows(named=True)
        ],
        strict=False,
    )


def _duplicate_key_report(rows: pl.DataFrame) -> pl.DataFrame:
    if rows.is_empty():
        return pl.DataFrame()
    return rows.group_by(COLLECTION_KEY_COLUMNS, maintain_order=True).agg(pl.len().alias("n_rows")).with_columns(
        pl.when(pl.col("n_rows") > 1)
        .then(pl.lit("duplicate"))
        .otherwise(pl.lit("unique"))
        .alias("duplicate_key_status"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )


def _markdown_table(frame: pl.DataFrame, max_rows: int = 20) -> str:
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


def render_forward_collection_report(
    *,
    raw_manifest: pl.DataFrame,
    normalized_rows: pl.DataFrame,
    availability_audit: pl.DataFrame,
) -> str:
    status_counts = (
        normalized_rows.group_by("row_status").agg(pl.len().alias("n_rows"))
        if not normalized_rows.is_empty()
        else pl.DataFrame()
    )
    return "\n\n".join(
        [
            "# Open-Meteo OM-M14 Forward Collection Report",
            f"production_status: {PRODUCTION_STATUS}",
            "No production, EV, pricing, shadow trading, or execution work is unlocked.",
            f"raw_manifest_rows: {raw_manifest.height}",
            f"normalized_feature_rows: {normalized_rows.height}",
            "## Row Status",
            _markdown_table(status_counts),
            "## Availability Audit",
            _markdown_table(availability_audit, max_rows=40),
        ]
    ) + "\n"


def write_forward_collection_artifacts(
    *,
    output_dir: Path,
    collection_request: dict[str, object],
    response_text: str,
    normalized_rows: pl.DataFrame,
) -> ForwardCollectionArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    response_sha = _sha256_text(response_text)
    request_url = str(collection_request.get("request_url", ""))
    request_url_sha = _sha256_text(request_url)
    raw_response_path = raw_dir / f"{response_sha}.json"
    raw_response_path.write_text(response_text, encoding="utf-8")
    normalized = normalized_rows.with_columns(
        pl.lit(response_sha).alias("response_sha256"),
        pl.lit(request_url_sha).alias("request_url_sha256"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )
    raw_manifest = pl.DataFrame(
        [
            {
                **collection_request,
                "request_url_sha256": request_url_sha,
                "response_sha256": response_sha,
                "raw_response_path": str(raw_response_path),
                "collector_version": "om_m14_v1",
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
    availability_audit = build_forward_availability_audit(normalized)

    raw_manifest_path = output_dir / OPEN_METEO_FORWARD_COLLECTION_FILENAMES["open_meteo_forward_raw_manifest_v1"]
    provider_features_path = output_dir / OPEN_METEO_FORWARD_COLLECTION_FILENAMES["open_meteo_forward_provider_features_v1"]
    maturity_audit_path = output_dir / OPEN_METEO_FORWARD_COLLECTION_FILENAMES["open_meteo_forward_maturity_audit_v1"]
    causality_audit_path = output_dir / OPEN_METEO_FORWARD_COLLECTION_FILENAMES["open_meteo_forward_causality_audit_v1"]
    availability_audit_path = output_dir / OPEN_METEO_FORWARD_COLLECTION_FILENAMES["open_meteo_forward_availability_audit_v1"]
    duplicate_key_report_path = output_dir / OPEN_METEO_FORWARD_COLLECTION_FILENAMES["open_meteo_forward_duplicate_key_report_v1"]
    report_path = output_dir / "open_meteo_forward_collection_report_v1.md"

    raw_manifest.write_csv(raw_manifest_path)
    normalized.write_parquet(provider_features_path)
    _maturity_audit(normalized).write_csv(maturity_audit_path)
    _causality_audit(normalized).write_csv(causality_audit_path)
    availability_audit.write_csv(availability_audit_path)
    _duplicate_key_report(normalized).write_csv(duplicate_key_report_path)
    report_path.write_text(
        render_forward_collection_report(
            raw_manifest=raw_manifest,
            normalized_rows=normalized,
            availability_audit=availability_audit,
        ),
        encoding="utf-8",
    )

    return ForwardCollectionArtifacts(
        raw_manifest_path=raw_manifest_path,
        provider_features_path=provider_features_path,
        maturity_audit_path=maturity_audit_path,
        causality_audit_path=causality_audit_path,
        availability_audit_path=availability_audit_path,
        duplicate_key_report_path=duplicate_key_report_path,
        report_path=report_path,
        raw_response_path=raw_response_path,
    )
