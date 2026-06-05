#!/usr/bin/env python3
"""Profile the live forecast pipeline stages.

This is a diagnostic script for Wave 4.1. It measures the concrete runtime of
the forecast inputs instead of relying on broad "the CLI is slow" guesses.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.baselines.climatology import fit_climatology
from core.baselines.empirical import fit_empirical_conditional
from core.contracts.station import load_station_config
from core.features.builder import build_cp_features, build_empirical_panel_fast
from core.features.training_panel import build_training_panel
from core.ingest.iem_csv import load_observations
from core.labels.tmax import build_tmax_labels


def _elapsed(t0: float) -> float:
    return round(perf_counter() - t0, 6)


def profile_pipeline(
    *,
    station_yaml: Path,
    csv: Path,
    target_date: date,
    cp: str,
    train_start: date,
    train_end: date | None = None,
    rich_panel_sample_days: int = 0,
) -> dict:
    """Profile forecast preprocessing and empirical fitting stages."""
    cfg = load_station_config(station_yaml)
    train_end_d = train_end or date.fromordinal(target_date.toordinal() - 1)
    timings: dict[str, float] = {}

    t = perf_counter()
    obs, stats = load_observations(
        csv,
        tmp_min_c=cfg.tmp_c_int_plausibility.min,
        tmp_max_c=cfg.tmp_c_int_plausibility.max,
    )
    timings["load_observations_s"] = _elapsed(t)

    t = perf_counter()
    labels = build_tmax_labels(obs, tz_name=cfg.tz, cp_set_utc=cfg.cp_set_utc)
    timings["build_tmax_labels_s"] = _elapsed(t)

    train_dates = [
        d for d in labels["date_local"].unique().to_list()
        if d is not None and train_start <= d <= train_end_d
    ]

    t = perf_counter()
    empirical_panel = build_empirical_panel_fast(
        obs,
        labels,
        tz_name=cfg.tz,
        cp_set=cfg.cp_set_utc,
        dates=train_dates,
    )
    timings["build_empirical_panel_fast_s"] = _elapsed(t)

    t = perf_counter()
    climo = fit_climatology(labels, train_start=train_start, train_end=train_end_d)
    timings["fit_climatology_s"] = _elapsed(t)

    t = perf_counter()
    fit_empirical_conditional(
        empirical_panel,
        train_window=(train_start, train_end_d),
    )
    timings["fit_empirical_conditional_s"] = _elapsed(t)

    t = perf_counter()
    feats = build_cp_features(
        obs,
        date_local=target_date,
        cp_hhmm=f"{int(cp):02d}:00",
        tz_name=cfg.tz,
        labels=labels,
    )
    timings["build_target_cp_features_s"] = _elapsed(t)

    rich_panel_profile: dict[str, object] = {
        "enabled": rich_panel_sample_days > 0,
        "sample_days": rich_panel_sample_days,
    }
    if rich_panel_sample_days > 0:
        sample_dates = train_dates[-rich_panel_sample_days:]
        t = perf_counter()
        rich_panel = build_training_panel(
            obs,
            labels,
            climo=climo,
            tz_name=cfg.tz,
            cp_set=[f"{int(cp):02d}:00"],
            dates=sample_dates,
        )
        rich_elapsed = _elapsed(t)
        timings["build_ridge_training_panel_sample_s"] = rich_elapsed
        per_day = rich_elapsed / len(sample_dates) if sample_dates else None
        rich_panel_profile.update({
            "sample_rows": rich_panel.height,
            "sample_days": len(sample_dates),
            "sample_seconds": rich_elapsed,
            "seconds_per_day": per_day,
            "estimated_full_train_seconds": (
                None if per_day is None else round(per_day * len(train_dates), 3)
            ),
            "full_train_dates": len(train_dates),
        })

    return {
        "task": "wave4.1-forecast-pipeline-profile",
        "date_local": target_date.isoformat(),
        "cp": f"{int(cp):02d}:00",
        "train_start": train_start.isoformat(),
        "train_end": train_end_d.isoformat(),
        "rows": {
            "observations": obs.height,
            "labels": labels.height,
            "train_dates": len(train_dates),
            "empirical_panel": empirical_panel.height,
        },
        "fallback_rate": stats.fallback_rate,
        "target_k_cp": feats.features.get("k_cp"),
        "target_feature_max_ts_utc": feats.feature_max_ts_utc.isoformat(),
        "target_feature_gap_to_cp_min": int(
            (feats.cp_utc - feats.feature_max_ts_utc).total_seconds() // 60
        ),
        "ridge_rich_panel_profile": rich_panel_profile,
        "timings": timings,
        "notes": [
            "METAR cadence is 30 minutes in the source CSV, but live forecast latency is dominated by historical preprocessing, not the last METAR row.",
            "build_empirical_panel_fast is the narrow operational path for empirical forecasts; full rich panels remain a separate Ridge/residual bottleneck.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile live forecast pipeline stages.")
    parser.add_argument("--station-config", type=Path, default=Path("nzwn/config/station.yaml"))
    parser.add_argument("--csv", type=Path, default=Path("NZWN.csv"))
    parser.add_argument("--date", required=True, type=str)
    parser.add_argument("--cp", required=True, type=str)
    parser.add_argument("--train-start", type=str, default="2020-01-01")
    parser.add_argument("--train-end", type=str, default=None)
    parser.add_argument(
        "--rich-panel-sample-days",
        type=int,
        default=0,
        help="Also profile Ridge rich-panel construction on the last N train days.",
    )
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = profile_pipeline(
        station_yaml=args.station_config,
        csv=args.csv,
        target_date=date.fromisoformat(args.date),
        cp=args.cp,
        train_start=date.fromisoformat(args.train_start),
        train_end=date.fromisoformat(args.train_end) if args.train_end else None,
        rich_panel_sample_days=args.rich_panel_sample_days,
    )
    text = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="ascii")
        print(f"Wrote: {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
