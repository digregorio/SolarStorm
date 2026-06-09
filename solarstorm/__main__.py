"""CLI entry point: tmax ingest | baselines | leaderboard | eda.

Every command that produces output writes a versioned artifact to reports/ (P5).
Stdout is an echo, not the authoritative record.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl
import typer

from solarstorm._config import TZ_NAME
from solarstorm.baselines._climatology import fit_climatology
from solarstorm.baselines._empirical import fit_empirical_conditional
from solarstorm.baselines._ladder import LadderResult
from solarstorm.data._iem import fetch_iem_asos
from solarstorm.data._labels import DayCompleteParams, build_tmax_labels
from solarstorm.data._metar import parse_tmp_c_int_from_row
from solarstorm.data._obs import persist_obs
from solarstorm.data._settlement import integer_settlement
from solarstorm.eda._catalog import SEED_HYPOTHESES
from solarstorm.eda._validate import _fit_ols_challenger, validate_hypotheses
from solarstorm.eval._leaderboard import build_leaderboard, export_leaderboard
from solarstorm.features.builder import build_coverage_manifest, build_features
from solarstorm.onda2e import (
    apply_decision_updates,
    build_cloud_cover_baseline_experiment,
    build_cooling_decision_updates,
    build_cooling_domain_artifacts,
    build_decision_gate_artifacts,
    build_eda_feature_candidate_review,
    build_foehn_decision_updates,
    build_foehn_domain_artifacts,
    build_foundation_experiment_catalog,
    build_foundation_experiment_results,
    build_full_eda_artifacts,
    build_prerequisite_artifacts,
    build_regime_binary_macro_candidate_artifacts,
    build_regime_calm_radiative_cloud_signal_validation,
    build_regime_calm_radiative_feature_hypotheses,
    build_regime_calm_radiative_target_diagnostics,
    build_regime_candidate_artifacts,
    build_regime_candidate_v2_assignment_artifacts,
    build_regime_classifiability_artifacts,
    build_regime_deadlock_pivot_artifacts,
    build_regime_design_candidate_v2,
    build_regime_design_decision_updates,
    build_regime_repair_diagnostics,
    build_regime_residual_absorption_artifacts,
    build_regime_v22_calm_radiative_artifacts,
    build_regime_v23_calm_failure_diagnostics,
    build_thesis_domain_eda_artifacts,
    build_thesis_domain_eda_decision_updates,
    build_timing_decision_updates,
    build_timing_domain_artifacts,
    build_wind_decision_updates,
    build_wind_domain_artifacts,
    compare_regime_candidate_r2,
    compare_regime_candidate_v2_v21,
    compare_regime_candidate_v21_v22,
    load_foundation_experiment_inputs,
    parse_thesis_atlas,
    refresh_full_eda_decision_review,
    remove_decision_items,
    thesis_testability_audit,
    validate_binary_macro_regimes,
    validate_regime_candidate_r2,
    validate_regime_design_queue,
    write_binary_validation_reports,
    write_cloud_cover_baseline_experiment_artifacts,
    write_cooling_domain_artifacts,
    write_decision_gate_artifacts,
    write_eda_feature_candidate_review_artifacts,
    write_foehn_domain_artifacts,
    write_foundation_experiment_catalog_artifacts,
    write_foundation_experiment_result_artifacts,
    write_full_eda_artifacts,
    write_onda2e_artifacts,
    write_regime_binary_macro_candidate_artifacts,
    write_regime_calm_radiative_cloud_signal_validation_artifacts,
    write_regime_calm_radiative_feature_hypotheses_artifacts,
    write_regime_calm_radiative_target_diagnostics_artifacts,
    write_regime_candidate_v2_validation_artifacts,
    write_regime_candidate_v21_validation_artifacts,
    write_regime_candidate_validation_artifacts,
    write_regime_classifiability_artifacts,
    write_regime_deadlock_pivot_artifacts,
    write_regime_design_candidate_v2_artifacts,
    write_regime_repair_diagnostics_artifacts,
    write_regime_residual_absorption_artifacts,
    write_regime_v22_calm_radiative_artifacts,
    write_regime_v23_calm_failure_diagnostics_artifacts,
    write_thesis_domain_eda_artifacts,
    write_timing_domain_artifacts,
    write_wind_domain_artifacts,
)
from solarstorm.onda2e._full_eda import _build_cluster_matrix
from solarstorm.onda3 import (
    build_onda3_design_matrix,
    build_onda3_feature_manifest,
    build_onda3_slice_diagnostics,
    run_onda3_baseline_model,
    write_onda3_baseline_artifacts,
)
from solarstorm.robustness._causal_audit import reaudit_causality
from solarstorm.robustness._drift import compute_drift_trend, write_drift_snapshot
from solarstorm.robustness._late_spike import (
    find_late_spike_candidates,
    write_late_spike_candidates,
)
from solarstorm.robustness._lead_time import detect_nowcast_only, lead_time_analysis
from solarstorm.robustness._regime_analysis import detect_dead_regimes, regime_sensitivity
from solarstorm.robustness._regime_diagnostics import (
    cooling_rule_experiment,
    regime_trigger_audit,
    summarize_cooling_rule_experiment,
    summarize_regime_trigger_audit,
    write_cooling_rule_experiment,
    write_regime_trigger_audit,
)
from solarstorm.robustness._replication import (
    hypotheses_from_contract,
    per_year_replication,
)
from solarstorm.robustness._report import evaluate_go_nogo, render_robustness_report
from solarstorm.robustness._tmax_hour import (
    detect_fixed_cp_artifact,
    has_late_tmax_risk_baseline,
    tmax_hour_stratification,
)

app = typer.Typer(help="SolarStorm — intraday Tmax forecaster for NZWN")
CACHE_DIR = Path("./.cache/iem")
REPORTS_DIR = Path("./reports")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_latest_validated_contract(reports_dir: Path) -> Path | None:
    candidates = list(reports_dir.glob("*/validated_feature_contract.json"))
    if not candidates:
        direct = reports_dir / "validated_feature_contract.json"
        return direct if direct.exists() else None

    def sort_key(path: Path) -> tuple[dt.date, float]:
        try:
            parent_date = dt.date.fromisoformat(path.parent.name)
        except ValueError:
            parent_date = dt.date.min
        return parent_date, path.stat().st_mtime

    return max(candidates, key=sort_key)


@app.command()
def ingest(
    station: str = typer.Option("NZWN", help="ICAO station code"),
    start: str = typer.Option("2009-01-01", help="Start date YYYY-MM-DD"),
    end: str = typer.Option("2026-06-03", help="End date YYYY-MM-DD"),
):
    """Backfill METAR observations from IEM ASOS."""
    s, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    df = fetch_iem_asos(station, s, e, cache_dir=CACHE_DIR)
    print(f"Ingested {df.height:,} rows ({station}, {start} to {end})")

    stats = {"n_total": 0, "n_ok": 0, "n_imputed": 0, "n_missing": 0}
    tmp_c_int_vals: list[int | None] = []
    dq_vals: list[str] = []
    for row in df.iter_rows(named=True):
        tt, _, dq, _ = parse_tmp_c_int_from_row(row["metar"], row.get("tmpf"))
        stats["n_total"] += 1
        stats[f"n_{dq}"] += 1
        tmp_c_int_vals.append(tt)
        dq_vals.append(dq)
    print(f"Parse stats: {stats}")

    df = df.with_columns(
        pl.Series("tmp_c_int", tmp_c_int_vals, dtype=pl.Int64),
        pl.Series("dq_tmp_c_int", dq_vals, dtype=pl.Utf8),
    )

    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    df = persist_obs(df, data_dir)

    labels = build_tmax_labels(df, DayCompleteParams())
    complete = labels.filter(pl.col("day_complete"))
    print(f"Labels: {labels.height} days, {complete.height} complete")

    labels.write_parquet(data_dir / "labels.parquet")
    print(f"Saved labels to {data_dir / 'labels.parquet'}")


@app.command()
def baselines(
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
):
    """Fit all baselines and print a summary."""
    labels = pl.read_parquet(labels_path)
    complete = labels.filter(pl.col("day_complete"))

    print(f"Loaded {complete.height} complete days")

    climo = fit_climatology(
        complete,
        train_start=dt.date(2009, 1, 1),
        train_end=dt.date(2025, 12, 31),
    )
    print(f"Climatology: {climo.n_train_days} training days")

    fit_empirical_conditional(
        complete,
        train_window=(dt.date(2009, 1, 1), dt.date(2025, 12, 31)),
    )
    print("Empirical conditional fitted")

    print("\nBaselines ready. Run 'leaderboard' to evaluate.")


@app.command()
def features(
    obs_path: str = typer.Option("./data/obs.parquet", help="Path to obs parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    output_dir: str = typer.Option("./data", help="Output directory for features.parquet"),
):
    """Compute causal feature table from obs + labels (bridge P3)."""
    obs = pl.read_parquet(obs_path)
    labels = pl.read_parquet(labels_path)
    print(f"Loaded {obs.height} obs rows, {labels.height} label rows")

    result = build_features(obs, labels)
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    result.write_parquet(out / "features.parquet")
    print(f"Features: {result.height} rows, {len(result.columns)} columns")

    # Coverage manifest
    manifest = build_coverage_manifest(result)
    today_iso = dt.date.today().isoformat()
    report_dir = REPORTS_DIR / today_iso
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = report_dir / "feature_coverage.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Summary
    n_computable = sum(1 for v in manifest.values() if v["status"] == "computable")
    n_blocked = sum(1 for v in manifest.values() if v["status"] == "BLOCKED")
    print(f"Coverage manifest: {n_computable} computable, {n_blocked} BLOCKED")
    print(f"  {manifest_path}")


@app.command()
def validate(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
):
    """Run hypothesis validation harness (bridge P3)."""
    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    print(f"Loaded {features.height} feature rows, {labels.height} label rows")

    all_results, contract = validate_hypotheses(
        features,
        labels,
        SEED_HYPOTHESES,
    )
    print(f"Validation complete: {contract['n_validated']} validated, {contract['n_rejected']} rejected")

    today_iso = dt.date.today().isoformat()
    report_dir = REPORTS_DIR / today_iso
    report_dir.mkdir(parents=True, exist_ok=True)

    # ---- JSON export ----
    results_json = []
    for r in all_results:
        d = {
            "id": r.id,
            "feature_column": r.feature_column,
            "cp": r.cp,
            "regime": r.regime,
            "effect_size": r.effect_size,
            "ci_lo": r.ci_lo,
            "ci_hi": r.ci_hi,
            "p_value": r.p_value,
            "fdr_adjusted": r.fdr_adjusted,
            "passes": r.passes,
            "n_days": r.n_days,
            "status": r.status,
            "blocked_reason": r.blocked_reason,
            "best_null_name": r.best_null_name,
            "best_null_mae": r.best_null_mae,
        }
        if r.gate_results:
            d["gates"] = {
                k: {"passed": g.passed, "status": g.status, "detail": g.detail}
                for k, g in r.gate_results.items()
            }
        results_json.append(d)

    json_path = report_dir / "hypothesis_results.json"
    json_path.write_text(json.dumps(results_json, indent=2), encoding="utf-8")

    # ---- Markdown table ----
    md_lines = [
        f"# Hypothesis Validation Results — {today_iso}",
        "",
        "| id | feature | cp | regime | effect_size | ci_lo | ci_hi | p_value | fdr | passes | gates | status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in all_results:
        fdr = "Y" if r.fdr_adjusted else "N"
        passes = "Y" if r.passes else "N"
        gates_str = " ".join(f"{k}:{g.status}" for k, g in (r.gate_results or {}).items())
        es = f"{r.effect_size:.4f}" if r.effect_size is not None else ""
        clo = f"{r.ci_lo:.4f}" if r.ci_lo is not None else ""
        chi = f"{r.ci_hi:.4f}" if r.ci_hi is not None else ""
        pv = f"{r.p_value:.6f}" if r.p_value is not None else ""
        md_lines.append(
            f"| {r.id} | {r.feature_column} | {r.cp} | {r.regime} "
            f"| {es} | {clo} | {chi} | {pv} "
            f"| {fdr} | {passes} | {gates_str} | {r.status} |"
        )

    md_path = report_dir / "hypothesis_results.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # ---- Validated contract ----
    contract_path = report_dir / "validated_feature_contract.json"
    contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    print(f"\nExported to {report_dir}:")
    print(f"  {json_path.name}")
    print(f"  {md_path.name}")
    print(f"  {contract_path.name}")
    print(
        f"\nValidated: {contract.get('n_validated', 0)}  "
        f"Rejected: {contract.get('n_rejected', 0)}  "
        f"BLOCKED: {len(contract.get('blocked', []))}"
    )


@app.command()
def leaderboard(
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    window_days: int = typer.Option(30, help="Recent window size in days"),
):
    """Evaluate all baselines on recent window and export leaderboard (P5)."""
    labels = pl.read_parquet(labels_path)
    complete = labels.filter(pl.col("day_complete"))

    today = dt.date.today()
    window_start = today - dt.timedelta(days=window_days)
    recent = complete.filter(pl.col("date_local").is_between(window_start, today - dt.timedelta(days=1)))

    if recent.height == 0:
        print(f"No complete days in window [{window_start}, {today})")
        raise typer.Exit(1)

    print(f"Evaluating {recent.height} days in window [{window_start}, {today})")

    # Fit baselines on all data up to window_start
    train_end = window_start - dt.timedelta(days=1)
    train_labels = complete.filter(pl.col("date_local") <= train_end)

    climo = fit_climatology(
        train_labels,
        train_start=dt.date(2009, 1, 1),
        train_end=train_end,
    )

    # ---- L4 empirical conditional ----
    history_start = complete["date_local"].min()
    emp = fit_empirical_conditional(
        train_labels,
        train_window=(history_start, train_end),
    )
    support_k = sorted(complete["tmax_int"].unique().to_list())

    # ---- Date-to-tmax lookup for L1 (dminus1) ----
    tmax_by_date: dict[dt.date, int] = {
        row["date_local"]: row["tmax_int"] for row in complete.iter_rows(named=True)
    }

    # ---- Build regime lookup for segments ----
    regime_lookup: dict[tuple[dt.date, str], str] = {}
    features_path = Path("./data/features.parquet")
    if features_path.exists():
        feats_df = pl.read_parquet(features_path)
        for frow in feats_df.select(["date_local", "cp", "regime_label"]).iter_rows(named=True):
            regime_lookup[(frow["date_local"], frow["cp"])] = frow["regime_label"] or "unknown"

    # ---- Evaluate all baselines per-row (with regime tracking) ----
    results: list[LadderResult] = []
    regime_errors: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    n_missing_dminus1: int = 0
    for row in recent.iter_rows(named=True):
        d = row["date_local"]
        truth = row["tmax_int"]

        for cp_str in ["20:00", "21:00", "22:00", "23:00"]:
            cp_code = cp_str.replace(":", "")
            kcp_col = f"k_cp__cp_{cp_code}"
            kcp = row.get(kcp_col)
            if kcp is None:
                continue

            kcp_int = int(kcp)
            regime = regime_lookup.get((d, cp_str), "unknown")
            error_l0 = kcp_int - truth

            # L0: persistence
            results.append(
                LadderResult(
                    level="L0",
                    name="persistence",
                    cp=cp_str,
                    mae=abs(error_l0),
                    rmse=error_l0**2,
                    bias=error_l0,
                    bracket_match=1.0 if kcp_int == truth else 0.0,
                    n=1,
                )
            )
            regime_errors[("L0", "persistence", cp_str, regime)].append(abs(error_l0))

            # L1: dminus1
            prev_day = d - dt.timedelta(days=1)
            tmax_dminus1 = tmax_by_date.get(prev_day)
            if tmax_dminus1 is not None:
                error_l1 = tmax_dminus1 - truth
                results.append(
                    LadderResult(
                        level="L1",
                        name="dminus1",
                        cp=cp_str,
                        mae=abs(error_l1),
                        rmse=error_l1**2,
                        bias=error_l1,
                        bracket_match=1.0 if tmax_dminus1 == truth else 0.0,
                        n=1,
                    )
                )
                regime_errors[("L1", "dminus1", cp_str, regime)].append(abs(error_l1))
            else:
                n_missing_dminus1 += 1

            # L2: climatology
            clim_pred = integer_settlement(climo.tmax_dec_for(d))
            error_l2 = clim_pred - truth
            results.append(
                LadderResult(
                    level="L2",
                    name="climatology_doy",
                    cp=cp_str,
                    mae=abs(error_l2),
                    rmse=error_l2**2,
                    bias=error_l2,
                    bracket_match=1.0 if clim_pred == truth else 0.0,
                    n=1,
                )
            )
            regime_errors[("L2", "climatology_doy", cp_str, regime)].append(abs(error_l2))

            # L4: empirical conditional (mode of distribution)
            dist, source = emp.predict_dist(
                month=d.month,
                cp=str(cp_str),
                k_cp=kcp_int,
                support_k=support_k,
            )
            l4_p50 = max(dist, key=dist.get)
            error_l4 = l4_p50 - truth
            results.append(
                LadderResult(
                    level="L4",
                    name="empirical_conditional",
                    cp=cp_str,
                    mae=abs(error_l4),
                    rmse=error_l4**2,
                    bias=error_l4,
                    bracket_match=1.0 if l4_p50 == truth else 0.0,
                    n=1,
                    fallback_rate=0.0 if source == "conditional" else 1.0,
                )
            )
            regime_errors[("L4", "empirical_conditional", cp_str, regime)].append(abs(error_l4))

    # ---- Aggregate per-row results into per-(level, name, cp) summaries ----
    from solarstorm.baselines._ladder import aggregate_results

    aggregated = aggregate_results(results)

    if n_missing_dminus1 > 0:
        print(f"L1 (dminus1): {n_missing_dminus1} rows skipped (previous day data unavailable)")

    # ---- Build segments: MAE by regime for each baseline x CP ----
    segments: dict[str, list[LadderResult]] = {}
    for (level, name, cp, regime), errors in sorted(regime_errors.items()):
        n_regime = len(errors)
        if n_regime > 0:
            segments.setdefault(regime, []).append(
                LadderResult(
                    level=level,
                    name=name,
                    cp=cp,
                    mae=sum(errors) / n_regime,
                    n=n_regime,
                )
            )

    # ---- Gates: G1-G5 for each aggregated baseline x CP ----
    from solarstorm.eval._gates import apply_all_gates

    gates_dict: dict[str, dict[str, dict]] = {}
    best_null_mae_by_cp: dict[str, float] = {}
    for r in aggregated:
        if r.level != "feature":
            prev_best = best_null_mae_by_cp.get(r.cp, float("inf"))
            if r.mae < prev_best:
                best_null_mae_by_cp[r.cp] = r.mae

    for r in aggregated:
        if r.level == "feature":
            continue
        best_mae = best_null_mae_by_cp.get(r.cp, r.mae)
        gate_results = apply_all_gates(
            model_mae=r.mae,
            best_null_mae=best_mae,
            cp=r.cp,
            fallback_rate=r.fallback_rate or 0.0,
            p50_mode_share=r.p50_mode_share,
            corr_diff=r.corr_diff,
            per_cp_passed=r.mae <= best_mae,
        )
        gates_dict.setdefault(r.cp, {})[f"{r.level}_{r.name}"] = {
            g.gate: {"passed": g.passed, "status": g.status, "detail": g.detail}
            for g in gate_results.values()
        }

    # ---- Build and export ----
    board = build_leaderboard(
        results=aggregated,
        segments=segments,
        gates=gates_dict,
        window_start=window_start,
        window_end=today - dt.timedelta(days=1),
    )

    # ---- Baseline+Feature Nulls ----
    today_iso = dt.date.today().isoformat()
    contract_path = REPORTS_DIR / today_iso / "validated_feature_contract.json"
    features_path = Path("./data/features.parquet")

    if contract_path.exists() and features_path.exists():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        features_df = pl.read_parquet(features_path)
        feature_rows: list[LadderResult] = []

        for vf in contract.get("validated_features", []):
            fc = vf["feature_column"]
            cp_str = vf["cp"]

            # Skip regime-specific results; use the "all" aggregate
            if vf.get("regime", "all") != "all":
                continue

            # Fit OLS challenger on training data
            train_feats_cp = features_df.filter(
                (pl.col("date_local") <= train_end) & (pl.col("cp") == cp_str)
            )
            ols = _fit_ols_challenger(train_feats_cp, complete, fc, cp_str)
            if ols is None:
                continue

            k_col = f"k_cp__cp_{cp_str.replace(':', '')}"

            errors: list[float] = []
            preds: list[float] = []
            truths: list[float] = []
            base_preds: list[float] = []

            for trow in recent.iter_rows(named=True):
                td = trow["date_local"]
                truth_val = trow["tmax_int"]
                kcp_val = trow.get(k_col)
                if kcp_val is None:
                    continue

                feat_row = features_df.filter((pl.col("date_local") == td) & (pl.col("cp") == cp_str))
                if feat_row.height == 0:
                    continue

                feat_vals = feat_row[fc].to_list()
                if not feat_vals:
                    continue

                pred_rw = ols.predict_remaining_warming(feat_vals[0])
                if pred_rw is None:
                    continue
                pred_tmax = integer_settlement(kcp_val + pred_rw)

                errors.append(abs(pred_tmax - truth_val))
                preds.append(float(pred_tmax))
                truths.append(float(truth_val))
                base_preds.append(float(kcp_val))

            if len(errors) >= 5:
                mean_ae = sum(errors) / len(errors)

                # corr_diff
                pa = np.array(preds)
                ta = np.array(truths)
                ba = np.array(base_preds)
                mask = ~(np.isnan(pa) | np.isnan(ta))
                if mask.sum() > 2:
                    r_model = float(np.corrcoef(pa[mask], ta[mask])[0, 1])
                    r_base = float(np.corrcoef(ba[mask], ta[mask])[0, 1])
                    cdiff = r_model - r_base
                else:
                    cdiff = None

                feature_rows.append(
                    LadderResult(
                        level="feature",
                        name=fc,
                        cp=cp_str,
                        mae=mean_ae,
                        n=len(errors),
                        corr_diff=cdiff,
                    )
                )

        if feature_rows:
            board["feature_nulls"] = [
                {"name": r.name, "cp": r.cp, "mae": r.mae, "n": r.n, "corr_diff": r.corr_diff}
                for r in feature_rows
            ]

    json_path, md_path = export_leaderboard(board, REPORTS_DIR / "leaderboard")
    print("Leaderboard exported:")
    print(f"  {json_path}")
    print(f"  {md_path}")

    # Print summary
    print(f"\n{board['summary']}")


@app.command()
def eda(
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
):
    """Run hypothesis catalog and export results (P5)."""
    hypotheses = SEED_HYPOTHESES
    results = []

    for h in hypotheses:
        # Placeholder: actual test runs through walk-forward harness
        result = {
            "id": h.id,
            "description": h.description,
            "feature_column": h.feature_column,
            "source": h.source,
            "status": "pending",  # Will be filled by actual EDA run
        }
        results.append(result)

    out = REPORTS_DIR / "hypotheses"
    out.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    json_path = out / f"{today}-hypotheses.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    md_lines = ["# Hypothesis Catalog", f"Generated: {today}", ""]
    for r in results:
        md_lines.append(f"- **{r['id']}** [{r['status']}]: {r['description']} (source: {r['source']})")
    md_path = out / f"{today}-hypotheses.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Hypothesis results exported to {out}")
    print(f"  {json_path}")
    print(f"  {md_path}")


@app.command()
def robustness(
    features_path: str = typer.Option(
        "./data/features.parquet",
        "--features",
        "--features-path",
        help="Path to features parquet",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        "--labels",
        "--labels-path",
        help="Path to labels parquet",
    ),
    output_dir: str = typer.Option(
        "./reports/robustness",
        "--output",
        "--output-dir",
        help="Output directory for robustness artifacts",
    ),
    test_years: str | None = typer.Option(
        None,
        help="Comma-separated test years. Defaults to the full available Onda 4 range.",
    ),
    regime_set: str | None = typer.Option(
        None,
        "--regime-set",
        help=(
            "Optional comma-separated regime labels for R2 dead-regime detection. "
            "Defaults to the production physical regime family."
        ),
    ),
):
    """Run Onda 4 robustness hardening checks.

    This command deliberately does no trading, no EV, no position sizing, and
    no Polymarket API work. It only asks whether the current feature foundation
    is robust enough to unblock model work.
    """
    features_file = Path(features_path)
    labels_file = Path(labels_path)
    out_dir = Path(output_dir)

    if not features_file.exists():
        print(f"ERROR: features parquet not found: {features_file}")
        raise typer.Exit(2)
    if not labels_file.exists():
        print(f"ERROR: labels parquet not found: {labels_file}")
        raise typer.Exit(2)

    contract_path = _find_latest_validated_contract(REPORTS_DIR)
    if contract_path is None:
        print(f"ERROR: validated_feature_contract.json not found under {REPORTS_DIR}")
        print("Run 'python -m solarstorm validate' first.")
        raise typer.Exit(2)

    features_df = pl.read_parquet(features_file)
    labels_df = pl.read_parquet(labels_file)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    hypotheses, cp_set = hypotheses_from_contract(contract)

    if not hypotheses or not cp_set:
        print(f"ERROR: no pooled validated features found in {contract_path}")
        raise typer.Exit(2)

    parsed_years: tuple[int, ...] | None = None
    if test_years:
        try:
            parsed_years = tuple(int(part.strip()) for part in test_years.split(",") if part.strip())
        except ValueError:
            print(f"ERROR: invalid --test-years value: {test_years}")
            raise typer.Exit(2) from None
    parsed_regime_set = (
        tuple(part.strip() for part in regime_set.split(",") if part.strip()) if regime_set else None
    )

    print(f"Loaded {features_df.height:,} feature rows and {labels_df.height:,} label rows")
    print(f"Using contract: {contract_path}")
    print(f"Validated pooled features: {len(hypotheses)}; CPs: {', '.join(cp_set)}")

    print("\n--- R1: Per-Year Replication ---")
    year_matrix, replication_summary = per_year_replication(
        features_df,
        labels_df,
        hypotheses,
        test_years=parsed_years,
        cp_set=cp_set,
        seed=42,
    )
    n_passing_years = (
        year_matrix.filter(pl.col("passes_g1_g5").fill_null(False))["year"].n_unique()
        if year_matrix.height
        else 0
    )
    print(
        f"Years tested: {replication_summary.get('n_years_tested', 0)}; "
        f"years with >=1 pass: {n_passing_years}"
    )

    print("\n--- R2: Regime Sensitivity ---")
    regime_tab = regime_sensitivity(
        features_df,
        labels_df,
        hypotheses,
        cp_set=cp_set,
        seed=42,
    )
    dead_regimes = (
        detect_dead_regimes(regime_tab, regimes=parsed_regime_set)
        if parsed_regime_set is not None
        else detect_dead_regimes(regime_tab)
    )
    print(f"Regime rows: {regime_tab.height}; dead regimes: {dead_regimes if dead_regimes else 'None'}")

    print("\n--- R3: Causal Firewall Re-Audit ---")
    feature_columns = [hyp.feature_column for hyp in hypotheses]
    causal_clean, causal_violating = reaudit_causality(features_df, feature_columns)
    print(f"Clean: {len(causal_clean)}; violations: {len(causal_violating)}")

    print("\n--- R4: Drift Trend ---")
    drift = compute_drift_trend(year_matrix)
    print(
        f"S={drift['trend_statistic']:.2f}; p={drift['p_value']:.4f}; "
        f"direction={drift['trend_direction']}; warning={drift['warning']}"
    )
    write_drift_snapshot(drift, out_dir / "robustness_drift_snapshot.json")

    print("\n--- R5: Fresh Gate Re-Run ---")
    try:
        pooled_results, _pooled_contract = validate_hypotheses(
            features_df,
            labels_df,
            hypotheses,
            cp_set=cp_set,
            seed=42,
        )
        gates_rerun_pass = any(
            result.regime == "all" and result.status == "validated" for result in pooled_results
        )
    except ValueError as exc:
        print(f"Fresh gate re-run failed: {exc}")
        gates_rerun_pass = False
    print(f"Fresh gates pass: {gates_rerun_pass}")

    validated_entries = contract.get("validated_features", [])

    print("\n--- R6: Anti-Nowcast Lead-Time ---")
    lead_table = lead_time_analysis(features_df, labels_df, validated_entries)
    nowcast_only = detect_nowcast_only(lead_table)
    print(f"Lead-time rows: {lead_table.height}; nowcast-only evidence: {nowcast_only}")

    print("\n--- R7: Month/Regime Tmax Timing Norms ---")
    tmax_hour_tab = tmax_hour_stratification(features_df, labels_df, validated_entries)
    fixed_cp_artifact = detect_fixed_cp_artifact(tmax_hour_tab)
    late_tmax_risk_baseline_exists = has_late_tmax_risk_baseline(tmax_hour_tab)
    print(f"Tmax-hour rows: {tmax_hour_tab.height}; fixed-CP artifact: {fixed_cp_artifact}")

    print("\n--- R8: Late-Spike Evidence Pack ---")
    late_spikes = find_late_spike_candidates(labels_df, cp_set=cp_set)
    late_spike_path = out_dir / "late_spike_candidates.json"
    write_late_spike_candidates(late_spikes, late_spike_path)
    print(f"Late-spike candidates: {late_spikes.height}; artifact: {late_spike_path}")

    print("\n--- R9: Late-Tmax Risk Baseline ---")
    print(f"Late-Tmax risk baseline exists: {late_tmax_risk_baseline_exists}")

    artifact_hashes = {
        "features": _sha256_file(features_file),
        "labels": _sha256_file(labels_file),
        "validated_feature_contract": _sha256_file(contract_path),
    }
    report_path = render_robustness_report(
        output_dir=out_dir,
        year_matrix=year_matrix,
        regime_cross_tab=regime_tab,
        drift_result=drift,
        causal_clean=causal_clean,
        causal_violating=causal_violating,
        lead_time_table=lead_table,
        tmax_hour_table=tmax_hour_tab,
        late_spike_candidates=late_spikes,
        gates_rerun_pass=gates_rerun_pass,
        artifact_hashes=artifact_hashes,
        regime_set=parsed_regime_set,
    )

    verdict = evaluate_go_nogo(
        {
            "n_passing_years": n_passing_years,
            "dead_regimes": dead_regimes,
            "causal_violations": causal_violating,
            "gates_rerun_pass": gates_rerun_pass,
            "lead_time_ok": not nowcast_only,
            "fixed_cp_artifact": fixed_cp_artifact,
            "late_spike_artifact_produced": True,
            "late_tmax_risk_baseline_exists": late_tmax_risk_baseline_exists,
        }
    )

    print(f"\nReport: {report_path}")
    print(f"===== VERDICT: {verdict} =====")
    if verdict == "NO-GO":
        raise typer.Exit(1)


@app.command("regime-diagnostics")
def regime_diagnostics(
    obs_path: str = typer.Option("./data/obs.parquet", help="Path to obs parquet"),
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    output_dir: str = typer.Option("./reports/regime", help="Output directory"),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
    tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
):
    """Audit physical-regime trigger evidence without changing labels or gates."""
    obs_file = Path(obs_path)
    features_file = Path(features_path)
    if not obs_file.exists():
        print(f"ERROR: obs parquet not found: {obs_file}")
        raise typer.Exit(2)
    if not features_file.exists():
        print(f"ERROR: features parquet not found: {features_file}")
        raise typer.Exit(2)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    obs_df = pl.read_parquet(obs_file)
    features_df = pl.read_parquet(features_file)
    audit = regime_trigger_audit(
        obs_df,
        features_df,
        cp_set=parsed_cp_set,
        tz_name=tz_name,
    )
    summary = summarize_regime_trigger_audit(audit)
    json_path, md_path = write_regime_trigger_audit(
        audit,
        summary,
        output_dir=output_dir,
    )
    experiment = cooling_rule_experiment(audit)
    experiment_summary = summarize_cooling_rule_experiment(experiment)
    experiment_json_path, experiment_md_path = write_cooling_rule_experiment(
        experiment,
        experiment_summary,
        output_dir=output_dir,
    )
    print(f"Regime trigger rows: {audit.height}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Cooling experiment rows: {experiment.height}")
    print(f"Cooling experiment JSON: {experiment_json_path}")
    print(f"Cooling experiment Markdown: {experiment_md_path}")


@app.command("regime-design-validate")
def regime_design_validate(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    obs_path: str = typer.Option("./data/obs.parquet", help="Path to obs parquet"),
    candidate_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v1.csv",
        help="Path to Onda 2E regime design candidate CSV",
    ),
    queue_path: str = typer.Option(
        "./reports/onda2e/regime_design_queue.csv",
        help="Path to ADR-012 regime design queue CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for candidate validation artifacts",
    ),
    tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
    test_start: str | None = typer.Option(
        None,
        "--test-start",
        help="Comma-separated walk-forward test-start dates YYYY-MM-DD",
    ),
):
    """Validate the Onda 2E regime-design candidate without promoting production labels."""
    features_file = Path(features_path)
    labels_file = Path(labels_path)
    obs_file = Path(obs_path)
    candidate_file = Path(candidate_path)
    queue_file = Path(queue_path)
    for path, label in (
        (features_file, "features"),
        (labels_file, "labels"),
        (obs_file, "obs"),
        (candidate_file, "candidate"),
        (queue_file, "regime design queue"),
    ):
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            raise typer.Exit(2)

    queue = pl.read_csv(queue_file)
    if not validate_regime_design_queue(queue):
        print("ERROR: ADR-012 queue does not authorize WCT-REGIME-016 regime design validation.")
        raise typer.Exit(2)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    test_starts = (
        [dt.date.fromisoformat(value.strip()) for value in test_start.split(",") if value.strip()]
        if test_start
        else None
    )
    features_df = pl.read_parquet(features_file)
    labels_df = pl.read_parquet(labels_file)
    obs_df = pl.read_parquet(obs_file)
    candidate = pl.read_csv(candidate_file)
    candidate_artifacts = build_regime_candidate_artifacts(
        candidate,
        features_df,
        labels_df,
        obs_df,
        tz_name=tz_name,
    )
    validation = validate_regime_candidate_r2(
        features_df,
        labels_df,
        candidate_artifacts["regime_candidate_assignments"],
        SEED_HYPOTHESES,
        cp_set=parsed_cp_set,
        test_starts=test_starts,
    )
    paths = write_regime_candidate_validation_artifacts(
        {**candidate_artifacts, **validation},
        output_dir=output_dir,
    )
    dead = validation["dead_candidate_regimes"].filter(pl.col("status") == "DEAD").height
    print(f"Candidate assignments: {candidate_artifacts['regime_candidate_assignments'].height}")
    print(f"Dead candidate regimes: {dead}")
    print(f"Validation report: {paths['validation_report_md']}")


@app.command("regime-repair-diagnostics")
def regime_repair_diagnostics(
    candidate_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v1.csv",
        help="Path to Onda 2E regime design candidate CSV",
    ),
    assignments_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v1.csv",
        help="Path to v1 candidate assignment CSV",
    ),
    r2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation.csv",
        help="Path to v1 candidate R2 validation CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for repair diagnostics",
    ),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
    dead_families: str = typer.Option(
        "candidate_maritime_cloudy,candidate_mixed_or_transition",
        help="Comma-separated candidate families to diagnose",
    ),
    min_support_rows: int = typer.Option(30, help="Minimum assignment rows per family"),
):
    """Write non-production diagnostics for dead or weak regime families."""
    candidate_file = Path(candidate_path)
    assignments_file = Path(assignments_path)
    r2_file = Path(r2_path)
    for path, label in (
        (candidate_file, "candidate"),
        (assignments_file, "candidate assignments"),
        (r2_file, "candidate R2 validation"),
    ):
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            raise typer.Exit(2)

    artifacts = build_regime_repair_diagnostics(
        pl.read_csv(candidate_file),
        pl.read_csv(assignments_file),
        pl.read_csv(r2_file),
        dead_families=tuple(part.strip() for part in dead_families.split(",") if part.strip()),
        cp_set=tuple(part.strip() for part in cp_set.split(",") if part.strip()),
        min_support_rows=min_support_rows,
    )
    paths = write_regime_repair_diagnostics_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    diagnostics = artifacts["regime_repair_diagnostics"]
    print(f"Regime repair diagnostic rows: {diagnostics.height}")
    print(f"Diagnostics CSV: {paths['regime_repair_diagnostics_csv']}")
    print(f"Diagnostics Markdown: {paths['regime_repair_diagnostics_md']}")


@app.command("regime-candidate-v2")
def regime_candidate_v2(
    candidate_v1_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v1.csv",
        help="Path to v1 regime design candidate CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/onda2e",
        help="Output directory for v2 candidate artifacts",
    ),
):
    """Build the non-production Regime Ontology v2 design candidate."""
    candidate_file = Path(candidate_v1_path)
    if not candidate_file.exists():
        print(f"ERROR: v1 candidate file not found: {candidate_file}")
        raise typer.Exit(2)

    artifacts = build_regime_design_candidate_v2(pl.read_csv(candidate_file))
    paths = write_regime_design_candidate_v2_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    candidate_v2 = artifacts["regime_design_candidate_v2"]
    print(f"Regime candidate v2 rows: {candidate_v2.height}")
    print(f"Candidate v2 CSV: {paths['regime_design_candidate_v2_csv']}")
    print(f"Candidate v2 Markdown: {paths['regime_design_candidate_v2_md']}")


@app.command("regime-design-v2-validate")
def regime_design_v2_validate(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    obs_path: str = typer.Option("./data/obs.parquet", help="Path to obs parquet"),
    candidate_v2_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v2.csv",
        help="Path to Regime Ontology v2 candidate CSV",
    ),
    v1_r2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation.csv",
        help="Path to v1 candidate R2 validation CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for v2 validation artifacts",
    ),
    tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
    test_start: str | None = typer.Option(
        None,
        "--test-start",
        help="Comma-separated walk-forward test-start dates YYYY-MM-DD",
    ),
    min_assignment_rows: int = typer.Option(30, help="Minimum assignment rows per macro"),
):
    """Validate Regime Ontology v2 without promoting production labels."""
    required_paths = [
        Path(features_path),
        Path(labels_path),
        Path(obs_path),
        Path(candidate_v2_path),
        Path(v1_r2_path),
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    test_starts = (
        [dt.date.fromisoformat(value.strip()) for value in test_start.split(",") if value.strip()]
        if test_start
        else None
    )
    features_df = pl.read_parquet(features_path)
    labels_df = pl.read_parquet(labels_path)
    obs_df = pl.read_parquet(obs_path)
    candidate_v2 = pl.read_csv(candidate_v2_path)
    v1_r2 = pl.read_csv(v1_r2_path)
    assignments = build_regime_candidate_v2_assignment_artifacts(
        candidate_v2,
        features_df,
        labels_df,
        obs_df,
        tz_name=tz_name,
    )
    validation = validate_regime_candidate_r2(
        features_df,
        labels_df,
        assignments["regime_candidate_assignments_v2"],
        SEED_HYPOTHESES,
        cp_set=parsed_cp_set,
        test_starts=test_starts,
    )
    v1_regimes = (
        tuple(sorted(str(value) for value in v1_r2["regime"].drop_nulls().unique().to_list()))
        if "regime" in v1_r2.columns
        else ()
    )
    assignment_frame = assignments["regime_candidate_assignments_v2"]
    v2_regimes = (
        tuple(
            sorted(
                str(value)
                for value in assignment_frame["candidate_regime_label"].drop_nulls().unique().to_list()
            )
        )
        if "candidate_regime_label" in assignment_frame.columns
        else ()
    )
    comparison = compare_regime_candidate_r2(
        v1_r2=v1_r2,
        v2_r2=validation["regime_candidate_r2_validation"],
        v2_assignments=assignment_frame,
        v1_regimes=v1_regimes,
        v2_regimes=v2_regimes,
        protected_v2_regimes=("macro_nw_continuum", "macro_southerly_flow"),
        min_assignment_rows=min_assignment_rows,
    )
    paths = write_regime_candidate_v2_validation_artifacts(
        {**assignments, **validation, **comparison},
        output_dir=output_dir,
    )
    print(f"v2 assignments: {assignment_frame.height}")
    print(f"v2 validation report: {paths['regime_candidate_v2_validation_report_md']}")


@app.command("regime-design-v21-validate")
def regime_design_v21_validate(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    assignments_v2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2.csv",
        help="Path to Regime Ontology v2 assignment CSV",
    ),
    r2_v2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation_v2.csv",
        help="Path to Regime Ontology v2 R2 validation CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for v2.1 validation artifacts",
    ),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
    test_start: str | None = typer.Option(
        None,
        "--test-start",
        help="Comma-separated walk-forward test-start dates YYYY-MM-DD",
    ),
):
    """Validate Regime Ontology v2.1 without promoting production labels."""
    required_paths = [
        Path(features_path),
        Path(labels_path),
        Path(assignments_v2_path),
        Path(r2_v2_path),
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    test_starts = (
        [dt.date.fromisoformat(value.strip()) for value in test_start.split(",") if value.strip()]
        if test_start
        else None
    )
    features_df = pl.read_parquet(features_path)
    labels_df = pl.read_parquet(labels_path)
    assignments_v2 = pl.read_csv(assignments_v2_path)
    if "date_local" in assignments_v2.columns:
        assignments_v2 = assignments_v2.with_columns(pl.col("date_local").cast(pl.Date))
    v2_r2 = pl.read_csv(r2_v2_path)
    residual_artifacts = build_regime_residual_absorption_artifacts(assignments_v2)
    residual_paths = write_regime_residual_absorption_artifacts(
        residual_artifacts,
        output_dir=output_dir,
    )
    assignment_frame = residual_artifacts["regime_candidate_assignments_v2_1"]
    validation = validate_regime_candidate_r2(
        features_df,
        labels_df,
        assignment_frame,
        SEED_HYPOTHESES,
        cp_set=parsed_cp_set,
        test_starts=test_starts,
    )
    v2_regimes = (
        tuple(sorted(str(value) for value in v2_r2["regime"].drop_nulls().unique().to_list()))
        if "regime" in v2_r2.columns
        else tuple(
            sorted(
                str(value)
                for value in assignments_v2["candidate_regime_label"].drop_nulls().unique().to_list()
            )
        )
    )
    v21_regimes = (
        tuple(
            sorted(
                str(value)
                for value in assignment_frame["candidate_regime_label"].drop_nulls().unique().to_list()
            )
        )
        if "candidate_regime_label" in assignment_frame.columns
        else ()
    )
    comparison = compare_regime_candidate_v2_v21(
        v2_r2=v2_r2,
        v21_r2=validation["regime_candidate_r2_validation"],
        v21_assignments=assignment_frame,
        residual_diagnostics=residual_artifacts["regime_residual_absorption_diagnostics"],
        v2_regimes=v2_regimes,
        v21_regimes=v21_regimes,
        protected_v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
    )
    validation_paths = write_regime_candidate_v21_validation_artifacts(
        {**validation, **comparison},
        output_dir=output_dir,
    )
    absorbed = (
        assignment_frame.filter(pl.col("absorbed_from_residual")).height if assignment_frame.height else 0
    )
    comparison_frame = comparison["regime_candidate_v2_v21_comparison"]
    dead_count = int(comparison_frame["v21_dead_regimes"][0]) if comparison_frame.height else len(v21_regimes)
    print(f"v2.1 assignments: {assignment_frame.height}")
    print(f"absorbed residual rows: {absorbed}")
    print(f"v2.1 dead macros: {dead_count}")
    print(f"residual absorption report: {residual_paths['regime_residual_absorption_diagnostics_md']}")
    print(f"v2.1 validation report: {validation_paths['regime_candidate_v21_validation_report_md']}")


@app.command("regime-design-v22-validate")
def regime_design_v22_validate(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    obs_path: str = typer.Option("./data/obs.parquet", help="Path to obs parquet"),
    assignments_v21_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_1.csv",
        help="Path to Regime Ontology v2.1 assignment CSV",
    ),
    r2_v21_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation_v2_1.csv",
        help="Path to Regime Ontology v2.1 R2 validation CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for v2.2 validation artifacts",
    ),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
    test_start: str | None = typer.Option(
        None,
        "--test-start",
        help="Comma-separated walk-forward test-start dates YYYY-MM-DD",
    ),
    min_assignment_rows: int = typer.Option(
        30,
        help="Minimum assignment rows for protected v2.2 macro support",
    ),
    tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
):
    """Validate Regime Ontology v2.2 with calm/radiative restored."""
    required_paths = [
        Path(features_path),
        Path(labels_path),
        Path(obs_path),
        Path(assignments_v21_path),
        Path(r2_v21_path),
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    test_starts = (
        [dt.date.fromisoformat(value.strip()) for value in test_start.split(",") if value.strip()]
        if test_start
        else None
    )
    features_df = pl.read_parquet(features_path)
    labels_df = pl.read_parquet(labels_path)
    obs_df = pl.read_parquet(obs_path)
    physical_matrix = _build_cluster_matrix(
        features_df,
        labels_df,
        obs_df,
        tz_name=tz_name,
    )
    assignments_v21 = pl.read_csv(assignments_v21_path)
    if "date_local" in assignments_v21.columns:
        assignments_v21 = assignments_v21.with_columns(pl.col("date_local").str.to_date())
    r2_v21 = pl.read_csv(r2_v21_path)

    v22_artifacts = build_regime_v22_calm_radiative_artifacts(
        assignments_v21,
        physical_matrix,
        min_assignment_rows=min_assignment_rows,
    )
    assignment_frame = v22_artifacts["regime_candidate_assignments_v2_2"]
    validation = validate_regime_candidate_r2(
        features_df,
        labels_df,
        assignment_frame,
        SEED_HYPOTHESES,
        cp_set=parsed_cp_set,
        test_starts=test_starts,
    )
    v21_regimes = (
        tuple(sorted(str(value) for value in r2_v21["regime"].drop_nulls().unique().to_list()))
        if "regime" in r2_v21.columns
        else tuple(
            sorted(
                str(value)
                for value in assignments_v21["candidate_regime_label"].drop_nulls().unique().to_list()
            )
        )
    )
    v22_regimes = tuple(
        sorted(
            str(value) for value in assignment_frame["candidate_regime_label"].drop_nulls().unique().to_list()
        )
    )
    comparison = compare_regime_candidate_v21_v22(
        v21_r2=r2_v21,
        v22_r2=validation["regime_candidate_r2_validation"],
        v22_assignments=assignment_frame,
        v21_regimes=v21_regimes,
        v22_regimes=v22_regimes,
        min_assignment_rows=min_assignment_rows,
    )
    paths = write_regime_v22_calm_radiative_artifacts(
        {**v22_artifacts, **validation, **comparison},
        output_dir=output_dir,
    )
    comparison_frame = comparison["regime_candidate_v21_v22_comparison"]
    dead_count = int(comparison_frame["v22_dead_regimes"][0]) if comparison_frame.height else len(v22_regimes)
    calm_rows = (
        assignment_frame.filter(pl.col("macro_regime_label") == "macro_calm_radiative").height
        if assignment_frame.height
        else 0
    )
    print(f"v2.2 assignments: {assignment_frame.height}")
    print(f"v2.2 calm/radiative rows: {calm_rows}")
    print(f"v2.2 dead macros: {dead_count}")
    print(f"v2.2 reassignment audit: {paths['regime_calm_radiative_reassignment_audit_md']}")
    print(f"v2.2 validation report: {paths['regime_candidate_v22_validation_report_md']}")


@app.command("regime-design-v23-calm-diagnostics")
def regime_design_v23_calm_diagnostics(
    assignments_v22_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_2.csv",
        help="Path to Regime Ontology v2.2 assignment CSV",
    ),
    r2_v22_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation_v2_2.csv",
        help="Path to Regime Ontology v2.2 R2 validation CSV",
    ),
    features_path: str = typer.Option(
        "./data/features.parquet",
        help="Path to features parquet",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        help="Path to labels parquet",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for v2.3 calm/radiative diagnostics",
    ),
    min_assignment_rows: int = typer.Option(
        30,
        help="Minimum assignment rows for macro support",
    ),
    min_cp_rows: int = typer.Option(
        30,
        help="Minimum rows in the smallest CP slice for macro support",
    ),
):
    """Explain the v2.2 calm/radiative R2 blocker with experiment-only artifacts."""
    required_paths = [
        Path(assignments_v22_path),
        Path(r2_v22_path),
        Path(features_path),
        Path(labels_path),
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    assignments = pl.read_csv(assignments_v22_path)
    r2_validation = pl.read_csv(r2_v22_path)
    features_df = pl.read_parquet(features_path)
    labels_df = pl.read_parquet(labels_path)
    artifacts = build_regime_v23_calm_failure_diagnostics(
        assignments=assignments,
        r2_validation=r2_validation,
        features=features_df,
        labels=labels_df,
        min_assignment_rows=min_assignment_rows,
        min_cp_rows=min_cp_rows,
    )
    paths = write_regime_v23_calm_failure_diagnostics_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    diagnostics = artifacts["regime_calm_radiative_failure_diagnostics_v1"]
    calm = diagnostics.filter(pl.col("macro_regime_label") == "macro_calm_radiative")
    calm_row = calm.row(0, named=True) if calm.height else {}
    print(f"v2.3 calm/radiative diagnosis: {calm_row.get('diagnosis', '')}")
    print(f"v2.3 calm/radiative rows: {calm_row.get('assignment_rows', 0)}")
    print(f"v2.3 calm/radiative R2 pass rows: {calm_row.get('r2_pass_rows', 0)}")
    print(f"v2.3 calm/radiative diagnostics report: {paths['regime_calm_radiative_failure_diagnostics_md']}")


@app.command("regime-design-v23-calm-target-diagnostics")
def regime_design_v23_calm_target_diagnostics(
    assignments_v22_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_2.csv",
        help="Path to Regime Ontology v2.2 assignment CSV",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        help="Path to labels parquet",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for CEXP calm/radiative target diagnostics",
    ),
    train_end: str = typer.Option(
        "2025-12-31",
        help="Inclusive train-window end date YYYY-MM-DD",
    ),
    min_cell_rows: int = typer.Option(
        30,
        help="Minimum rows for a macro x month x CP target cell",
    ),
):
    """Write CEXP-CALM-RADIATIVE-001 target diagnostics."""
    required_paths = [Path(assignments_v22_path), Path(labels_path)]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    assignments = pl.read_csv(assignments_v22_path)
    labels_df = pl.read_parquet(labels_path)
    train_end_date = dt.date.fromisoformat(train_end)
    artifacts = build_regime_calm_radiative_target_diagnostics(
        assignments=assignments,
        labels=labels_df,
        train_end=train_end_date,
        min_cell_rows=min_cell_rows,
    )
    paths = write_regime_calm_radiative_target_diagnostics_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    diagnostics = artifacts["regime_calm_radiative_target_diagnostics_v1"]
    calm_rows = diagnostics.filter(pl.col("macro_regime_label") == "macro_calm_radiative").height
    print("CEXP-CALM-RADIATIVE-001 target diagnostics complete.")
    print(f"Diagnostic rows: {diagnostics.height}")
    print(f"Calm/radiative target cells: {calm_rows}")
    print(f"Target diagnostics report: {paths['regime_calm_radiative_target_diagnostics_md']}")


@app.command("regime-design-v23-calm-feature-hypotheses")
def regime_design_v23_calm_feature_hypotheses(
    assignments_v22_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_2.csv",
        help="Path to Regime Ontology v2.2 assignment CSV",
    ),
    features_path: str = typer.Option(
        "./data/features.parquet",
        help="Path to features parquet",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        help="Path to labels parquet",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for CEXP calm/radiative feature hypotheses",
    ),
    train_end: str = typer.Option(
        "2025-12-31",
        help="Inclusive train-window end date YYYY-MM-DD",
    ),
    candidate_features: str = typer.Option(
        (
            "cloud_base_transparency,nocturnal_plateau_flag,"
            "dewpoint_depression,cloud_cover_suppression,pressure_trend_3h,"
            "warming_rate_06_09,dewpoint_collapse_rate_3h,sst_maritime_cap"
        ),
        help="Comma-separated candidate feature columns to screen",
    ),
    min_rows: int = typer.Option(
        30,
        help="Minimum train-window rows for a feature screen",
    ),
    min_abs_corr: float = typer.Option(
        0.2,
        help="Minimum absolute Pearson correlation for CANDIDATE_SIGNAL",
    ),
):
    """Write CEXP-CALM-RADIATIVE-002 feature-hypothesis diagnostics."""
    required_paths = [Path(assignments_v22_path), Path(features_path), Path(labels_path)]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    parsed_features = tuple(feature.strip() for feature in candidate_features.split(",") if feature.strip())
    if not parsed_features:
        print("ERROR: --candidate-features must include at least one feature")
        raise typer.Exit(2)

    assignments = pl.read_csv(assignments_v22_path)
    features_df = pl.read_parquet(features_path)
    labels_df = pl.read_parquet(labels_path)
    train_end_date = dt.date.fromisoformat(train_end)
    artifacts = build_regime_calm_radiative_feature_hypotheses(
        assignments=assignments,
        features=features_df,
        labels=labels_df,
        train_end=train_end_date,
        candidate_features=parsed_features,
        min_rows=min_rows,
        min_abs_corr=min_abs_corr,
    )
    paths = write_regime_calm_radiative_feature_hypotheses_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    diagnostics = artifacts["regime_calm_radiative_feature_hypotheses_v1"]
    signals = diagnostics.filter(pl.col("recommended_disposition") == "CANDIDATE_SIGNAL").height
    print("CEXP-CALM-RADIATIVE-002 feature hypotheses complete.")
    print(f"Candidate features screened: {diagnostics.height}")
    print(f"Candidate signals: {signals}")
    print(f"Feature hypotheses report: {paths['regime_calm_radiative_feature_hypotheses_md']}")


@app.command("regime-design-v23-calm-cloud-validation")
def regime_design_v23_calm_cloud_validation(
    assignments_v22_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_2.csv",
        help="Path to Regime Ontology v2.2 assignment CSV",
    ),
    features_path: str = typer.Option(
        "./data/features.parquet",
        help="Path to features parquet",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        help="Path to labels parquet",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for CEXP calm/radiative cloud validation",
    ),
    train_end: str = typer.Option(
        "2025-12-31",
        help="Inclusive train-window end date YYYY-MM-DD",
    ),
    min_rows: int = typer.Option(
        30,
        help="Minimum train-window rows for signal validation",
    ),
    min_cell_rows: int = typer.Option(
        30,
        help="Minimum rows for each CP or month x CP stability cell",
    ),
    min_abs_corr: float = typer.Option(
        0.2,
        help="Minimum absolute overall Pearson correlation",
    ),
    min_cp_negative_share: float = typer.Option(
        0.75,
        help="Minimum share of CP cells with negative cloud-cover slope",
    ),
    min_cell_negative_share: float = typer.Option(
        0.75,
        help="Minimum share of month x CP cells with negative cloud-cover slope",
    ),
    min_controlled_slope_retention: float = typer.Option(
        0.4,
        help="Minimum retained slope magnitude after physical controls",
    ),
    max_proxy_abs_corr: float = typer.Option(
        0.8,
        help="Maximum allowed absolute correlation with proxy/leakage checks",
    ),
):
    """Write CEXP-CALM-RADIATIVE-002B cloud signal validation artifacts."""
    required_paths = [Path(assignments_v22_path), Path(features_path), Path(labels_path)]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    assignments = pl.read_csv(assignments_v22_path)
    features_df = pl.read_parquet(features_path)
    labels_df = pl.read_parquet(labels_path)
    train_end_date = dt.date.fromisoformat(train_end)
    artifacts = build_regime_calm_radiative_cloud_signal_validation(
        assignments=assignments,
        features=features_df,
        labels=labels_df,
        train_end=train_end_date,
        min_rows=min_rows,
        min_cell_rows=min_cell_rows,
        min_abs_corr=min_abs_corr,
        min_cp_negative_share=min_cp_negative_share,
        min_cell_negative_share=min_cell_negative_share,
        min_controlled_slope_retention=min_controlled_slope_retention,
        max_proxy_abs_corr=max_proxy_abs_corr,
    )
    paths = write_regime_calm_radiative_cloud_signal_validation_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    validation = artifacts["regime_calm_radiative_cloud_signal_validation_v1"]
    row = validation.row(0, named=True) if validation.height else {}
    print("CEXP-CALM-RADIATIVE-002B cloud signal validation complete.")
    print(f"Decision: {row.get('validation_decision', '')}")
    print(f"Next experiment: {row.get('next_experiment', '')}")
    if "regime_calm_radiative_demote_split_v1" in artifacts:
        print(
            f"CEXP-CALM-RADIATIVE-003 demote/split matrix: {paths['regime_calm_radiative_demote_split_csv']}"
        )
    print(f"Cloud signal validation report: {paths['regime_calm_radiative_cloud_signal_validation_md']}")


@app.command("foundation-experiments")
def foundation_experiments(
    onda2e_dir: str = typer.Option(
        "./reports/onda2e",
        help="Path to Onda 2E artifact directory",
    ),
    regime_design_dir: str = typer.Option(
        "./reports/regime-design",
        help="Path to regime-design artifact directory",
    ),
    output_dir: str = typer.Option(
        "./reports/foundation-experiments",
        "--output-dir",
        help="Output directory for foundation experiment catalog artifacts",
    ),
):
    """Write the experiment-only catalog that bridges Onda 2E evidence to implementation."""
    try:
        inputs = load_foundation_experiment_inputs(
            onda2e_dir=onda2e_dir,
            regime_design_dir=regime_design_dir,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise typer.Exit(2) from exc

    artifacts = build_foundation_experiment_catalog(
        decision_register=inputs["decision_register"],
        regime_design_queue=inputs["regime_design_queue"],
        quarantined_baselines=inputs["quarantined_baselines"],
        rejection_register=inputs.get("rejection_register"),
        domain_eda_next_experiments=inputs.get("domain_eda_next_experiments"),
        foehn_repair_candidates=inputs.get("foehn_repair_candidates"),
        wind_repair_candidates=inputs.get("wind_repair_candidates"),
        regime_candidate_r2_validation=inputs.get("regime_candidate_r2_validation"),
        optional_artifact_warnings=inputs.get("optional_artifact_warnings"),
    )
    paths = write_foundation_experiment_catalog_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    catalog = artifacts["foundation_experiment_catalog"]
    warnings = artifacts["foundation_experiment_warnings"]
    print(f"Foundation experiment rows: {catalog.height}")
    print(f"Optional artifact warnings: {warnings.height}")
    print(f"Catalog CSV: {paths['foundation_experiment_catalog_csv']}")
    print(f"Catalog Markdown: {paths['foundation_experiment_catalog_md']}")


@app.command("foundation-experiment-results")
def foundation_experiment_results(
    catalog_path: str = typer.Option(
        "./reports/foundation-experiments/foundation_experiment_catalog_v1.csv",
        help="Path to foundation experiment catalog CSV",
    ),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    features_path: str | None = typer.Option(
        None,
        "--features-path",
        help="Optional path to features parquet for feature-probe experiments.",
    ),
    assignments_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v1.csv",
        help="Path to candidate regime assignments CSV",
    ),
    regime_candidate_r2_path: str | None = typer.Option(
        None,
        "--regime-candidate-r2-path",
        help=(
            "Optional path to candidate R2 validation CSV for dead-regime experiments. "
            "If omitted, the default reports/regime-design path is used when present."
        ),
    ),
    regime_candidate_v2_comparison_path: str | None = typer.Option(
        None,
        "--regime-candidate-v2-comparison-path",
        help="Optional path to v1-v2 regime comparison CSV for dead-regime experiments.",
    ),
    regime_candidate_v21_comparison_path: str | None = typer.Option(
        None,
        "--regime-candidate-v21-comparison-path",
        help="Optional path to v2-v2.1 regime comparison CSV for dead-regime experiments.",
    ),
    output_dir: str = typer.Option(
        "./reports/foundation-experiments",
        "--output-dir",
        help="Output directory for foundation experiment result artifacts",
    ),
    cp_set: str = typer.Option(
        "20:00,21:00,22:00,23:00",
        help="Comma-separated CP set",
    ),
    test_start: str | None = typer.Option(
        None,
        "--test-start",
        help="Comma-separated walk-forward test-start dates YYYY-MM-DD",
    ),
    test_length_days: int = typer.Option(365, help="Number of days in each test split"),
    min_cell_rows: int = typer.Option(30, help="Minimum train rows per candidate cell"),
    n_bootstrap: int = typer.Option(1000, help="Bootstrap resamples for MAE-delta CI"),
):
    """Run experiment-only baseline results from the Foundation Experiment Catalog."""
    catalog_file = Path(catalog_path)
    labels_file = Path(labels_path)
    assignments_file = Path(assignments_path)
    for path, label in (
        (catalog_file, "foundation experiment catalog"),
        (labels_file, "labels"),
        (assignments_file, "candidate assignments"),
    ):
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            raise typer.Exit(2)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    test_starts = (
        [dt.date.fromisoformat(value.strip()) for value in test_start.split(",") if value.strip()]
        if test_start
        else None
    )
    catalog = pl.read_csv(catalog_file)
    labels = pl.read_parquet(labels_file)
    features_frame = None
    if features_path is not None:
        features_file = Path(features_path)
        if not features_file.exists():
            print(f"ERROR: features file not found: {features_file}")
            raise typer.Exit(2)
        features_frame = pl.read_parquet(features_file)
    assignments = pl.read_csv(assignments_file)
    if regime_candidate_r2_path is None:
        default_r2_file = Path("./reports/regime-design/regime_candidate_r2_validation.csv")
        regime_candidate_r2 = pl.read_csv(default_r2_file) if default_r2_file.exists() else None
    else:
        r2_file = Path(regime_candidate_r2_path)
        if not r2_file.exists():
            print(f"ERROR: candidate R2 validation file not found: {r2_file}")
            raise typer.Exit(2)
        regime_candidate_r2 = pl.read_csv(r2_file)
    if regime_candidate_v2_comparison_path is None:
        regime_candidate_v2_comparison = None
    else:
        comparison_file = Path(regime_candidate_v2_comparison_path)
        if not comparison_file.exists():
            print(f"ERROR: v2 comparison file not found: {comparison_file}")
            raise typer.Exit(2)
        regime_candidate_v2_comparison = pl.read_csv(comparison_file)
    if regime_candidate_v21_comparison_path is None:
        regime_candidate_v21_comparison = None
    else:
        comparison_file = Path(regime_candidate_v21_comparison_path)
        if not comparison_file.exists():
            print(f"ERROR: v2.1 comparison file not found: {comparison_file}")
            raise typer.Exit(2)
        regime_candidate_v21_comparison = pl.read_csv(comparison_file)
    try:
        artifacts = build_foundation_experiment_results(
            catalog=catalog,
            labels=labels,
            candidate_assignments=assignments,
            features=features_frame,
            regime_candidate_r2_validation=regime_candidate_r2,
            regime_candidate_v21_comparison=regime_candidate_v21_comparison,
            regime_candidate_v2_comparison=regime_candidate_v2_comparison,
            cp_set=parsed_cp_set,
            test_starts=test_starts,
            test_length_days=test_length_days,
            min_cell_rows=min_cell_rows,
            n_bootstrap=n_bootstrap,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        raise typer.Exit(2) from exc
    paths = write_foundation_experiment_result_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    results = artifacts["foundation_experiment_results"]
    completed = results.filter(pl.col("status") != "not_run").height
    print(f"Foundation experiment result rows: {results.height}")
    print(f"Runnable rows completed: {completed}")
    print(f"Results CSV: {paths['foundation_experiment_results_csv']}")
    print(f"Results Markdown: {paths['foundation_experiment_results_md']}")


@app.command("eda-feature-candidate-review")
def eda_feature_candidate_review(
    catalog_path: str = typer.Option(
        "./reports/foundation-experiments/foundation_experiment_catalog_v1.csv",
        help="Path to foundation experiment catalog CSV",
    ),
    results_path: str | None = typer.Option(
        "./reports/foundation-experiments/foundation_experiment_results_v1.csv",
        help="Optional path to foundation experiment results CSV",
    ),
    feature_candidate_queue_path: str | None = typer.Option(
        "./reports/onda2e/feature_candidate_queue.csv",
        help="Optional path to Onda 2E feature candidate queue CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/foundation-experiments",
        "--output-dir",
        help="Output directory for EDA feature candidate review artifacts",
    ),
):
    """Write the experiment-only review that maps EDA evidence to feature work."""
    catalog_file = Path(catalog_path)
    if not catalog_file.exists():
        print(f"ERROR: foundation experiment catalog file not found: {catalog_file}")
        raise typer.Exit(2)

    catalog = pl.read_csv(catalog_file)
    results = None
    if results_path:
        result_file = Path(results_path)
        if not result_file.exists():
            print(f"ERROR: foundation experiment results file not found: {result_file}")
            raise typer.Exit(2)
        results = pl.read_csv(result_file)

    feature_queue = None
    if feature_candidate_queue_path:
        queue_file = Path(feature_candidate_queue_path)
        if not queue_file.exists():
            print(f"ERROR: feature candidate queue file not found: {queue_file}")
            raise typer.Exit(2)
        feature_queue = pl.DataFrame() if queue_file.stat().st_size == 0 else pl.read_csv(queue_file)

    try:
        artifacts = build_eda_feature_candidate_review(
            catalog=catalog,
            results=results,
            feature_candidate_queue=feature_queue,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        raise typer.Exit(2) from exc
    paths = write_eda_feature_candidate_review_artifacts(
        artifacts,
        output_dir=output_dir,
    )
    review = artifacts["eda_feature_candidate_review"]
    feature_rows = review.filter(pl.col("eda_feature_disposition") == "feature_ready_experiment").height
    print(f"EDA feature review rows: {review.height}")
    print(f"Feature-ready experiment rows: {feature_rows}")
    print(f"Review CSV: {paths['eda_feature_candidate_review_csv']}")
    print(f"Review Markdown: {paths['eda_feature_candidate_review_md']}")


@app.command("onda2e")
def onda2e(
    atlas_path: str = typer.Option(
        "./reports/onda2e/thesis_atlas_v1.md",
        help="Official Onda 2E thesis atlas markdown",
    ),
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    obs_path: str | None = typer.Option("./data/obs.parquet", help="Path to obs parquet"),
    output_dir: str = typer.Option("./reports/onda2e", help="Output directory"),
    tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
):
    """Run Onda 2E prerequisite EDA from the official thesis atlas."""
    atlas_file = Path(atlas_path)
    features_file = Path(features_path)
    labels_file = Path(labels_path)
    if not atlas_file.exists():
        print(f"ERROR: thesis atlas not found: {atlas_file}")
        raise typer.Exit(2)
    if not features_file.exists():
        print(f"ERROR: features parquet not found: {features_file}")
        raise typer.Exit(2)
    if not labels_file.exists():
        print(f"ERROR: labels parquet not found: {labels_file}")
        raise typer.Exit(2)
    obs_file = Path(obs_path) if obs_path else None
    if obs_file is not None and not obs_file.exists():
        print(f"ERROR: obs parquet not found: {obs_file}")
        raise typer.Exit(2)

    theses = parse_thesis_atlas(atlas_file)
    testability = thesis_testability_audit(theses)
    features_df = pl.read_parquet(features_file)
    labels_df = pl.read_parquet(labels_file)
    obs_df = pl.read_parquet(obs_file) if obs_file is not None else None
    artifacts = build_prerequisite_artifacts(
        features_df,
        labels_df,
        obs=obs_df,
        tz_name=tz_name,
    )
    paths = write_onda2e_artifacts(
        theses=theses,
        testability=testability,
        artifacts=artifacts,
        output_dir=output_dir,
        source_atlas=atlas_file,
    )
    timing_artifacts = build_timing_domain_artifacts(features_df, labels_df)
    timing_paths = write_timing_domain_artifacts(
        timing_artifacts,
        output_dir=output_dir,
    )
    timing_decisions = build_timing_decision_updates(timing_artifacts)
    cooling_artifacts = (
        build_cooling_domain_artifacts(
            features_df,
            labels_df,
            obs_df,
            tz_name=tz_name,
        )
        if obs_df is not None
        else None
    )
    cooling_paths = (
        write_cooling_domain_artifacts(cooling_artifacts, output_dir=output_dir)
        if cooling_artifacts is not None
        else {}
    )
    cooling_decisions = (
        build_cooling_decision_updates(cooling_artifacts)
        if cooling_artifacts is not None
        else pl.DataFrame(schema=timing_decisions.schema)
    )
    foehn_artifacts = build_foehn_domain_artifacts(features_df, labels_df)
    foehn_paths = write_foehn_domain_artifacts(
        foehn_artifacts,
        output_dir=output_dir,
    )
    foehn_decisions = build_foehn_decision_updates(foehn_artifacts)
    wind_artifacts = (
        build_wind_domain_artifacts(
            features_df,
            labels_df,
            obs_df,
            tz_name=tz_name,
        )
        if obs_df is not None
        else None
    )
    wind_paths = (
        write_wind_domain_artifacts(wind_artifacts, output_dir=output_dir)
        if wind_artifacts is not None
        else {}
    )
    wind_decisions = (
        build_wind_decision_updates(wind_artifacts)
        if wind_artifacts is not None
        else pl.DataFrame(schema=timing_decisions.schema)
    )
    decision_gate = build_decision_gate_artifacts(
        theses,
        testability,
        prereq_artifacts=artifacts,
    )
    thesis_domain_artifacts = build_thesis_domain_eda_artifacts(
        theses,
        testability,
        features_df,
        labels_df,
        obs_df,
        tz_name=tz_name,
    )
    thesis_domain_decisions = build_thesis_domain_eda_decision_updates(thesis_domain_artifacts)
    decision_gate = apply_decision_updates(decision_gate, thesis_domain_decisions)
    removed_external_ids = set(
        thesis_domain_artifacts["removed_external_theses"].get_column("thesis_id").to_list()
    )
    if removed_external_ids:
        decision_gate = remove_decision_items(
            decision_gate,
            removed_external_ids,
            item_type="thesis",
        )
    active_theses = [thesis for thesis in theses if thesis.id not in removed_external_ids]
    active_testability = testability.filter(~pl.col("id").is_in(removed_external_ids))
    decision_gate = apply_decision_updates(decision_gate, timing_decisions)
    decision_gate = apply_decision_updates(decision_gate, cooling_decisions)
    decision_gate = apply_decision_updates(decision_gate, foehn_decisions)
    decision_gate = apply_decision_updates(decision_gate, wind_decisions)
    thesis_domain_paths = write_thesis_domain_eda_artifacts(
        thesis_domain_artifacts,
        output_dir=output_dir,
    )
    full_eda_paths = {}
    full_eda_artifacts = None
    if obs_df is not None:
        full_eda_artifacts = build_full_eda_artifacts(
            active_theses,
            active_testability,
            decision_gate["evidence_decision_register"],
            features_df,
            labels_df,
            obs_df,
            tz_name=tz_name,
        )
        regime_decisions = build_regime_design_decision_updates(full_eda_artifacts)
        decision_gate = apply_decision_updates(decision_gate, regime_decisions)
        full_eda_artifacts = refresh_full_eda_decision_review(
            full_eda_artifacts,
            active_theses,
            active_testability,
            decision_gate["evidence_decision_register"],
        )
        full_eda_paths = write_full_eda_artifacts(
            full_eda_artifacts,
            output_dir=output_dir,
        )
    decision_paths = write_decision_gate_artifacts(
        decision_gate,
        output_dir=output_dir,
    )

    blocked = testability.filter(pl.col("testability") == "blocked_external_data").height
    print(f"Onda 2E theses parsed: {len(theses)}")
    print(f"External-data blocked theses: {blocked}")
    print(f"Registry: {paths['registry_csv']}")
    print(f"Testability audit: {paths['testability_csv']}")
    print(f"Report: {paths['report_md']}")
    print(f"Timing report: {timing_paths['timing_report_md']}")
    if cooling_paths:
        print(f"Cooling report: {cooling_paths['cooling_report_md']}")
    print(f"FOEHN report: {foehn_paths['foehn_report_md']}")
    if wind_paths:
        print(f"Wind report: {wind_paths['wind_report_md']}")
    print(f"Thesis-domain EDA report: {thesis_domain_paths['thesis_domain_report_md']}")
    print(f"Decision register: {decision_paths['evidence_decision_register_csv']}")
    print(f"Decision report: {decision_paths['decision_report_md']}")
    if full_eda_paths:
        print(f"Full EDA report: {full_eda_paths['full_eda_report_md']}")
        print(f"Regime architecture report: {full_eda_paths['regime_architecture_report_md']}")
        print(f"Regime design candidate: {full_eda_paths['regime_design_candidate_md']}")


@app.command("regime-classifiability-benchmark")
def regime_classifiability_benchmark(
    features_path: str = typer.Option(
        "./data/features.parquet",
        help="Path to features candidate parquet",
    ),
    labels_path: str | None = typer.Option(
        None,
        "--labels-path",
        help="Path to labels parquet for physical feature-basis reconstruction.",
    ),
    obs_path: str | None = typer.Option(
        None,
        "--obs-path",
        help="Path to obs parquet for physical feature-basis reconstruction.",
    ),
    basis_mode: str = typer.Option(
        "physical",
        "--basis-mode",
        help="Feature basis mode: physical or precomputed.",
    ),
    tz_name: str = typer.Option(TZ_NAME, help="IANA timezone name"),
    assignments_v2_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2.csv",
        help="Path to v2 candidate assignments CSV",
    ),
    assignments_v21_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_1.csv",
        "--assignments-v21-path",
        "--candidate-under-review-assignments-path",
        help="Path to candidate-under-review assignments CSV",
    ),
    candidate_v2_path: str = typer.Option(
        "./reports/onda2e/regime_design_candidate_v2.csv",
        help="Path to candidate v2 ontology CSV",
    ),
    comparison_v21_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_v2_v21_comparison.csv",
        "--comparison-v21-path",
        "--candidate-under-review-comparison-path",
        help="Path to candidate-under-review comparison CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-classifiability",
        help="Output directory for classifiability report/CSVs",
    ),
    train_end: str = typer.Option("2025-12-31", help="Train fold end date (YYYY-MM-DD)"),
    test_start: str = typer.Option("2026-01-01", help="Test fold start date (YYYY-MM-DD)"),
    candidate_under_review_version: str = typer.Option(
        "v2.1",
        "--candidate-under-review-version",
        help="Candidate version evaluated by Onda C",
    ),
    candidate_under_review_method: str = typer.Option(
        "distance_softmax_v21",
        "--candidate-under-review-method",
        help="Method label for candidate-under-review baseline rows",
    ),
    protected_macros_csv: str = typer.Option(
        "macro_nw_continuum,macro_southerly_flow",
        "--protected-macros",
        help="Comma-separated protected macros for candidate-under-review",
    ),
    comparison_dead_count_column: str = typer.Option(
        "v21_dead_regimes",
        "--comparison-dead-count-column",
        help="Dead-regime count column in candidate-under-review comparison CSV",
    ),
    allow_blocked_candidate_for_onda_c: bool = typer.Option(
        False,
        "--allow-blocked-candidate-for-onda-c",
        help="Write an Onda C BLOCK report even when the candidate comparison gate is not ready",
    ),
):
    """Run non-production scientific validation wave to check regime classifiability."""
    features_input = pl.read_parquet(features_path)
    if basis_mode == "physical":
        if labels_path is None or obs_path is None:
            print("ERROR: --labels-path and --obs-path are required for physical basis mode")
            raise typer.Exit(2)
        labels_file = Path(labels_path)
        obs_file = Path(obs_path)
        if not labels_file.exists():
            print(f"ERROR: labels parquet not found: {labels_file}")
            raise typer.Exit(2)
        if not obs_file.exists():
            print(f"ERROR: obs parquet not found: {obs_file}")
            raise typer.Exit(2)
        labels_df = pl.read_parquet(labels_file)
        obs_df = pl.read_parquet(obs_file)
        features = _build_cluster_matrix(
            features_input,
            labels_df,
            obs_df,
            tz_name=tz_name,
        )
        if features.height == 0:
            print("ERROR: physical classifiability matrix is empty")
            raise typer.Exit(2)
    elif basis_mode == "precomputed":
        features = features_input
    else:
        print(f"ERROR: unsupported --basis-mode: {basis_mode}")
        raise typer.Exit(2)

    assignments_v2 = pl.read_csv(assignments_v2_path)
    if "date_local" in assignments_v2.columns:
        assignments_v2 = assignments_v2.with_columns(pl.col("date_local").str.to_date())

    assignments_v21 = pl.read_csv(assignments_v21_path)
    if "date_local" in assignments_v21.columns:
        assignments_v21 = assignments_v21.with_columns(pl.col("date_local").str.to_date())

    candidate_v2 = pl.read_csv(candidate_v2_path)
    comparison_v21 = pl.read_csv(comparison_v21_path)

    t_end = dt.date.fromisoformat(train_end)
    t_start = dt.date.fromisoformat(test_start)

    artifacts = build_regime_classifiability_artifacts(
        features=features,
        assignments_v2=assignments_v2,
        assignments_v21=assignments_v21,
        candidate_v2=candidate_v2,
        comparison_v21=comparison_v21,
        train_end=t_end,
        test_start=t_start,
        candidate_under_review_version=candidate_under_review_version,
        candidate_under_review_method=candidate_under_review_method,
        protected_macros=tuple(part.strip() for part in protected_macros_csv.split(",") if part.strip()),
        comparison_dead_count_column=comparison_dead_count_column,
        allow_blocked_candidate_for_onda_c=allow_blocked_candidate_for_onda_c,
    )

    paths = write_regime_classifiability_artifacts(
        artifacts,
        output_dir=output_dir,
        today=dt.date.today(),
    )

    print("Onda C Classifiability Benchmark complete.")
    print(f"Written assignments: {paths['assignments_csv']}")
    print(f"Written metrics: {paths['metrics_csv']}")
    print(f"Written comparison: {paths['comparison_csv']}")
    print(f"Written diagnostics: {paths['diagnostics_csv']}")
    print(f"Written report: {paths['report_md']}")


@app.command("regime-deadlock-pivot")
def regime_deadlock_pivot(
    r2_validation_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_r2_validation_v2_2.csv",
        help="Path to v2.2 R2 validation CSV",
    ),
    cloud_validation_path: str = typer.Option(
        "./reports/regime-design/regime_calm_radiative_cloud_signal_validation_v1.csv",
        help="Path to CEXP-002B cloud validation CSV",
    ),
    source_report_path: str = typer.Option(
        "./reports/onda2e/regime_deadlock_diagnosis_v1.md",
        help="Path to the deadlock diagnosis report",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for pivot artifacts",
    ),
):
    """Write the regime-deadlock pivot decision and audit-demotion artifacts."""
    required = [Path(r2_validation_path), Path(source_report_path)]
    missing = [path for path in required if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)
    cloud_path = Path(cloud_validation_path)
    r2_validation = pl.read_csv(r2_validation_path)
    cloud_validation = pl.read_csv(cloud_path) if cloud_path.exists() else pl.DataFrame()
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=r2_validation,
        cloud_validation=cloud_validation,
        source_report_path=source_report_path,
    )
    paths = write_regime_deadlock_pivot_artifacts(artifacts, output_dir=output_dir)
    decision = artifacts["regime_deadlock_pivot_decision_v1"].row(0, named=True)
    print(f"Regime deadlock pivot: {decision['decision_status']}")
    print(f"Active path: {decision['active_path']}")
    print(f"Pivot report: {paths['regime_deadlock_pivot_decision_md']}")


@app.command("regime-binary-macro-candidate")
def regime_binary_macro_candidate(
    assignments_path: str = typer.Option(
        "./reports/regime-design/regime_candidate_assignments_v2_2.csv",
        help="Path to non-production source regime assignments",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for binary macro candidate artifacts",
    ),
):
    """Write experiment-only binary macro regime candidate artifacts."""
    path = Path(assignments_path)
    if not path.exists():
        print(f"ERROR: missing input file: {path}")
        raise typer.Exit(2)
    artifacts = build_regime_binary_macro_candidate_artifacts(pl.read_csv(path))
    paths = write_regime_binary_macro_candidate_artifacts(artifacts, output_dir=output_dir)
    candidate = artifacts["regime_binary_macro_candidate_v1"]
    labels = ", ".join(candidate["macro_regime_label"].to_list())
    print(f"Binary macro labels: {labels}")
    print(f"Binary macro report: {paths['regime_binary_macro_candidate_md']}")


@app.command("cloud-cover-baseline-experiment")
def cloud_cover_baseline_experiment(
    features_path: str = typer.Option("./data/features.parquet", help="Path to features parquet"),
    labels_path: str = typer.Option("./data/labels.parquet", help="Path to labels parquet"),
    output_dir: str = typer.Option("./reports/regime-design", help="Output directory"),
    test_years: str = typer.Option("2024,2025", help="Comma-separated walk-forward test years"),
    cp_set: str = typer.Option("20:00,21:00,22:00,23:00", help="Comma-separated CP set"),
):
    """Write experiment-only cloud-cover baseline comparison artifacts."""
    required = [Path(features_path), Path(labels_path)]
    missing = [path for path in required if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)
    years = tuple(int(value.strip()) for value in test_years.split(",") if value.strip())
    cps = tuple(value.strip() for value in cp_set.split(",") if value.strip())
    artifacts = build_cloud_cover_baseline_experiment(
        features=pl.read_parquet(features_path),
        labels=pl.read_parquet(labels_path),
        test_years=years,
        cp_set=cps,
    )
    paths = write_cloud_cover_baseline_experiment_artifacts(artifacts, output_dir=output_dir)
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    print(f"Cloud-cover experiment rows: {results.height}")
    print("Feature: cloud_cover_suppression")
    print(f"Cloud-cover report: {paths['cloud_cover_baseline_experiment_md']}")


@app.command("regime-binary-macro-validation")
def regime_binary_macro_validation(
    assignments_path: str = typer.Option(
        "./reports/regime-design/regime_binary_macro_assignments_v1.csv",
        help="Path to Regime Binary Macro assignments CSV",
    ),
    features_path: str = typer.Option(
        "./data/features.parquet",
        help="Path to features parquet",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        help="Path to labels parquet",
    ),
    obs_path: str = typer.Option(
        "./data/obs.parquet",
        help="Path to obs parquet",
    ),
    output_dir: str = typer.Option(
        "./reports/regime-design",
        help="Output directory for validation artifacts",
    ),
    train_end: str = typer.Option(
        "2025-12-31",
        help="Inclusive train-window end date YYYY-MM-DD",
    ),
    test_start: str = typer.Option(
        "2026-01-01",
        help="Inclusive test-window start date YYYY-MM-DD",
    ),
    cp_set: str = typer.Option(
        "20:00,21:00,22:00,23:00",
        help="Comma-separated CP set",
    ),
):
    """Write experiment-only binary macro candidate validation artifacts."""
    required = [Path(assignments_path), Path(features_path), Path(labels_path), Path(obs_path)]
    missing = [path for path in required if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    assignments = pl.read_csv(assignments_path)
    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    obs = pl.read_parquet(obs_path)

    parsed_cp_set = tuple(part.strip() for part in cp_set.split(",") if part.strip())
    t_end = dt.date.fromisoformat(train_end)
    t_start = dt.date.fromisoformat(test_start)

    artifacts = validate_binary_macro_regimes(
        assignments=assignments,
        features=features,
        labels=labels,
        obs=obs,
        train_end=t_end,
        test_start=t_start,
        cp_set=parsed_cp_set,
        tz_name=TZ_NAME,
    )

    paths = write_binary_validation_reports(artifacts, output_dir=output_dir)
    decision = artifacts["regime_binary_macro_decision_update_v1"].row(0, named=True)
    print("Regime binary macro validation complete.")
    print(f"Decision Status: {decision['decision_status']}")
    print(f"R2 report: {paths['regime_binary_macro_r2_validation_md']}")
    print(f"Classifiability report: {paths['regime_binary_macro_classifiability_md']}")


@app.command("onda3-baseline-model")
def onda3_baseline_model(
    features_path: str = typer.Option(
        "./data/features.parquet",
        help="Path to features parquet",
    ),
    labels_path: str = typer.Option(
        "./data/labels.parquet",
        help="Path to labels parquet",
    ),
    binary_assignments_path: str = typer.Option(
        "./reports/regime-design/regime_binary_macro_assignments_v1.csv",
        help="Optional path to experiment-only binary macro assignments CSV",
    ),
    output_dir: str = typer.Option(
        "./reports/onda3",
        help="Output directory for Onda 3 baseline artifacts",
    ),
    train_end: str = typer.Option(
        "2024-12-31",
        help="Inclusive train-window end date YYYY-MM-DD",
    ),
    test_start: str = typer.Option(
        "2025-01-01",
        help="Inclusive test-window start date YYYY-MM-DD",
    ),
):
    """Write experiment-only Onda 3 baseline-first model artifacts."""
    required = [Path(features_path), Path(labels_path)]
    missing = [path for path in required if not path.exists()]
    if missing:
        print(f"ERROR: missing input files: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    assignment_file = Path(binary_assignments_path)
    binary_assignments = pl.read_csv(assignment_file) if assignment_file.exists() else None

    manifest = build_onda3_feature_manifest(features)
    matrix, audit = build_onda3_design_matrix(
        features=features,
        labels=labels,
        binary_assignments=binary_assignments,
        train_end=dt.date.fromisoformat(train_end),
        test_start=dt.date.fromisoformat(test_start),
    )
    feature_columns = [
        row["feature"]
        for row in manifest.filter(pl.col("included_in_onda3")).iter_rows(named=True)
        if row["feature"] in matrix.columns and matrix.schema[row["feature"]].is_numeric()
    ]
    results, uncertainty = run_onda3_baseline_model(
        matrix,
        feature_columns=feature_columns,
        target_column="tmax_int",
    )
    baseline_results = results.filter(pl.col("model_name") == "train_mean_null")
    challenger_results = results.filter(pl.col("model_name") == "ridge_challenger")
    slice_diagnostics = build_onda3_slice_diagnostics(
        matrix,
        slice_columns=["cp", "binary_macro_regime_label"],
    )
    challenger_beats = bool(
        challenger_results.select(pl.col("beats_train_mean_null").all()).item()
    )
    decision = pl.DataFrame(
        [
            {
                "decision_status": (
                    "READY_FOR_ONDA4_MODEL_RERUN"
                    if challenger_beats
                    else "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
                ),
                "decision_rationale": (
                    "Baseline-first Onda 3 experiment completed against train-only null."
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    paths = write_onda3_baseline_artifacts(
        {
            "onda3_feature_manifest_v1": manifest,
            "onda3_design_matrix_audit_v1": audit,
            "onda3_baseline_results_v1": baseline_results,
            "onda3_challenger_results_v1": challenger_results,
            "onda3_slice_diagnostics_v1": slice_diagnostics,
            "onda3_uncertainty_abstention_v1": uncertainty,
            "onda3_decision_update_v1": decision,
        },
        output_dir=Path(output_dir),
        today=dt.date.today(),
    )
    print(f"Onda 3 baseline model complete: {paths['onda3_report_md']}")


if __name__ == "__main__":
    app()
