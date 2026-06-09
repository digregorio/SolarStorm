"""Onda 2E thesis atlas parsing and prerequisite EDA artifacts."""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import re
from pathlib import Path

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc

BLOCKED_EXTERNAL_IDS: frozenset[str] = frozenset(
    {
        "WCT-PRES-008",
        "WCT-GAP-024",
        "WCT-GAP-025",
        "WCT-GAP-031",
        "WCT-GAP-014",
        "WCT-GAP-047",
    }
)

DOMAIN_PRIORITY: dict[str, int] = {
    "REGIME": 1,
    "COOLING": 1,
    "WIND": 1,
    "TIMING": 1,
    "RAIN": 1,
    "PRES": 1,
    "FOEHN": 2,
    "CLOUD": 2,
    "HUM": 2,
    "SPIKE": 2,
    "CP": 2,
    "DQ": 2,
    "IX": 3,
    "GAP": 3,
}

DOMAIN_ORDER: dict[str, int] = {
    "REGIME": 1,
    "COOLING": 2,
    "WIND": 3,
    "FOEHN": 4,
    "RAIN": 5,
    "CLOUD": 6,
    "PRES": 7,
    "HUM": 8,
    "TIMING": 9,
    "SPIKE": 10,
    "CP": 11,
    "DQ": 12,
    "IX": 13,
    "GAP": 14,
}

_COOLING_FEATURE_ROW_NR = "_onda2e_cooling_feature_row_nr"


@dataclasses.dataclass
class _CoolingEventRowsCache:
    features: pl.DataFrame
    obs: pl.DataFrame
    tz_name: str
    rows: pl.DataFrame


_COOLING_EVENT_ROWS_CACHE: _CoolingEventRowsCache | None = None


@dataclasses.dataclass(frozen=True)
class Thesis:
    """Single thesis row from the official Onda 2E atlas."""

    id: str
    domain: str
    claim: str
    key_strata: str
    status: str
    source_section: str
    registry_complete: bool = True


def _split_md_table_row(line: str) -> list[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]

    parts: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(row):
        char = row[index]
        next_char = row[index + 1] if index + 1 < len(row) else ""
        if char == "\\" and next_char == "|":
            current.append("|")
            index += 2
            continue
        if char == "|":
            parts.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    parts.append("".join(current).strip())
    return parts


def parse_thesis_atlas(path: str | Path) -> list[Thesis]:
    """Parse the official markdown thesis atlas into a stable registry."""
    text = Path(path).read_text(encoding="utf-8")
    theses: dict[str, Thesis] = {}
    current_section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("### ") or line.startswith("## "):
            current_section = line.lstrip("#").strip()
            continue
        if not line.startswith("| WCT-"):
            continue

        parts = _split_md_table_row(line)
        if len(parts) < 4:
            continue
        thesis_id = parts[0]
        if not re.fullmatch(r"WCT-[A-Z]+-\d{3}", thesis_id):
            continue
        id_domain = thesis_id.split("-")[1]

        if len(parts) >= 5 and re.fullmatch(r"[A-Z]+", parts[1]):
            domain = parts[1]
            claim = parts[2]
            key_strata = parts[3]
            status = parts[4]
        else:
            domain = id_domain
            claim = parts[1]
            key_strata = parts[2]
            status = parts[3]

        theses.setdefault(
            thesis_id,
            Thesis(
                id=thesis_id,
                domain=domain,
                claim=claim,
                key_strata=key_strata,
                status=status,
                source_section=current_section,
            ),
        )
    for thesis_id in sorted(set(re.findall(r"WCT-[A-Z]+-\d{3}", text))):
        if thesis_id in theses:
            continue
        domain = thesis_id.split("-")[1]
        match = re.search(
            rf"{re.escape(thesis_id)}\s*[—-]\s*(.+?)(?:\*Test:|\n|$)",
            text,
            flags=re.S,
        )
        claim = (
            " ".join(match.group(1).split()).strip()
            if match
            else "Atlas v1 references this thesis outside the quick-reference registry."
        )
        theses[thesis_id] = Thesis(
            id=thesis_id,
            domain=domain,
            claim=claim,
            key_strata="registry detail outside quick-reference table",
            status="E0_candidate",
            source_section="Detailed Thesis Definitions",
            registry_complete=False,
        )
    # The official v1 atlas summary adopts 251 theses, including 20 IX theses,
    # but the current markdown body does not list the IX rows explicitly. Keep
    # the official scope and mark these as registry-detail gaps instead of
    # silently dropping them.
    if not any(key.startswith("WCT-IX-") for key in theses):
        for i in range(1, 21):
            thesis_id = f"WCT-IX-{i:03d}"
            theses[thesis_id] = Thesis(
                id=thesis_id,
                domain="IX",
                claim="Atlas v1 summary declares 20 IX interaction theses, but this thesis detail is missing from the markdown body.",
                key_strata="interaction gap",
                status="E0_candidate",
                source_section="Atlas Summary Statistics",
                registry_complete=False,
            )
    return sorted(
        theses.values(),
        key=lambda thesis: (
            DOMAIN_ORDER.get(thesis.domain, 99),
            thesis.id,
        ),
    )


