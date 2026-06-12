# Open-Meteo Availability-First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an audit-only Open-Meteo availability and causality gate before any Open-Meteo forecast data is used as model features.

**Architecture:** Add a focused `solarstorm.open_meteo` package with a source registry, causal checkpoint/run eligibility helpers, bounded probe planning, injectable HTTP client, coverage summaries, decision logic, and artifact writers. Wire it into a Typer command named `open-meteo-availability-audit`; unit tests use fake probe responses and never hit the network.

**Tech Stack:** Python 3.12, Polars, Typer, pytest, standard-library `urllib.request` for the small runtime HTTP client, Ruff.

---

## Guardrails

- This step is audit-only and all outputs must include `production_status = EXPERIMENT_ONLY`.
- Do not create `data/open_meteo_features.parquet` in this step.
- Do not train, refit, compare, or promote a model with Open-Meteo inputs in this step.
- Historical Weather / reanalysis must be blocked from causal feature generation even when coverage is excellent.
- Historical Forecast must stay audit-only unless the audit proves CP-causal run/lead selection.
- Forecast API must be live/forward-collection only; it cannot reconstruct historical run snapshots by ordinary live calls.
- Previous Runs can be used for fixed-lead skill audit only.
- Single Runs is the preferred causal pilot source because it preserves run initialization, but short history must narrow the pilot window instead of silently changing the Onda 3H baseline.
- Unit tests must not hit the network. Live probes are explicit, bounded, and invoked only when `--live` is passed.

## File Structure

- Create `solarstorm/open_meteo/__init__.py`
  - Public exports for the availability audit package.
- Create `solarstorm/open_meteo/_availability.py`
  - Source taxonomy, source registry, CP UTC conversion, causal run eligibility, probe plan builder, fake-result compatible probe runner, coverage summaries, decision logic, report renderer, and artifact writer.
- Create `solarstorm/open_meteo/_client.py`
  - Minimal injectable Open-Meteo HTTP client using `urllib.request`, stable URL construction, and request/response SHA-256 hashes.
- Modify `solarstorm/__main__.py`
  - Add `open-meteo-availability-audit` CLI command.
- Create `tests/test_open_meteo_availability.py`
  - Unit tests for taxonomy, registry, CP UTC conversion, causal run eligibility, probe planning, coverage, decisions, report writing, and the no-features guard.
- Create `tests/test_open_meteo_client.py`
  - Unit tests for URL normalization and hashing without network.
- Create `tests/test_open_meteo_availability_cli.py`
  - CLI smoke tests using plan-only mode and fake inputs; no network.
- Generate `reports/open-meteo-availability/`
  - Audit artifacts only.
- Modify `ROADMAP.md`
  - Record that Open-Meteo integration is gated by availability/causality audit.
- Modify `CHANGELOG.md`
  - Record the new audit command and artifacts.

---

### Task 1: Source Taxonomy and Registry

**Files:**
- Create: `tests/test_open_meteo_availability.py`
- Create: `solarstorm/open_meteo/__init__.py`
- Create: `solarstorm/open_meteo/_availability.py`

- [ ] **Step 1: Write the failing source registry tests**

Add to `tests/test_open_meteo_availability.py`:

```python
from __future__ import annotations

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_blocked_source_register,
    build_source_registry_frame,
)


def test_source_registry_includes_all_open_meteo_source_classes():
    registry = build_source_registry_frame()

    assert registry.height == 5
    assert set(registry["causal_class"].to_list()) == {
        "live_seamless_forecast",
        "seamless_historical_forecast",
        "fixed_lead_forecast",
        "forecast_snapshot",
        "reanalysis_not_forecast",
    }
    assert set(registry["endpoint"].to_list()) == {
        "forecast",
        "historical_forecast",
        "previous_runs",
        "single_runs",
        "historical_weather",
    }
    assert set(registry["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_registry_blocks_reanalysis_and_non_snapshot_sources_from_causal_features():
    registry = build_source_registry_frame()
    blocked = build_blocked_source_register(registry)

    by_id = {row["source_id"]: row for row in blocked.iter_rows(named=True)}

    assert by_id["historical_weather_era5"]["causal_feature_allowed"] is False
    assert by_id["historical_weather_era5"]["blocked_reason"] == (
        "reanalysis_not_forecast"
    )
    assert by_id["forecast_api_best_match"]["causal_feature_allowed"] is False
    assert by_id["forecast_api_best_match"]["blocked_reason"] == (
        "live_seamless_no_historical_runs"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["causal_feature_allowed"] is True
    assert set(blocked["production_status"].to_list()) == {PRODUCTION_STATUS}
```

- [ ] **Step 2: Run the red registry tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_source_registry_includes_all_open_meteo_source_classes tests/test_open_meteo_availability.py::test_registry_blocks_reanalysis_and_non_snapshot_sources_from_causal_features -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'solarstorm.open_meteo'`.

- [ ] **Step 3: Create the package exports**

Create `solarstorm/open_meteo/__init__.py`:

```python
"""Open-Meteo availability and causality audit helpers."""

from __future__ import annotations

