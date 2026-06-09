"""Markdown report generation for Onda 4 robustness."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.robustness._config import (
    R1_BLOCK_YEARS,
    R1_MIN_PASSING_YEARS,
    ROBUSTNESS_CONFIG_VERSION,
)
from solarstorm.robustness._lead_time import detect_nowcast_only
from solarstorm.robustness._regime_analysis import detect_dead_regimes
from solarstorm.robustness._tmax_hour import (
    detect_fixed_cp_artifact,
    has_late_tmax_risk_baseline,
)


def evaluate_go_nogo(inputs: dict) -> str:
    """Return GO when no blocking Onda 4 criterion fails."""
    if int(inputs.get("n_passing_years", 0)) < R1_BLOCK_YEARS:
        return "NO-GO"
    if inputs.get("dead_regimes"):
        return "NO-GO"
    if inputs.get("causal_violations"):
        return "NO-GO"
    if inputs.get("gates_rerun_pass") is False:
        return "NO-GO"
    if inputs.get("lead_time_ok") is False:
        return "NO-GO"
    if inputs.get("fixed_cp_artifact") is True:
        return "NO-GO"
    if inputs.get("late_tmax_risk_baseline_exists") is False:
        return "NO-GO"
    return "GO"


def _bool_status(ok: bool, *, warning: bool = False) -> str:
    if ok:
        return "PASS"
    return "WARNING" if warning else "BLOCK"


def _n_passing_years(year_matrix: pl.DataFrame) -> int:
    if year_matrix.height == 0 or "passes_g1_g5" not in year_matrix.columns:
        return 0
    return year_matrix.filter(pl.col("passes_g1_g5").fill_null(False))["year"].n_unique()


def render_robustness_report(
    *,
    output_dir: str | Path,
    year_matrix: pl.DataFrame,
    regime_cross_tab: pl.DataFrame,
    drift_result: dict,
    causal_clean: list[str],
    causal_violating: list[str],
    lead_time_table: pl.DataFrame | None = None,
    tmax_hour_table: pl.DataFrame | None = None,
    late_spike_candidates: pl.DataFrame | None = None,
    gates_rerun_pass: bool = True,
    artifact_hashes: dict[str, str] | None = None,
    regime_set: tuple[str, ...] | None = None,
    today: dt.date | None = None,
) -> str:
    """Write the Onda 4 go/no-go report and return its path."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    report_path = out_dir / f"{report_date.isoformat()}-robustness-report.md"

    n_passing_years = _n_passing_years(year_matrix)
    dead_regimes = (
        detect_dead_regimes(regime_cross_tab, regimes=regime_set)
        if regime_set is not None
        else detect_dead_regimes(regime_cross_tab)
    )
    nowcast_only = detect_nowcast_only(lead_time_table) if lead_time_table is not None else True
    fixed_cp_artifact = (
        detect_fixed_cp_artifact(tmax_hour_table) if tmax_hour_table is not None else True
    )
    late_spike_artifact_produced = late_spike_candidates is not None
    late_tmax_risk_baseline_exists = (
        has_late_tmax_risk_baseline(tmax_hour_table)
        if tmax_hour_table is not None
        else False
    )

    verdict = evaluate_go_nogo(
        {
            "n_passing_years": n_passing_years,
            "dead_regimes": dead_regimes,
            "causal_violations": causal_violating,
            "gates_rerun_pass": gates_rerun_pass,
            "lead_time_ok": not nowcast_only,
            "fixed_cp_artifact": fixed_cp_artifact,
            "late_spike_artifact_produced": late_spike_artifact_produced,
            "late_tmax_risk_baseline_exists": late_tmax_risk_baseline_exists,
        }
    )

    lines: list[str] = [
        f"# Robustness Hardening Report - {report_date.isoformat()}",
        "",
        f"**Config version:** {ROBUSTNESS_CONFIG_VERSION}",
        f"**Generated:** {dt.datetime.now(dt.UTC).isoformat()}",
        f"**Verdict:** **{verdict}**",
        "",
    ]

    if artifact_hashes:
        lines += ["## Input Artifacts", ""]
        for name, digest in sorted(artifact_hashes.items()):
            lines.append(f"- **{name}:** sha256={digest}")
        lines.append("")

    lines += [
        "## 1. Per-Year Replication",
        "",
        f"Years with at least one passing feature: {n_passing_years}",
        f"Warning threshold: < {R1_MIN_PASSING_YEARS}; block threshold: < {R1_BLOCK_YEARS}",
        "",
        "| Year | Rows | Passing |",
        "|------|------|---------|",
    ]
    for year in sorted(year_matrix["year"].unique().to_list()) if year_matrix.height else []:
        subset = year_matrix.filter(pl.col("year") == year)
        passing = subset.filter(pl.col("passes_g1_g5").fill_null(False)).height
        lines.append(f"| {year} | {subset.height} | {passing} |")
    lines.append("")

    lines += [
        "## 2. Regime Sensitivity",
        "",
        f"Dead regimes: {', '.join(dead_regimes) if dead_regimes else 'None'}",
        "",
    ]

    lines += [
        "## 3. Drift Trend",
        "",
        f"Mann-Kendall S: {float(drift_result.get('trend_statistic', 0.0)):.2f}",
        f"p-value: {float(drift_result.get('p_value', 1.0)):.4f}",
        f"Warning: {bool(drift_result.get('warning', False))}",
        "",
    ]

    lines += [
        "## 4. Causal Firewall Re-Audit",
        "",
        f"Clean features: {len(causal_clean)}",
        f"Violations: {len(causal_violating)}",
        "",
    ]

    lines += [
        "## 5. Anti-Nowcast Lead-Time",
        "",
        f"Nowcast-only evidence: {nowcast_only}",
        "",
    ]

    lines += [
        "## 6. Month/Regime Tmax Timing Norms",
        "",
        f"Fixed-CP artifact detected: {fixed_cp_artifact}",
        f"Late-Tmax risk baseline exists: {late_tmax_risk_baseline_exists}",
        "",
    ]

    n_spikes = late_spike_candidates.height if late_spike_candidates is not None else 0
    lines += [
        "## 7. Late-Spike Evidence Pack",
        "",
        f"Late-spike candidates: {n_spikes}",
        "",
    ]

    r1_status = (
        "PASS"
        if n_passing_years >= R1_MIN_PASSING_YEARS
        else ("BLOCK" if n_passing_years < R1_BLOCK_YEARS else "WARNING")
    )
    lines += [
        "## 8. Go/No-Go Verdict",
        "",
        "| Criterion | Result | Severity |",
        "|-----------|--------|----------|",
        f"| R1: Per-year replication | {n_passing_years} passing years | {r1_status} |",
        f"| R2: Dead regimes | {', '.join(dead_regimes) if dead_regimes else 'None'} | {_bool_status(not dead_regimes)} |",
        f"| R3: Causal firewall | {len(causal_violating)} violations | {_bool_status(not causal_violating)} |",
        f"| R4: Drift trend | p={float(drift_result.get('p_value', 1.0)):.4f} | {_bool_status(not bool(drift_result.get('warning', False)), warning=True)} |",
        f"| R5: Fresh gate re-run | {gates_rerun_pass} | {_bool_status(gates_rerun_pass)} |",
        f"| R6: Anti-nowcast lead-time | {not nowcast_only} | {_bool_status(not nowcast_only)} |",
        f"| R7: Month/regime Tmax timing norms | artifact={fixed_cp_artifact} | {_bool_status(not fixed_cp_artifact)} |",
        f"| R8: Late-spike evidence pack | produced={late_spike_artifact_produced} | {_bool_status(late_spike_artifact_produced, warning=True)} |",
        f"| R9: Late-Tmax risk baseline | exists={late_tmax_risk_baseline_exists} | {_bool_status(late_tmax_risk_baseline_exists)} |",
        "",
        f"Final verdict: **{verdict}**",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)