def thesis_registry_frame(theses: list[Thesis]) -> pl.DataFrame:
    """Convert theses to a registry DataFrame."""
    return pl.DataFrame([dataclasses.asdict(thesis) for thesis in theses])


def _testability_for(thesis: Thesis) -> tuple[str, str]:
    if not thesis.registry_complete:
        return "registry_missing_detail", "Official atlas count includes this thesis, but markdown detail is missing."
    text = f"{thesis.claim} {thesis.key_strata}".lower()
    explicit_external = any(
        phrase in text
        for phrase in (
            "requires additional station data",
            "requires 2nd station",
            "requires enso",
            "requires sst",
            "requires radiosonde",
            "requires nwp",
            "requires external",
        )
    )
    if thesis.id in BLOCKED_EXTERNAL_IDS or explicit_external:
        return "blocked_external_data", "Requires data not currently in obs/labels/features."
    if thesis.domain in {"REGIME", "COOLING", "WIND", "TIMING", "RAIN", "PRES"}:
        return "priority_eda", "High-risk Onda 2E domain; run in first EDA wave."
    if thesis.domain == "GAP":
        return "gap_audit", "Gap thesis; use to drive prerequisite artifact coverage."
    return "available_eda", "Testable with current local artifacts or descriptive EDA."


def thesis_testability_audit(theses: list[Thesis]) -> pl.DataFrame:
    """Classify atlas theses by current testability and EDA priority."""
    rows = []
    for thesis in theses:
        testability, reason = _testability_for(thesis)
        rows.append(
            {
                **dataclasses.asdict(thesis),
                "priority": DOMAIN_PRIORITY.get(thesis.domain, 9),
                "testability": testability,
                "testability_reason": reason,
            }
        )
    return pl.DataFrame(rows)


def _with_month(df: pl.DataFrame) -> pl.DataFrame:
    if "month" in df.columns:
        return df
    return df.with_columns(pl.col("date_local").dt.month().alias("month"))


def _quantile_expr(col: str, q: float, name: str) -> pl.Expr:
    return pl.col(col).quantile(q, interpolation="nearest").alias(name)


def _join_feature_labels(features: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    joined = features.join(labels, on="date_local", how="inner")
    if "month" not in joined.columns:
        joined = joined.with_columns(pl.col("date_local").dt.month().alias("month"))
    return joined


def _with_remaining_warming(joined: pl.DataFrame) -> pl.DataFrame:
    values: list[int | None] = []
    for row in joined.iter_rows(named=True):
        cp_code = str(row["cp"]).replace(":", "")
        k_col = f"k_cp__cp_{cp_code}"
        k_value = row.get(k_col)
        tmax = row.get("tmax_int")
        values.append(int(tmax - k_value) if tmax is not None and k_value is not None else None)
    return joined.with_columns(pl.Series("remaining_warming", values, dtype=pl.Int64))


def _empty_monthly_wind_rose() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "month": pl.Int8,
            "cp": pl.Utf8,
            "wind_sector": pl.Utf8,
            "n_obs": pl.Int64,
            "n_days": pl.Int64,
            "total_obs": pl.Int64,
            "share": pl.Float64,
            "mean_sknt": pl.Float64,
        }
    )