from solarstorm.open_meteo._availability import (
    PRODUCTION_STATUS,
    build_blocked_source_register,
    build_source_registry_frame,
)

__all__ = [
    "PRODUCTION_STATUS",
    "build_blocked_source_register",
    "build_source_registry_frame",
]
```

- [ ] **Step 4: Implement the minimal source registry**

Create `solarstorm/open_meteo/_availability.py`:

```python
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl

from solarstorm._config import ICAO, TZ_NAME

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
WELLINGTON_LATITUDE = -41.3272
WELLINGTON_LONGITUDE = 174.8053
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
    ),
    OpenMeteoSource(
        source_id="single_runs_ecmwf_ifs_hres",
        endpoint="single_runs",
        endpoint_url="https://api.open-meteo.com/v1/forecast",
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
```

- [ ] **Step 5: Verify the registry tests pass**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_source_registry_includes_all_open_meteo_source_classes tests/test_open_meteo_availability.py::test_registry_blocks_reanalysis_and_non_snapshot_sources_from_causal_features -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_availability.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Checkpoint UTC Conversion and Causal Run Eligibility

**Files:**
- Modify: `tests/test_open_meteo_availability.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/open_meteo/_availability.py`

- [ ] **Step 1: Write the failing causality tests**

Append to `tests/test_open_meteo_availability.py`:

```python
import datetime as dt

from solarstorm.open_meteo import cp_local_to_utc, select_latest_eligible_run


def test_cp_local_to_utc_respects_new_zealand_dst():
    summer = cp_local_to_utc(dt.date(2025, 1, 15), "23:00")
    winter = cp_local_to_utc(dt.date(2025, 7, 15), "23:00")

    assert summer == dt.datetime(2025, 1, 15, 10, 0, tzinfo=dt.UTC)
    assert winter == dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC)


def test_select_latest_eligible_run_blocks_runs_available_after_checkpoint():
    cp_utc = dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC)
    valid_time_utc = dt.datetime(2025, 7, 15, 12, 0, tzinfo=dt.UTC)

    selected = select_latest_eligible_run(
        cp_utc=cp_utc,
        valid_time_utc=valid_time_utc,
        candidate_run_times_utc=[
            dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC),
            dt.datetime(2025, 7, 15, 6, 0, tzinfo=dt.UTC),
        ],
        availability_lag_h=6,
        safety_margin_minutes=10,
    )

    assert selected is not None
    assert selected["selected_run_time_utc"] == "2025-07-15T00:00:00+00:00"
    assert selected["selected_available_time_utc"] == "2025-07-15T06:10:00+00:00"
    assert selected["selected_valid_time_utc"] == "2025-07-15T12:00:00+00:00"
    assert selected["selected_lead_h"] == 12


def test_select_latest_eligible_run_rejects_non_forecast_valid_time():
    cp_utc = dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC)

    selected = select_latest_eligible_run(
        cp_utc=cp_utc,
        valid_time_utc=dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC),
        candidate_run_times_utc=[dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC)],
        availability_lag_h=0,
        safety_margin_minutes=0,
    )

    assert selected is None
```

- [ ] **Step 2: Run the red causality tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_cp_local_to_utc_respects_new_zealand_dst tests/test_open_meteo_availability.py::test_select_latest_eligible_run_blocks_runs_available_after_checkpoint tests/test_open_meteo_availability.py::test_select_latest_eligible_run_rejects_non_forecast_valid_time -q
```

Expected: FAIL with import errors for the new functions.

- [ ] **Step 3: Export the causality helpers**

Update `solarstorm/open_meteo/__init__.py`:

```python
"""Open-Meteo availability and causality audit helpers."""

from __future__ import annotations

from solarstorm.open_meteo._availability import (
    PRODUCTION_STATUS,
    build_blocked_source_register,
    build_source_registry_frame,
    cp_local_to_utc,
    select_latest_eligible_run,
)

__all__ = [
    "PRODUCTION_STATUS",
    "build_blocked_source_register",
    "build_source_registry_frame",
    "cp_local_to_utc",
    "select_latest_eligible_run",
]
```

- [ ] **Step 4: Implement the causality helpers**

Add the import and append the helpers to `solarstorm/open_meteo/_availability.py`:

```python
from zoneinfo import ZoneInfo
```

