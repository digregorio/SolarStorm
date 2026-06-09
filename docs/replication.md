# Replication Guide - Adapting SolarStorm for Another City

This guide documents what needs to change to adapt SolarStorm from NZWN
(Wellington Airport) to another ICAO station. It assumes the new station has
IEM ASOS coverage and the forecasting target is the same: intraday Tmax for
daily maximum temperature markets.

## What Changes

### 1. Station Identity (`solarstorm/_config.py`)

```python
ICAO = "NZWN"                       # new station ICAO code
TZ_NAME = "Pacific/Auckland"        # IANA timezone for the station
CP_SET_UTC = ("20:00", "21:00", "22:00", "23:00")  # UTC checkpoints
TMP_C_INT_PLAUSIBILITY = (-10, 40)  # climate-appropriate bounds
SEED = 42                           # unchanged reproducibility seed
```

### 2. Checkpoint Times (`CP_SET_UTC`)

CP times are UTC hours, not local hours. For NZWN, 20:00-23:00 UTC maps to
local morning under NZST/NZDT. These are evaluation cutoffs, not claims about
the physical timing of Tmax.

### 3. Data Source (`solarstorm/data/_iem.py`)

The IEM ASOS API is called with `station=<ICAO>`. Verify the station exists in
the IEM network before running a backfill.

### 4. Climate Parameters

The old heuristic regime classifier in `solarstorm/eda/_regimes.py` is
superseded by the Onda 2R regime ontology repair plan. For a different station,
do not port the old 5-regime table directly. Rebuild causal physical regimes
from station data and keep late Tmax timing as a target/risk layer.

| Parameter | NZWN Baseline | Recalibration Method |
|-----------|---------------|---------------------|
| Causal physical regimes | Onda 2R model card | Morning METAR clustering plus physical audit |
| Late Tmax threshold | Train-only month/regime norm | `q90_train(tmax_hour | month, regime)` |
| Wind sectors | Wellington-specific | Local wind climatology with vector wind |
| Timing risk | Station-specific | Walk-forward calibrated event/risk model |

## What Does Not Change

These are invariant across stations:

| Component | Why Invariant |
|-----------|---------------|
| Causal firewall (`_contracts.py`) | `ts_utc < cp_utc` is logical, not meteorological |
| Integer settlement (`_settlement.py`) | Market contract standard |
| Frozen gates G1-G5 (`_gates.py`) | Statistical quality gates |
| Walk-forward design (`_walkforward.py`) | Evaluation methodology |
| Bootstrap CI (`_bootstrap.py`) | Statistical inference |
| Hypothesis framework (`_hypotheses.py`) | FDR plus gated testing |
| Commercial rounding | `floor(dec + 0.5)` is mathematical |

## Data Requirements

- Minimum 5 years of historical METAR data from IEM ASOS.
- At least 365 complete days for climatology fitting.
- At least 365 training days before the first walk-forward test split.

## Step-by-Step Adaptation

1. Fork or clone SolarStorm.
2. Update `solarstorm/_config.py` with new station constants.
3. Run `python -m solarstorm ingest` to backfill METAR.
4. Verify `data/labels.parquet` has enough complete days.
5. Run `python -m solarstorm leaderboard` to establish baselines.
6. Rebuild causal physical regimes by analyzing local climatology.
7. Run `python -m solarstorm features` and `python -m solarstorm validate`.
8. Run `python -m solarstorm robustness`.
9. Review reports for local performance and timing-risk failures.