def _empty_cooling_mechanism_taxonomy() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "month": pl.Int8,
            "regime_label": pl.Utf8,
            "cp": pl.Utf8,
            "cooling_mechanism": pl.Utf8,
            "n_rows": pl.Int64,
            "total_rows": pl.Int64,
            "share": pl.Float64,
            "underpowered_n_lt_30": pl.Boolean,
            "median_min_delta_t_per_h": pl.Float64,
            "median_cooling_hour": pl.Float64,
        }
    )


def _empty_cooling_event_rows() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            _COOLING_FEATURE_ROW_NR: pl.UInt32,
            "date_local": pl.Date,
            "month": pl.Int8,
            "cp": pl.Utf8,
            "regime_label": pl.Utf8,
            "cooling_mechanism": pl.Utf8,
            "min_delta_t_per_h": pl.Float64,
            "cooling_hour": pl.Int64,
            "n_pre_cp_obs": pl.Int64,
        }
    )


def _annotate_obs(obs: pl.DataFrame, tz_name: str) -> pl.DataFrame:
    if "ts_local" not in obs.columns:
        obs = obs.with_columns(pl.col("valid").dt.convert_time_zone(tz_name).alias("ts_local"))
    if "date_local" not in obs.columns:
        obs = obs.with_columns(pl.col("ts_local").dt.date().alias("date_local"))
    if "hour_local" not in obs.columns:
        obs = obs.with_columns(pl.col("ts_local").dt.hour().alias("hour_local"))
    if "wind_dir_deg" not in obs.columns and "drct" in obs.columns:
        obs = obs.with_columns(pl.col("drct").alias("wind_dir_deg"))
    return obs


def _obs_by_local_date(obs: pl.DataFrame, tz_name: str) -> dict[dt.date, pl.DataFrame]:
    annotated = (
        _annotate_obs(obs, tz_name)
        .filter(pl.col("dq_tmp_c_int") != "missing")
        .sort(["date_local", "valid"])
    )
    groups: dict[dt.date, pl.DataFrame] = {}
    for key, day_df in annotated.partition_by(
        "date_local",
        as_dict=True,
        maintain_order=True,
    ).items():
        date_key = key[0] if isinstance(key, tuple) else key
        groups[date_key] = day_df
    return groups


def _wind_sector(direction_deg: float | int | None) -> str:
    if direction_deg is None:
        return "unknown"
    deg = float(direction_deg) % 360.0
    sectors = (
        ("N", 337.5, 22.5),
        ("NE", 22.5, 67.5),
        ("E", 67.5, 112.5),
        ("SE", 112.5, 157.5),
        ("S", 157.5, 202.5),
        ("SW", 202.5, 247.5),
        ("W", 247.5, 292.5),
        ("NW", 292.5, 337.5),
    )
    for name, start, end in sectors:
        if start > end:
            if deg >= start or deg < end:
                return name
        elif start <= deg < end:
            return name
    return "unknown"


def _is_southerly(direction_deg: float | int | None) -> bool:
    if direction_deg is None:
        return False
    deg = float(direction_deg) % 360.0
    return 135.0 <= deg <= 225.0


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _feature_row_slice(
    row: dict,
    obs_by_date: dict[dt.date, pl.DataFrame],
    tz_name: str,
) -> pl.DataFrame | None:
    date_local = row["date_local"]
    day_df = obs_by_date.get(date_local)
    if day_df is None:
        return None
    cp_utc = cp_to_utc(date_local, str(row["cp"]), tz_name).astimezone(dt.UTC)
    return day_df.filter(pl.col("valid") < cp_utc)