```python
def _parse_cp_time(cp: str) -> dt.time:
    hour_text, minute_text = cp.split(":", maxsplit=1)
    return dt.time(int(hour_text), int(minute_text))


def cp_local_to_utc(
    date_local: dt.date,
    cp: str,
    *,
    tz_name: str = TZ_NAME,
) -> dt.datetime:
    local_dt = dt.datetime.combine(
        date_local,
        _parse_cp_time(cp),
        tzinfo=ZoneInfo(tz_name),
    )
    return local_dt.astimezone(dt.UTC)


def _iso(value: dt.datetime) -> str:
    return value.astimezone(dt.UTC).isoformat()


def select_latest_eligible_run(
    *,
    cp_utc: dt.datetime,
    valid_time_utc: dt.datetime,
    candidate_run_times_utc: list[dt.datetime],
    availability_lag_h: int,
    safety_margin_minutes: int,
) -> dict[str, object] | None:
    eligible: list[tuple[dt.datetime, dt.datetime]] = []
    cp_utc = cp_utc.astimezone(dt.UTC)
    valid_time_utc = valid_time_utc.astimezone(dt.UTC)
    for run_time in candidate_run_times_utc:
        run_time_utc = run_time.astimezone(dt.UTC)
        if valid_time_utc <= run_time_utc:
            continue
        available_time = run_time_utc + dt.timedelta(
            hours=availability_lag_h,
            minutes=safety_margin_minutes,
        )
        if available_time <= cp_utc:
            eligible.append((run_time_utc, available_time))

    if not eligible:
        return None

    selected_run_time, selected_available_time = max(eligible, key=lambda item: item[0])
    lead_hours = int((valid_time_utc - selected_run_time).total_seconds() // 3600)
    return {
        "selected_run_time_utc": _iso(selected_run_time),
        "selected_available_time_utc": _iso(selected_available_time),
        "selected_valid_time_utc": _iso(valid_time_utc),
        "selected_lead_h": lead_hours,
        "cp_utc": _iso(cp_utc),
    }
```

- [ ] **Step 5: Verify causality tests pass**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_cp_local_to_utc_respects_new_zealand_dst tests/test_open_meteo_availability.py::test_select_latest_eligible_run_blocks_runs_available_after_checkpoint tests/test_open_meteo_availability.py::test_select_latest_eligible_run_rejects_non_forecast_valid_time -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_availability.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: HTTP Client and Bounded Probe Plan

**Files:**
- Create: `tests/test_open_meteo_client.py`
- Modify: `tests/test_open_meteo_availability.py`
- Create: `solarstorm/open_meteo/_client.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/open_meteo/_availability.py`

- [ ] **Step 1: Write the failing client tests**

Create `tests/test_open_meteo_client.py`:

```python
from __future__ import annotations

from solarstorm.open_meteo._client import (
    OpenMeteoResponse,
    build_request_url,
    hash_text,
)


def test_build_request_url_is_stable_and_sorted():
    url = build_request_url(
        "https://example.test/forecast",
        {"longitude": 174.8053, "latitude": -41.3272, "hourly": "temperature_2m"},
    )

    assert url == (
        "https://example.test/forecast?"
        "hourly=temperature_2m&latitude=-41.3272&longitude=174.8053"
    )


def test_open_meteo_response_hashes_request_and_body():
    response = OpenMeteoResponse.from_text(
        request_url="https://example.test/forecast?latitude=-41.3272",
        status_code=200,
        text='{"hourly":{"temperature_2m":[12.3]}}',
    )

    assert response.ok is True
    assert response.request_url_sha256 == hash_text(response.request_url)
    assert response.response_sha256 == hash_text(response.text)
```

- [ ] **Step 2: Run the red client tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_client.py -q
```

Expected: FAIL because `solarstorm.open_meteo._client` does not exist.

- [ ] **Step 3: Implement the client without adding runtime dependencies**

Create `solarstorm/open_meteo/_client.py`:

```python
from __future__ import annotations

import hashlib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_request_url(base_url: str, params: dict[str, Any]) -> str:
    pairs = []
    for key in sorted(params):
        value = params[key]
        if value is None:
            continue
        pairs.append((key, str(value)))
    return f"{base_url}?{urllib.parse.urlencode(pairs)}"


@dataclass(frozen=True)
class OpenMeteoResponse:
    request_url: str
    status_code: int
    text: str
    request_url_sha256: str
    response_sha256: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @classmethod
    def from_text(
        cls,
        *,
        request_url: str,
        status_code: int,
        text: str,
    ) -> "OpenMeteoResponse":
        return cls(
            request_url=request_url,
            status_code=status_code,
            text=text,
            request_url_sha256=hash_text(request_url),
            response_sha256=hash_text(text),
        )