def _build_monthly_wind_rose(
    features: pl.DataFrame,
    obs: pl.DataFrame | None,
    *,
    tz_name: str,
) -> pl.DataFrame:
    if obs is None or obs.height == 0 or features.height == 0:
        return _empty_monthly_wind_rose()

    obs_by_date = _obs_by_local_date(obs, tz_name)
    rows: list[dict] = []
    for feature_row in features.select(["date_local", "cp"]).iter_rows(named=True):
        slice_df = _feature_row_slice(feature_row, obs_by_date, tz_name)
        if slice_df is None or slice_df.height == 0:
            continue
        date_local = feature_row["date_local"]
        for obs_row in slice_df.select(["drct", "sknt"]).iter_rows(named=True):
            rows.append(
                {
                    "date_local": date_local,
                    "month": date_local.month,
                    "cp": str(feature_row["cp"]),
                    "wind_sector": _wind_sector(obs_row.get("drct")),
                    "sknt": _safe_float(obs_row.get("sknt")),
                }
            )

    if not rows:
        return _empty_monthly_wind_rose()

    wind = pl.DataFrame(rows, strict=False)
    counts = (
        wind.group_by(["month", "cp", "wind_sector"])
        .agg(
            pl.len().alias("n_obs"),
            pl.col("date_local").n_unique().alias("n_days"),
            pl.mean("sknt").alias("mean_sknt"),
        )
    )
    totals = wind.group_by(["month", "cp"]).len(name="total_obs")
    return (
        counts.join(totals, on=["month", "cp"])
        .with_columns((pl.col("n_obs") / pl.col("total_obs")).alias("share"))
        .select(["month", "cp", "wind_sector", "n_obs", "n_days", "total_obs", "share", "mean_sknt"])
        .sort(["month", "cp", "wind_sector"])
    )


def _classify_cooling_mechanism(slice_df: pl.DataFrame) -> dict:
    if slice_df.height < 2:
        return {
            "cooling_mechanism": "insufficient_obs",
            "min_delta_t_per_h": None,
            "cooling_hour": None,
        }

    obs = (
        slice_df.sort("valid")
        .with_columns(
            (
                pl.col("valid").diff().dt.total_minutes().cast(pl.Float64) / 60.0
            ).alias("delta_hours")
        )
        .with_columns(
            (
                pl.col("tmp_c_int").diff().cast(pl.Float64)
                / pl.col("delta_hours")
            ).alias("delta_t_per_h")
        )
    )
    deltas = obs.filter(
        (pl.col("delta_hours") > 0.0)
        & pl.col("delta_t_per_h").is_not_null()
        & pl.col("delta_t_per_h").is_finite()
    )
    if deltas.height == 0:
        return {
            "cooling_mechanism": "insufficient_obs",
            "min_delta_t_per_h": None,
            "cooling_hour": None,
        }

    min_idx = deltas["delta_t_per_h"].arg_min()
    event = deltas.row(min_idx, named=True)
    min_delta = _safe_float(event.get("delta_t_per_h"))
    cooling_hour = event.get("hour_local")
    cooling_hour_int = int(cooling_hour) if cooling_hour is not None else None
    wind_speed = _safe_float(event.get("sknt")) or 0.0
    wind_dir = event.get("drct")
    precip_sum = float(slice_df["p01i"].sum() or 0.0) if "p01i" in slice_df.columns else 0.0

    if min_delta is None or min_delta >= -2.0:
        mechanism = "no_material_cooling"
    elif precip_sum > 0.01:
        mechanism = "rain_evaporative_or_frontal"
    elif cooling_hour_int is not None and cooling_hour_int <= 6 and wind_speed < 8.0 and not _is_southerly(wind_dir):
        mechanism = "radiative_pre_dawn"
    elif _is_southerly(wind_dir) and wind_speed >= 12.0:
        mechanism = "southerly_frontal"
    elif cooling_hour_int is not None and cooling_hour_int >= 9:
        mechanism = "post_dawn_advective"
    else:
        mechanism = "ambiguous_cooling"

    return {
        "cooling_mechanism": mechanism,
        "min_delta_t_per_h": min_delta,
        "cooling_hour": cooling_hour_int,
    }


def _build_cooling_event_rows(
    features: pl.DataFrame,
    obs: pl.DataFrame | None,
    *,
    tz_name: str,
) -> pl.DataFrame:
    if obs is None or features.height == 0:
        return _empty_cooling_event_rows()

    obs_by_date = _obs_by_local_date(obs, tz_name) if obs.height else {}
    rows: list[dict] = []
    feature_rows = features.select(["date_local", "cp", "regime_label"]).with_row_index(
        _COOLING_FEATURE_ROW_NR
    )
    for feature_row in feature_rows.iter_rows(named=True):
        slice_df = _feature_row_slice(feature_row, obs_by_date, tz_name)
        date_local = feature_row["date_local"]
        if slice_df is None:
            mechanism = {
                "cooling_mechanism": "insufficient_obs",
                "min_delta_t_per_h": None,
                "cooling_hour": None,
            }
        else:
            mechanism = _classify_cooling_mechanism(slice_df)
        rows.append(
            {
                _COOLING_FEATURE_ROW_NR: feature_row[_COOLING_FEATURE_ROW_NR],
                "date_local": date_local,
                "month": date_local.month,
                "cp": str(feature_row["cp"]),
                "regime_label": str(feature_row.get("regime_label") or "unknown"),
                **mechanism,
                "n_pre_cp_obs": 0 if slice_df is None else slice_df.height,
            }
        )

    if not rows:
        return _empty_cooling_event_rows()
    return pl.DataFrame(rows, strict=False)