class OpenMeteoClient:
    def __init__(self, *, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def get(self, base_url: str, params: dict[str, Any]) -> OpenMeteoResponse:
        request_url = build_request_url(base_url, params)
        request = urllib.request.Request(
            request_url,
            headers={"User-Agent": "solarstorm-open-meteo-availability-audit/1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                status_code = int(response.status)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            status_code = int(exc.code)
        return OpenMeteoResponse.from_text(
            request_url=request_url,
            status_code=status_code,
            text=body,
        )
```

- [ ] **Step 4: Write the failing probe plan tests**

Append to `tests/test_open_meteo_availability.py`:

```python
import json

from solarstorm.open_meteo import build_probe_plan


def test_build_probe_plan_is_bounded_and_excludes_live_forecast_by_default():
    registry = build_source_registry_frame()

    plan = build_probe_plan(
        registry,
        years=[2024],
        cps=["20:00", "23:00"],
        month_days=[(1, 15), (7, 15)],
    )

    assert "forecast_api_best_match" not in set(plan["source_id"].to_list())
    assert plan.height > 0
    assert plan["probe_id"].n_unique() == plan.height
    assert set(plan["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert set(plan["cp"].to_list()) == {"20:00", "23:00"}
    assert set(plan["date_local"].dt.year().to_list()) == {2024}

    single_rows = plan.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres")
    assert single_rows.height > 0
    params = json.loads(single_rows.row(0, named=True)["request_params_json"])
    assert params["latitude"] == -41.3272
    assert params["longitude"] == 174.8053
    assert params["hourly"] == ",".join(DEFAULT_VARIABLES_FOR_TEST)
```

At the top of `tests/test_open_meteo_availability.py`, add:

```python
import json

import polars as pl

DEFAULT_VARIABLES_FOR_TEST = (
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
```

- [ ] **Step 5: Run the red probe plan test**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_build_probe_plan_is_bounded_and_excludes_live_forecast_by_default -q
```

Expected: FAIL with import error for `build_probe_plan`.

- [ ] **Step 6: Export and implement bounded probe planning**

Update `solarstorm/open_meteo/__init__.py` to export `build_probe_plan`.

Add `import json` near the top of `solarstorm/open_meteo/_availability.py`, then
append:

```python
import json
```

```python
def _local_anchor_to_utc(date_local: dt.date, hour: int) -> dt.datetime:
    local_dt = dt.datetime.combine(
        date_local,
        dt.time(hour, 0),
        tzinfo=ZoneInfo(TZ_NAME),
    )
    return local_dt.astimezone(dt.UTC)


def _candidate_run_times_for_date(date_local: dt.date) -> list[dt.datetime]:
    start = dt.datetime.combine(
        date_local - dt.timedelta(days=1),
        dt.time(0, 0),
        tzinfo=dt.UTC,
    )
    return [start + dt.timedelta(hours=6 * offset) for offset in range(0, 9)]


def _source_request_params(
    row: dict[str, object],
    *,
    date_local: dt.date,
    selected_run: dict[str, object] | None,
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
        params["run"] = str(selected_run["selected_run_time_utc"]).replace(
            "+00:00",
            "Z",
        )
    if endpoint == "previous_runs":
        params["previous_days"] = 1
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
                    target_valid_time = _local_anchor_to_utc(date_local, 23)
                    selected_run = None
                    if source["causal_class"] == "forecast_snapshot":
                        selected_run = select_latest_eligible_run(
                            cp_utc=cp_utc,
                            valid_time_utc=target_valid_time,
                            candidate_run_times_utc=_candidate_run_times_for_date(
                                date_local
                            ),
                            availability_lag_h=6,
                            safety_margin_minutes=10,
                        )
                        if selected_run is None:
                            continue
                    params = _source_request_params(
                        source,
                        date_local=date_local,
                        selected_run=selected_run,
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
                            "cp_utc": _iso(cp_utc),
                            "target_valid_time_utc": _iso(target_valid_time),
                            "selected_run_time_utc": (
                                selected_run["selected_run_time_utc"]
                                if selected_run
                                else None
                            ),
                            "selected_available_time_utc": (
                                selected_run["selected_available_time_utc"]
                                if selected_run
                                else None
                            ),
                            "selected_lead_h": (
                                selected_run["selected_lead_h"]
                                if selected_run
                                else None
                            ),
                            "causal_class": source["causal_class"],
                            "request_params_json": json.dumps(
                                params,
                                sort_keys=True,
                            ),
                            "production_status": PRODUCTION_STATUS,
                        }
                    )
    return pl.DataFrame(rows)
```

- [ ] **Step 7: Verify client and probe plan tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_client.py tests/test_open_meteo_availability.py::test_build_probe_plan_is_bounded_and_excludes_live_forecast_by_default -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_client.py tests/test_open_meteo_availability.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 4: Fake-Compatible Probe Runner, Coverage, and Decisions

**Files:**
- Modify: `tests/test_open_meteo_availability.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/open_meteo/_availability.py`

- [ ] **Step 1: Write failing tests for probe runner and decisions**

Append to `tests/test_open_meteo_availability.py`:

```python
from solarstorm.open_meteo import (
    build_availability_summaries,
    build_decision_update,
    run_probe_plan,
)
from solarstorm.open_meteo._client import OpenMeteoResponse


class FakeOpenMeteoClient:
    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        text = json.dumps(
            {
                "hourly": {
                    "time": ["2024-07-15T23:00"],
                    "temperature_2m": [12.4],
                }
            }
        )
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?fake=1",
            status_code=200,
            text=text,
        )


def test_run_probe_plan_records_hashes_and_success_without_network():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )

    results = run_probe_plan(plan, client=FakeOpenMeteoClient(), live=True)

    assert results.height == 1
    row = results.row(0, named=True)
    assert row["success"] is True
    assert row["status_code"] == 200
    assert row["n_hourly_times"] == 1
    assert len(row["request_url_sha256"]) == 64
    assert len(row["response_sha256"]) == 64
    assert row["production_status"] == PRODUCTION_STATUS


def test_run_probe_plan_plan_only_does_not_call_client():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "historical_weather_era5"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )

    results = run_probe_plan(plan, client=None, live=False)

    assert results.height == plan.height
    assert set(results["success"].to_list()) == {False}
    assert set(results["error"].to_list()) == {"plan_only_not_requested"}


def test_decisions_keep_historical_weather_blocked_and_narrow_single_runs_pilot():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(
            pl.col("source_id").is_in(
                ["single_runs_ecmwf_ifs_hres", "historical_weather_era5"]
            )
        ),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=FakeOpenMeteoClient(), live=True)

    summaries = build_availability_summaries(registry, plan, results)
    decision = build_decision_update(summaries["availability_by_source"])

    by_id = {row["source_id"]: row for row in decision.iter_rows(named=True)}

    assert by_id["single_runs_ecmwf_ifs_hres"]["decision_status"] == (
        "OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["pilot_scope_note"] == (
        "narrow_to_available_window"
    )
    assert by_id["historical_weather_era5"]["decision_status"] == (
        "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA"
    )
    assert by_id["historical_weather_era5"]["pilot_scope_note"] == (
        "diagnostic_only_reanalysis"
    )
    assert set(decision["production_status"].to_list()) == {PRODUCTION_STATUS}
```

- [ ] **Step 2: Run the red probe runner tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_run_probe_plan_records_hashes_and_success_without_network tests/test_open_meteo_availability.py::test_run_probe_plan_plan_only_does_not_call_client tests/test_open_meteo_availability.py::test_decisions_keep_historical_weather_blocked_and_narrow_single_runs_pilot -q
```

Expected: FAIL with import errors for `run_probe_plan`, `build_availability_summaries`, and `build_decision_update`.

- [ ] **Step 3: Export the probe runner and decision helpers**

Update `solarstorm/open_meteo/__init__.py` to export:

```python
build_availability_summaries
build_decision_update
run_probe_plan
```

- [ ] **Step 4: Implement fake-compatible probe runner and summaries**

Append to `solarstorm/open_meteo/_availability.py`:

```python
def _safe_json_loads(text: str) -> dict[str, object]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


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
                    "request_url_sha256": None,
                    "response_sha256": None,
                    "error": "plan_only_not_requested",
                    "production_status": PRODUCTION_STATUS,
                }
            )
            continue
        if client is None:
            raise ValueError("client is required when live=True")
        try:
            params = json.loads(str(probe["request_params_json"]))
            response = client.get(str(probe["endpoint_url"]), params)
            n_hourly_times = _hourly_count(response.text)
            rows.append(
                {
                    **base,
                    "success": bool(response.ok and n_hourly_times > 0),
                    "status_code": int(response.status_code),
                    "n_hourly_times": n_hourly_times,
                    "request_url_sha256": response.request_url_sha256,
                    "response_sha256": response.response_sha256,
                    "error": None if response.ok else f"http_{response.status_code}",
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
                    "request_url_sha256": None,
                    "response_sha256": None,
                    "error": type(exc).__name__,
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows)


def _coverage_by_source(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame()
    return (
        results.group_by(["source_id", "endpoint", "model", "causal_class"])
        .agg(
            pl.len().alias("n_probes"),
            pl.col("success").cast(pl.Int64).sum().alias("n_success"),
            pl.col("calendar_year").filter(pl.col("success")).n_unique().alias(
                "n_success_years"
            ),
            pl.col("selected_run_time_utc").is_not_null().any().alias(
                "has_run_metadata"
            ),
            pl.col("selected_lead_h").is_not_null().any().alias("has_lead_metadata"),
        )
        .with_columns(
            (pl.col("n_success") / pl.col("n_probes") * 100.0).alias(
                "success_pct"
            ),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .sort(["source_id"])
    )


def _coverage_by_year_month_cp(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame()
    return (
        results.group_by(
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
            (pl.col("n_success") / pl.col("n_probes") * 100.0).alias(
                "success_pct"
            ),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .sort(["source_id", "calendar_year", "month", "cp"])
    )


def _causal_selection_audit(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame()
    return results.select(
        [
            "probe_id",
            "source_id",
            "endpoint",
            "model",
            "date_local",
            "cp",
            "cp_utc",
            "target_valid_time_utc",
            "selected_run_time_utc",
            "selected_available_time_utc",
            "selected_lead_h",
            "causal_class",
            "success",
            "error",
            "production_status",
        ]
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
        "availability_by_source": _coverage_by_source(probe_results),
        "availability_by_year_month_cp": _coverage_by_year_month_cp(probe_results),
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
            note = (
                "full_nested_window_candidate"
                if n_success_years >= 2
                else "narrow_to_available_window"
            )
            return ("OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT", note)
        return (
            "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA",
            "missing_run_or_lead_metadata",
        )
    return ("OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA", "unknown_causal_class")


def build_decision_update(availability_by_source: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for row in availability_by_source.iter_rows(named=True):
        status, scope_note = _decision_for_source(row)
        rows.append(
            {
                "source_id": row["source_id"],
                "endpoint": row["endpoint"],
                "model": row["model"],
                "causal_class": row["causal_class"],
                "n_probes": row["n_probes"],
                "n_success": row["n_success"],
                "n_success_years": row["n_success_years"],
                "success_pct": row["success_pct"],
                "has_run_metadata": row["has_run_metadata"],
                "has_lead_metadata": row["has_lead_metadata"],
                "decision_status": status,
                "pilot_scope_note": scope_note,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows).sort("source_id")
```

- [ ] **Step 5: Verify probe runner and decision tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_run_probe_plan_records_hashes_and_success_without_network tests/test_open_meteo_availability.py::test_run_probe_plan_plan_only_does_not_call_client tests/test_open_meteo_availability.py::test_decisions_keep_historical_weather_blocked_and_narrow_single_runs_pilot -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_availability.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 5: Artifact Writer, Report, and No-Features Guard

**Files:**
- Modify: `tests/test_open_meteo_availability.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/open_meteo/_availability.py`

- [ ] **Step 1: Write failing artifact writer tests**

Append to `tests/test_open_meteo_availability.py`:

```python
from solarstorm.open_meteo import (
    OPEN_METEO_FILENAMES,
    assert_no_open_meteo_features_created,
    render_availability_report,
    write_open_meteo_availability_artifacts,
)


def test_artifact_writer_creates_audit_outputs_and_no_feature_file(tmp_path: Path):
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=FakeOpenMeteoClient(), live=True)
    summaries = build_availability_summaries(registry, plan, results)
    summaries["decision_update"] = build_decision_update(
        summaries["availability_by_source"]
    )

    paths = write_open_meteo_availability_artifacts(
        summaries,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    for artifact_key, filename in OPEN_METEO_FILENAMES.items():
        assert paths[artifact_key] == tmp_path / filename
        assert paths[artifact_key].exists()
    assert paths["availability_report_md"].exists()
    assert not (tmp_path / "open_meteo_features.parquet").exists()
    assert_no_open_meteo_features_created(tmp_path)

    report = paths["availability_report_md"].read_text(encoding="utf-8")
    assert "Historical Weather / reanalysis is blocked" in report
    assert "data/open_meteo_features.parquet was not created" in report
    assert "EXPERIMENT_ONLY" in report
```

At the top of `tests/test_open_meteo_availability.py`, add:

```python
from pathlib import Path
```

- [ ] **Step 2: Run the red artifact writer test**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_artifact_writer_creates_audit_outputs_and_no_feature_file -q
```

Expected: FAIL with import errors for writer/report helpers.

- [ ] **Step 3: Export artifact helpers**

Update `solarstorm/open_meteo/__init__.py` to export:

```python
OPEN_METEO_FILENAMES
assert_no_open_meteo_features_created
render_availability_report
write_open_meteo_availability_artifacts
```

- [ ] **Step 4: Implement artifact filenames, guard, report, and writer**

Append to `solarstorm/open_meteo/_availability.py`:

```python
OPEN_METEO_FILENAMES = {
    "source_registry": "open_meteo_source_registry_v1.csv",
    "probe_plan": "open_meteo_probe_plan_v1.csv",
    "probe_results": "open_meteo_probe_results_v1.csv",
    "availability_by_source": "open_meteo_availability_by_source_v1.csv",
    "availability_by_year_month_cp": (
        "open_meteo_availability_by_year_month_cp_v1.csv"
    ),
    "causal_selection_audit": "open_meteo_causal_selection_audit_v1.csv",
    "blocked_source_register": "open_meteo_blocked_source_register_v1.csv",
    "decision_update": "open_meteo_decision_update_v1.csv",
}


def assert_no_open_meteo_features_created(output_dir: Path) -> None:
    forbidden = output_dir / "open_meteo_features.parquet"
    if forbidden.exists():
        raise AssertionError(
            "Open-Meteo feature generation is blocked in the availability audit."
        )


def _markdown_table(frame: pl.DataFrame, columns: list[str], *, limit: int = 20) -> list[str]:
    if frame.is_empty():
        return ["No rows."]
    selected = frame.select([column for column in columns if column in frame.columns])
    lines = [
        "| " + " | ".join(selected.columns) + " |",
        "| " + " | ".join("---" for _ in selected.columns) + " |",
    ]
    for row in selected.head(limit).iter_rows(named=True):
        lines.append("| " + " | ".join(str(row[column]) for column in selected.columns) + " |")
    return lines


def render_availability_report(
    summaries: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    decision = summaries.get("decision_update", pl.DataFrame())
    availability = summaries.get("availability_by_source", pl.DataFrame())
    blocked = summaries.get("blocked_source_register", pl.DataFrame())

    lines = [
        f"# Open-Meteo Availability Audit - {today.isoformat()}",
        "",
        f"`production_status`: `{PRODUCTION_STATUS}`",
        "",
        "This is an audit-only artifact. Open-Meteo data is not integrated into model features in this step.",
        "",
        "Historical Weather / reanalysis is blocked from causal feature generation.",
        "Historical Forecast remains audit-only unless CP-causal run metadata is proven.",
        "Single Runs can narrow a pilot to its available history instead of changing the Onda 3H baseline.",
        "",
        "data/open_meteo_features.parquet was not created.",
        "",
        "## Decision Update",
        "",
        *_markdown_table(
            decision,
            [
                "source_id",
                "causal_class",
                "n_success_years",
                "decision_status",
                "pilot_scope_note",
                "production_status",
            ],
        ),
        "",
        "## Availability by Source",
        "",
        *_markdown_table(
            availability,
            [
                "source_id",
                "endpoint",
                "model",
                "n_probes",
                "n_success",
                "success_pct",
                "has_run_metadata",
                "has_lead_metadata",
                "production_status",
            ],
        ),
        "",
        "## Blocked Source Register",
        "",
        *_markdown_table(
            blocked,
            [
                "source_id",
                "causal_class",
                "causal_feature_allowed",
                "blocked_reason",
                "production_status",
            ],
        ),
    ]
    return "\n".join(lines) + "\n"


def write_open_meteo_availability_artifacts(
    summaries: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in OPEN_METEO_FILENAMES.items():
        frame = summaries[key]
        path = output_dir / filename
        frame.write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_availability_report_v1.md"
    report_path.write_text(
        render_availability_report(summaries, today=today),
        encoding="utf-8",
    )
    paths["availability_report_md"] = report_path
    assert_no_open_meteo_features_created(output_dir)
    return paths
```

- [ ] **Step 5: Verify artifact writer tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py::test_artifact_writer_creates_audit_outputs_and_no_feature_file -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_availability.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 6: CLI Command and Plan-Only Default

**Files:**
- Create: `tests/test_open_meteo_availability_cli.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_open_meteo_availability_cli.py`:

```python
from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_open_meteo_availability_audit_cli_plan_only_writes_artifacts(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-availability-audit",
            "--output-dir",
            str(tmp_path),
            "--years",
            "2024",
            "--cps",
            "23:00",
            "--month-days",
            "7-15",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo availability audit complete" in result.stdout
    assert "Plan-only mode; no network requests were made." in result.stdout
    assert "Open-Meteo model features were not created." in result.stdout

    expected = [
        "open_meteo_source_registry_v1.csv",
        "open_meteo_probe_plan_v1.csv",
        "open_meteo_probe_results_v1.csv",
        "open_meteo_availability_by_source_v1.csv",
        "open_meteo_availability_by_year_month_cp_v1.csv",
        "open_meteo_causal_selection_audit_v1.csv",
        "open_meteo_blocked_source_register_v1.csv",
        "open_meteo_decision_update_v1.csv",
        "open_meteo_availability_report_v1.md",
    ]
    for filename in expected:
        assert (tmp_path / filename).exists()

    decision = pl.read_csv(tmp_path / "open_meteo_decision_update_v1.csv")
    assert set(decision["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert not (tmp_path / "open_meteo_features.parquet").exists()


def test_open_meteo_availability_audit_cli_validates_month_days(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-availability-audit",
            "--output-dir",
            str(tmp_path),
            "--month-days",
            "bad-value",
        ],
    )

    assert result.exit_code == 2
    assert "invalid --month-days item" in result.stdout
```

- [ ] **Step 2: Run the red CLI tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability_cli.py -q
```

Expected: FAIL because the CLI command does not exist.

- [ ] **Step 3: Add imports to `solarstorm/__main__.py`**

Add near the other imports in `solarstorm/__main__.py`:

```python
from solarstorm.open_meteo import (
    build_availability_summaries,
    build_decision_update,
    build_probe_plan,
    build_source_registry_frame,
    run_probe_plan,
    write_open_meteo_availability_artifacts,
)
from solarstorm.open_meteo._client import OpenMeteoClient
```

- [ ] **Step 4: Add parse helpers in `solarstorm/__main__.py`**

Add above the Open-Meteo command:

```python
def _parse_csv_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_csv_strings(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_month_days(value: str) -> list[tuple[int, int]]:
    parsed: list[tuple[int, int]] = []
    for item in value.split(","):
        token = item.strip()
        if not token:
            continue
        pieces = token.split("-", maxsplit=1)
        if len(pieces) != 2:
            print(f"ERROR: invalid --month-days item: {token}")
            raise typer.Exit(2)
        try:
            month = int(pieces[0])
            day = int(pieces[1])
            dt.date(2024, month, day)
        except ValueError as exc:
            print(f"ERROR: invalid --month-days item: {token}")
            raise typer.Exit(2) from exc
        parsed.append((month, day))
    if not parsed:
        print("ERROR: --month-days produced no valid probes")
        raise typer.Exit(2)
    return parsed
```

- [ ] **Step 5: Add the CLI command**

Add to `solarstorm/__main__.py`:

```python
@app.command("open-meteo-availability-audit")
def open_meteo_availability_audit(
    output_dir: str = typer.Option("./reports/open-meteo-availability"),
    years: str = typer.Option("2022,2023,2024,2025"),
    cps: str = typer.Option("20:00,21:00,22:00,23:00"),
    month_days: str = typer.Option("1-15,4-15,7-15,10-15"),
    include_live_forecast: bool = typer.Option(False),
    live: bool = typer.Option(False, help="Make bounded live Open-Meteo requests."),
    timeout_seconds: int = typer.Option(20),
):
    """Write audit-only Open-Meteo availability and causality artifacts."""
    registry = build_source_registry_frame()
    probe_plan = build_probe_plan(
        registry,
        years=_parse_csv_ints(years),
        cps=_parse_csv_strings(cps),
        month_days=_parse_month_days(month_days),
        include_live_forecast=include_live_forecast,
    )
    client = OpenMeteoClient(timeout_seconds=timeout_seconds) if live else None
    probe_results = run_probe_plan(probe_plan, client=client, live=live)
    summaries = build_availability_summaries(registry, probe_plan, probe_results)
    summaries["decision_update"] = build_decision_update(
        summaries["availability_by_source"]
    )
    paths = write_open_meteo_availability_artifacts(
        summaries,
        output_dir=Path(output_dir),
        today=dt.date.today(),
    )
    print("Open-Meteo availability audit complete.")
    if live:
        print("Live bounded Open-Meteo probes were requested.")
    else:
        print("Plan-only mode; no network requests were made.")
    print("Open-Meteo model features were not created.")
    print(f"Report: {paths['availability_report_md']}")
```

- [ ] **Step 6: Verify the CLI tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability_cli.py -q
uv run ruff check solarstorm/__main__.py tests/test_open_meteo_availability_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 7: Documentation and Real Plan-Only Run

**Files:**
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Generate: `reports/open-meteo-availability/`

- [ ] **Step 1: Run the plan-only audit on the repo defaults**

Run:

```powershell
uv run tmax open-meteo-availability-audit --output-dir reports/open-meteo-availability
```

Expected:

```text
Open-Meteo availability audit complete.
Plan-only mode; no network requests were made.
Open-Meteo model features were not created.
Report: reports\open-meteo-availability\open_meteo_availability_report_v1.md
```

- [ ] **Step 2: Inspect generated decision artifacts**

Run:

```powershell
Get-ChildItem reports/open-meteo-availability
uv run python -c "import polars as pl; print(pl.read_csv('reports/open-meteo-availability/open_meteo_decision_update_v1.csv'))"
```

Expected:

- all nine audit artifacts exist;
- `open_meteo_features.parquet` does not exist;
- plan-only rows are availability-blocked except policy-blocked source classes.

- [ ] **Step 3: Update `ROADMAP.md`**

Add a short entry under the current Onda/Open-Meteo planning section:

```markdown
- Open-Meteo integration is gated by `open-meteo-availability-audit`.
  The first pass is audit-only: source taxonomy, historical availability,
  CP-causal run selection, blocked-source register, and decision artifact.
  No `data/open_meteo_features.parquet` is allowed until the decision artifact
  permits feature generation.
```

- [ ] **Step 4: Update `CHANGELOG.md`**

Add under the latest unreleased/current date section:

```markdown
- Added the Open-Meteo availability-first audit plan and CLI surface.
  The audit separates Forecast, Historical Forecast, Previous Runs,
  Single Runs, and Historical Weather sources; preserves `run_time_utc`,
  `valid_time_utc`, lead metadata where available; and keeps all outputs
  `EXPERIMENT_ONLY`.
```

- [ ] **Step 5: Verify docs and generated artifacts**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_availability_cli.py -q
uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_availability_cli.py
Test-Path reports/open-meteo-availability/open_meteo_features.parquet
```

Expected:

- pytest passes;
- Ruff reports `All checks passed!`;
- `Test-Path` prints `False`.

---

### Task 8: Optional Bounded Live Probe

**Files:**
- Generate: `reports/open-meteo-availability-live-smoke/`

- [ ] **Step 1: Run a deliberately tiny live smoke audit**

Run only after the unit/CLI suite passes:

```powershell
uv run tmax open-meteo-availability-audit --output-dir reports/open-meteo-availability-live-smoke --years 2024 --cps 23:00 --month-days 7-15 --live
```

Expected:

- command exits 0 if Open-Meteo is reachable;
- output says `Live bounded Open-Meteo probes were requested.`;
- `open_meteo_probe_results_v1.csv` contains request and response hashes;
- `open_meteo_features.parquet` does not exist.

- [ ] **Step 2: If the network call fails, keep the failure as audit evidence**

Run:

```powershell
uv run python -c "import polars as pl; df=pl.read_csv('reports/open-meteo-availability-live-smoke/open_meteo_probe_results_v1.csv'); print(df.select(['source_id','success','status_code','error']))"
```

Expected:

- if Open-Meteo responds, at least one source has `success = true`;
- if Open-Meteo is unavailable or rejects a model/endpoint parameter, the CSV records `success = false` and the concrete `error`;
- no test should be changed to require live network success.

---

## Final Verification

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_availability_cli.py -q
uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_availability_cli.py
Test-Path data/open_meteo_features.parquet
Test-Path reports/open-meteo-availability/open_meteo_features.parquet
```

Expected:

- pytest passes;
- Ruff reports `All checks passed!`;
- both `Test-Path` commands print `False`.

## Execution Notes

- Prefer `superpowers:subagent-driven-development` for implementation because Tasks 1-5 are independent enough for review checkpoints and small merges.
- Keep commits small: one commit per task after tests and Ruff pass.
- Do not change the Onda 3H nested-validation baseline in this plan.
- Do not infer production readiness from any Open-Meteo coverage result; the only allowed status in this phase is `EXPERIMENT_ONLY`.