def _store_cooling_event_rows_cache(
    *,
    features: pl.DataFrame,
    obs: pl.DataFrame,
    tz_name: str,
    rows: pl.DataFrame,
) -> None:
    global _COOLING_EVENT_ROWS_CACHE
    _COOLING_EVENT_ROWS_CACHE = _CoolingEventRowsCache(
        features=features,
        obs=obs,
        tz_name=tz_name,
        rows=rows,
    )


def _cached_cooling_event_rows(
    features: pl.DataFrame,
    obs: pl.DataFrame,
    tz_name: str,
) -> pl.DataFrame | None:
    cache = _COOLING_EVENT_ROWS_CACHE
    if cache is None:
        return None
    if cache.features is not features or cache.obs is not obs or cache.tz_name != tz_name:
        return None
    return cache.rows


def _build_cooling_mechanism_taxonomy(
    features: pl.DataFrame,
    obs: pl.DataFrame | None,
    *,
    tz_name: str,
    cache_features: pl.DataFrame | None = None,
) -> pl.DataFrame:
    if obs is None or obs.height == 0 or features.height == 0:
        return _empty_cooling_mechanism_taxonomy()

    cooling = _build_cooling_event_rows(features, obs, tz_name=tz_name)
    if cache_features is not None:
        _store_cooling_event_rows_cache(
            features=cache_features,
            obs=obs,
            tz_name=tz_name,
            rows=cooling,
        )
    if cooling.height == 0:
        return _empty_cooling_mechanism_taxonomy()

    counts = (
        cooling.group_by(["month", "regime_label", "cp", "cooling_mechanism"])
        .agg(
            pl.len().alias("n_rows"),
            pl.median("min_delta_t_per_h").alias("median_min_delta_t_per_h"),
            pl.median("cooling_hour").alias("median_cooling_hour"),
        )
    )
    totals = cooling.group_by(["month", "regime_label", "cp"]).len(name="total_rows")
    return (
        counts.join(totals, on=["month", "regime_label", "cp"])
        .with_columns(
            (pl.col("n_rows") / pl.col("total_rows")).alias("share"),
            (pl.col("n_rows") < 30).alias("underpowered_n_lt_30"),
        )
        .select(
            [
                "month",
                "regime_label",
                "cp",
                "cooling_mechanism",
                "n_rows",
                "total_rows",
                "share",
                "underpowered_n_lt_30",
                "median_min_delta_t_per_h",
                "median_cooling_hour",
            ]
        )
        .sort(["month", "regime_label", "cp", "cooling_mechanism"])
    )


def build_prerequisite_artifacts(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    obs: pl.DataFrame | None = None,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    """Build mandatory prerequisite EDA tables from the official atlas."""
    features_m = _with_month(features)
    labels_m = _with_month(labels)
    joined = _join_feature_labels(features, labels)
    joined = _with_remaining_warming(joined)

    power_map = (
        features_m.group_by(["month", "regime_label", "cp"])
        .len(name="n_rows")
        .with_columns((pl.col("n_rows") < 30).alias("underpowered_n_lt_30"))
        .sort(["month", "regime_label", "cp"])
    )

    regime_frequency = (
        features_m.group_by(["month", "cp", "regime_label"])
        .len(name="n_rows")
        .join(
            features_m.group_by(["month", "cp"]).len(name="total_rows"),
            on=["month", "cp"],
        )
        .with_columns((pl.col("n_rows") / pl.col("total_rows")).alias("share"))
        .sort(["month", "cp", "regime_label"])
    )

    tmax_hour_distribution = (
        joined.group_by(["month", "regime_label"])
        .agg(
            pl.len().alias("n_rows"),
            _quantile_expr("tmax_hour", 0.10, "p10_tmax_hour"),
            _quantile_expr("tmax_hour", 0.25, "p25_tmax_hour"),
            _quantile_expr("tmax_hour", 0.50, "p50_tmax_hour"),
            _quantile_expr("tmax_hour", 0.75, "p75_tmax_hour"),
            _quantile_expr("tmax_hour", 0.90, "p90_tmax_hour"),
        )
        .sort(["month", "regime_label"])
    )

    remaining_warming_distribution = (
        joined.group_by(["month", "regime_label", "cp"])
        .agg(
            pl.len().alias("n_rows"),
            _quantile_expr("remaining_warming", 0.10, "p10_remaining_warming"),
            _quantile_expr("remaining_warming", 0.25, "p25_remaining_warming"),
            _quantile_expr("remaining_warming", 0.50, "p50_remaining_warming"),
            _quantile_expr("remaining_warming", 0.75, "p75_remaining_warming"),
            _quantile_expr("remaining_warming", 0.90, "p90_remaining_warming"),
        )
        .sort(["month", "regime_label", "cp"])
    )

    monthly_tmax = labels_m.group_by("month").agg(pl.mean("tmax_int").alias("month_mean_tmax"))
    tmax_anomaly_by_month = (
        labels_m.join(monthly_tmax, on="month")
        .with_columns((pl.col("tmax_int") - pl.col("month_mean_tmax")).alias("tmax_anomaly"))
        .group_by("month")
        .agg(
            pl.len().alias("n_days"),
            pl.mean("tmax_anomaly").alias("mean_tmax_anomaly"),
            _quantile_expr("tmax_anomaly", 0.05, "p05_tmax_anomaly"),
            _quantile_expr("tmax_anomaly", 0.25, "p25_tmax_anomaly"),
            _quantile_expr("tmax_anomaly", 0.50, "p50_tmax_anomaly"),
            _quantile_expr("tmax_anomaly", 0.75, "p75_tmax_anomaly"),
            _quantile_expr("tmax_anomaly", 0.95, "p95_tmax_anomaly"),
        )
        .sort("month")
    )

    return {
        "power_map": power_map,
        "regime_frequency": regime_frequency,
        "monthly_wind_rose": _build_monthly_wind_rose(features_m, obs, tz_name=tz_name),
        "tmax_hour_distribution": tmax_hour_distribution,
        "remaining_warming_distribution": remaining_warming_distribution,
        "cooling_mechanism_taxonomy": _build_cooling_mechanism_taxonomy(
            features_m,
            obs,
            tz_name=tz_name,
            cache_features=features,
        ),
        "tmax_anomaly_by_month": tmax_anomaly_by_month,
    }


def _write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def _artifact_summary_lines(artifacts: dict[str, pl.DataFrame]) -> list[str]:
    lines = ["| Artifact | Rows | Columns |", "|---|---:|---:|"]
    for name, frame in artifacts.items():
        lines.append(f"| `{name}` | {frame.height} | {len(frame.columns)} |")
    return lines


def _initial_findings_lines(testability: pl.DataFrame, artifacts: dict[str, pl.DataFrame]) -> list[str]:
    power_map = artifacts["power_map"]
    regime_frequency = artifacts["regime_frequency"]
    underpowered = power_map.filter(pl.col("underpowered_n_lt_30"))
    missing_detail = testability.filter(pl.col("testability") == "registry_missing_detail")
    blocked = testability.filter(pl.col("testability") == "blocked_external_data")
    regime_totals = (
        regime_frequency.group_by("regime_label")
        .agg(pl.sum("n_rows").alias("n_rows"))
        .sort("n_rows", descending=True)
    )
    lines = [
        "## Initial Findings",
        "",
        f"- Month x regime x CP cells audited: {power_map.height}.",
        f"- Underpowered cells (`n < 30`): {underpowered.height}.",
        f"- Registry-detail gaps in the official atlas: {missing_detail.height}.",
        f"- External-data blocked theses: {blocked.height}.",
        "",
        "### Regime Row Totals",
        "",
        "| Regime | Rows |",
        "|---|---:|",
    ]
    for row in regime_totals.iter_rows(named=True):
        lines.append(f"| {row['regime_label']} | {row['n_rows']} |")

    wind_rose = artifacts.get("monthly_wind_rose")
    if wind_rose is not None and wind_rose.height:
        wind_totals = (
            wind_rose.group_by("wind_sector")
            .agg(pl.sum("n_obs").alias("n_obs"))
            .sort("n_obs", descending=True)
        )
        lines += [
            "",
            "### Monthly Wind Rose Totals",
            "",
            "| Wind sector | Observations |",
            "|---|---:|",
        ]
        for row in wind_totals.iter_rows(named=True):
            lines.append(f"| {row['wind_sector']} | {row['n_obs']} |")

    cooling_taxonomy = artifacts.get("cooling_mechanism_taxonomy")
    if cooling_taxonomy is not None and cooling_taxonomy.height:
        cooling_totals = (
            cooling_taxonomy.group_by("cooling_mechanism")
            .agg(pl.sum("n_rows").alias("n_rows"))
            .sort("n_rows", descending=True)
        )
        lines += [
            "",
            "### Cooling Mechanism Taxonomy Totals",
            "",
            "| Cooling mechanism | Rows |",
            "|---|---:|",
        ]
        for row in cooling_totals.iter_rows(named=True):
            lines.append(f"| {row['cooling_mechanism']} | {row['n_rows']} |")

    if missing_detail.height:
        by_domain = missing_detail.group_by("domain").len(name="n").sort("domain")
        lines += [
            "",
            "### Registry Gaps",
            "",
            "| Domain | Missing thesis details |",
            "|---|---:|",
        ]
        for row in by_domain.iter_rows(named=True):
            lines.append(f"| {row['domain']} | {row['n']} |")

    return lines


def write_onda2e_artifacts(
    *,
    theses: list[Thesis],
    testability: pl.DataFrame,
    artifacts: dict[str, pl.DataFrame],
    output_dir: str | Path,
    source_atlas: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write Onda 2E registry, audit, prerequisite tables, and markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()

    registry = thesis_registry_frame(theses)
    paths: dict[str, Path] = {}
    paths["registry_csv"] = out_dir / "thesis_registry.csv"
    paths["testability_csv"] = out_dir / "thesis_testability_audit.csv"
    _write_csv(registry, paths["registry_csv"])
    _write_csv(testability, paths["testability_csv"])

    for name, frame in artifacts.items():
        path = out_dir / f"prereq_{name}.csv"
        _write_csv(frame, path)
        paths[f"prereq_{name}_csv"] = path

    domain_summary = (
        testability.group_by(["domain", "testability"])
        .len(name="n_theses")
        .sort(["domain", "testability"])
    )
    paths["domain_summary_csv"] = out_dir / "thesis_domain_summary.csv"
    _write_csv(domain_summary, paths["domain_summary_csv"])

    blocked = testability.filter(pl.col("testability") == "blocked_external_data")
    paths["blocked_json"] = out_dir / "blocked_external_data.json"
    paths["blocked_json"].write_text(
        json.dumps(blocked.to_dicts(), indent=2, default=str),
        encoding="utf-8",
    )

    report_path = out_dir / "onda2e_prerequisite_report.md"
    lines = [
        f"# Onda 2E Prerequisite EDA - {report_date.isoformat()}",
        "",
        f"Source atlas: `{Path(source_atlas).as_posix()}`",
        "",
        f"Theses parsed: {len(theses)}",
        f"Blocked external-data theses: {blocked.height}",
        "",
        "## Artifact Summary",
        "",
        *_artifact_summary_lines(artifacts),
        "",
        *_initial_findings_lines(testability, artifacts),
        "",
        "## Testability Summary",
        "",
        "| Domain | Testability | Theses |",
        "|---|---|---:|",
    ]
    for row in domain_summary.iter_rows(named=True):
        lines.append(f"| {row['domain']} | {row['testability']} | {row['n_theses']} |")

    lines += [
        "",
        "## Method Guardrail",
        "",
        "These artifacts are descriptive EDA prerequisites. They do not promote theses into features, change production regime labels, or relax Onda 4 gates.",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    paths["report_md"] = report_path
    return paths
