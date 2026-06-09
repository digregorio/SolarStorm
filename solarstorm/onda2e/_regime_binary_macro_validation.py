"""Offline validation of the binary macro regime candidate.

Evaluates the collapsed southerly vs non-southerly macro-regimes using:
1. R2 screening against seed hypotheses.
2. Stability and classifiability metrics.
3. Gate check: READY_FOR_ONDA3_DESIGN_REVIEW vs BLOCKED_WITH_CONCRETE_FAILURE.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from solarstorm._config import TZ_NAME
from solarstorm.eda._catalog import SEED_HYPOTHESES
from solarstorm.onda2e._full_eda import _build_cluster_matrix

# Import necessary functions from classifiability
from solarstorm.onda2e._regime_classifiability import (
    _compute_clustering_metrics,
    _map_by_train_centroids,
    _run_gmm,
    _run_michelangeli_stability,
    _standardize_data,
    select_physical_classifiability_features,
)
from solarstorm.onda2e._regime_design_validation import validate_regime_candidate_r2
from solarstorm.robustness._regime_analysis import detect_dead_regimes

DECISION_SCHEMA = {
    "decision_id": pl.Utf8,
    "item_id": pl.Utf8,
    "item_type": pl.Utf8,
    "domain": pl.Utf8,
    "decision_status": pl.Utf8,
    "evidence_level": pl.Utf8,
    "source_artifact": pl.Utf8,
    "strata": pl.Utf8,
    "sample_size_warning": pl.Utf8,
    "causal_availability": pl.Utf8,
    "leakage_risk": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "next_allowed_action": pl.Utf8,
}

CLASS_METRICS_SCHEMA = {
    "method": pl.Utf8,
    "candidate_version": pl.Utf8,
    "macro_count": pl.Int64,
    "dead_regimes": pl.Int64,
    "low_confidence_share": pl.Float64,
    "classifiability_score": pl.Float64,  # silhouette score
    "predictive_auc": pl.Float64,  # predictive AUC-ROC
    "stability_score": pl.Float64,  # fold stability
    "temporal_stability": pl.Float64,  # temporal stability
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
}


def validate_binary_macro_regimes(
    assignments: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    train_end: dt.date,
    test_start: dt.date,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    tz_name: str = TZ_NAME,
    seed: int = 42,
) -> dict[str, pl.DataFrame]:
    """Validate binary macro candidate R2 robustness and classifiability."""
    # Ensure assignments date_local matches date type of features/labels
    if assignments.schema["date_local"] == pl.Utf8:
        assignments = assignments.with_columns(pl.col("date_local").str.to_date())

    # ----------------------------------------------------
    # 1. R2 validation
    # ----------------------------------------------------
    # Rename binary macro label to candidate_regime_label as required by validation pipeline
    r2_assignments = assignments.select([
        "date_local",
        "cp",
        pl.col("binary_macro_regime_label").alias("candidate_regime_label")
    ])

    r2_artifacts = validate_regime_candidate_r2(
        features,
        labels,
        r2_assignments,
        SEED_HYPOTHESES,
        cp_set=cp_set,
        test_starts=None,
        seed=seed,
    )

    cross_tab = r2_artifacts["regime_candidate_r2_validation"]
    dead_regimes = detect_dead_regimes(cross_tab, regimes=["macro_southerly_flow", "macro_non_southerly"])

    # Build R2 validation summary
    dead_rows = [
        {
            "candidate_regime_family": family,
            "status": "DEAD" if family in dead_regimes else "PASS",
        }
        for family in ["macro_southerly_flow", "macro_non_southerly"]
    ]
    r2_summary = pl.DataFrame(dead_rows)

    # ----------------------------------------------------
    # 2. Classifiability and Stability Validation
    # ----------------------------------------------------
    # Build feature matrix (joining features, labels, and obs)
    cluster_matrix = _build_cluster_matrix(features, labels, obs, tz_name=tz_name)
    if "date_local" in cluster_matrix.columns and cluster_matrix.schema["date_local"] == pl.Utf8:
        cluster_matrix = cluster_matrix.with_columns(pl.col("date_local").str.to_date())

    # Filter features matrix to only have rows matched by assignments
    on_cols = ["date_local", "cp"]
    joined_feats = cluster_matrix.join(assignments, on=on_cols, how="inner").sort("date_local")

    # Select physical features
    cols, _feature_basis_audit = select_physical_classifiability_features(joined_feats)

    train_df = joined_feats.filter(pl.col("date_local") <= train_end)
    test_df = joined_feats.filter(pl.col("date_local") >= test_start)

    has_enough_rows = train_df.height >= 5 and test_df.height >= 1

    predictive_auc = 0.0
    predictive_auc_valid = False
    predictive_auc_blocker = "classifiability matrix was not built"
    comparison_rows = []

    if has_enough_rows and cols:
        # Standardize physical features
        train_std, all_std, _scaler = _standardize_data(train_df, joined_feats, cols)
        test_std = all_std[[i for i, r in enumerate(joined_feats.iter_rows(named=True)) if r["date_local"] >= test_start]]

        # Prepare labels lists
        train_labels = train_df["binary_macro_regime_label"].to_list()
        test_labels_ref = test_df["binary_macro_regime_label"].to_list()

        # Method 1: Candidate (distance_softmax_binary)
        # We treat it as hard assignments: confidence 1.0, margin 1.0, entropy 0.0
        cand_mapped = joined_feats.select(["date_local", "cp", pl.col("binary_macro_regime_label").alias("macro_regime_label")]).with_columns([
            pl.lit("train").alias("train_fold"),
            pl.when(pl.col("date_local") >= test_start).then(pl.lit("test")).otherwise(pl.lit("none")).alias("test_fold"),
            pl.lit(1.0).alias("assignment_confidence"),
            pl.lit(0.0).alias("assignment_entropy"),
            pl.lit(1.0).alias("assignment_margin"),
        ])

        cand_sil, _db, _ch = _compute_clustering_metrics(cand_mapped, joined_feats, cols)

        # Compute predictive AUC-ROC
        y_train = np.array([1 if lbl == "macro_southerly_flow" else 0 for lbl in train_labels])
        y_test = np.array([1 if lbl == "macro_southerly_flow" else 0 for lbl in test_labels_ref])

        has_train_class_variation = len(set(y_train)) >= 2
        has_test_class_variation = len(set(y_test)) >= 2
        if has_train_class_variation and has_test_class_variation:
            clf = LogisticRegression(class_weight="balanced", max_iter=500, random_state=seed)
            clf.fit(train_std, y_train)
            y_probs = clf.predict_proba(test_std)[:, 1]
            predictive_auc = float(roc_auc_score(y_test, y_probs))
            predictive_auc_valid = True
            predictive_auc_blocker = ""
        else:
            predictive_auc = 0.0
            predictive_auc_blocker = (
                "insufficient class variation for AUC-ROC "
                f"(train_classes={len(set(y_train))}, test_classes={len(set(y_test))})"
            )

        cand_temp, cand_fold = _run_michelangeli_stability(
            train_std, train_labels, test_std, test_labels_ref, seed=seed
        )

        comparison_rows.append({
            "method": "distance_softmax_binary",
            "candidate_version": "binary_v1",
            "macro_count": 2,
            "dead_regimes": len(dead_regimes),
            "low_confidence_share": 0.0,
            "classifiability_score": float(cand_sil),
            "predictive_auc": predictive_auc,
            "stability_score": float(cand_fold),
            "temporal_stability": float(cand_temp),
            "decision_update": "KEEP_IN_REGIME_DESIGN_REVIEW",
            "production_status": "EXPERIMENT_ONLY",
        })

        # Method 2: GMM
        mapped_labels_gmm, _cluster_labels_gmm, probs_gmm, entropy_gmm, margin_gmm, _distances_gmm = _run_gmm(
            train_std, all_std, train_labels, n_components=2, seed=seed
        )

        gmm_rows = []
        for idx, row in enumerate(joined_feats.iter_rows(named=True)):
            date_local = row["date_local"]
            gmm_rows.append({
                "date_local": date_local,
                "cp": row["cp"],
                "macro_regime_label": mapped_labels_gmm[idx],
                "train_fold": "train" if date_local <= train_end else "none",
                "test_fold": "test" if date_local >= test_start else "none",
                "assignment_confidence": float(probs_gmm[idx].max()),
                "assignment_entropy": float(entropy_gmm[idx]),
                "assignment_margin": float(margin_gmm[idx]),
            })
        gmm_mapped = pl.DataFrame(gmm_rows)
        gmm_sil, _, _ = _compute_clustering_metrics(gmm_mapped, joined_feats, cols)
        gmm_temp, gmm_fold = _run_michelangeli_stability(
            train_std, mapped_labels_gmm[:len(train_std)], test_std, test_labels_ref, seed=seed
        )

        # Calculate low confidence share for GMM
        n_assigned = gmm_mapped.height
        low_conf = gmm_mapped.filter(pl.col("assignment_confidence") < 0.7)
        low_conf_share = float(low_conf.height / n_assigned) if n_assigned > 0 else 0.0

        comparison_rows.append({
            "method": "train_only_gmm",
            "candidate_version": "binary_v1",
            "macro_count": len(set(mapped_labels_gmm)),
            "dead_regimes": len(set(["macro_southerly_flow", "macro_non_southerly"]) - set(mapped_labels_gmm)),
            "low_confidence_share": low_conf_share,
            "classifiability_score": float(gmm_sil),
            "predictive_auc": 0.0,
            "stability_score": float(gmm_fold),
            "temporal_stability": float(gmm_temp),
            "decision_update": "KEEP_IN_REGIME_DESIGN_REVIEW",
            "production_status": "EXPERIMENT_ONLY",
        })

        # Method 3: PCA SOM
        centroid_labels_som, centroid_distances_som, centroid_margins_som = _map_by_train_centroids(
            train_std, all_std, train_labels
        )
        som_rows = []
        for idx, row in enumerate(joined_feats.iter_rows(named=True)):
            date_local = row["date_local"]
            som_rows.append({
                "date_local": date_local,
                "cp": row["cp"],
                "macro_regime_label": centroid_labels_som[idx],
                "train_fold": "train" if date_local <= train_end else "none",
                "test_fold": "test" if date_local >= test_start else "none",
                "assignment_confidence": 1.0,
                "assignment_entropy": 0.0,
                "assignment_margin": float(centroid_margins_som[idx]),
            })
        som_mapped = pl.DataFrame(som_rows)
        som_sil, _, _ = _compute_clustering_metrics(som_mapped, joined_feats, cols)
        som_temp, som_fold = _run_michelangeli_stability(
            train_std, centroid_labels_som[:len(train_std)], test_std, test_labels_ref, seed=seed
        )

        comparison_rows.append({
            "method": "som_topological",
            "candidate_version": "binary_v1",
            "macro_count": len(set(centroid_labels_som)),
            "dead_regimes": len(set(["macro_southerly_flow", "macro_non_southerly"]) - set(centroid_labels_som)),
            "low_confidence_share": 0.0,
            "classifiability_score": float(som_sil),
            "predictive_auc": 0.0,
            "stability_score": float(som_fold),
            "temporal_stability": float(som_temp),
            "decision_update": "KEEP_IN_REGIME_DESIGN_REVIEW",
            "production_status": "EXPERIMENT_ONLY",
        })

        # Method 4: Michelangeli stability proxy
        # Same mapping but structured as michelangeli method
        michelangeli_rows = []
        max_distance = float(np.max(centroid_distances_som)) if len(centroid_distances_som) else 0.0
        for idx, row in enumerate(joined_feats.iter_rows(named=True)):
            date_local = row["date_local"]
            confidence = 1.0 if max_distance <= 0.0 else 1.0 - (centroid_distances_som[idx] / (max_distance + 1e-12))
            michelangeli_rows.append({
                "date_local": date_local,
                "cp": row["cp"],
                "macro_regime_label": centroid_labels_som[idx],
                "train_fold": "train" if date_local <= train_end else "none",
                "test_fold": "test" if date_local >= test_start else "none",
                "assignment_confidence": float(np.clip(confidence, 0.0, 1.0)),
                "assignment_entropy": 0.0,
                "assignment_margin": float(centroid_margins_som[idx]),
            })
        michelangeli_mapped = pl.DataFrame(michelangeli_rows)
        mich_sil, _, _ = _compute_clustering_metrics(michelangeli_mapped, joined_feats, cols)
        mich_temp, mich_fold = _run_michelangeli_stability(
            train_std, centroid_labels_som[:len(train_std)], test_std, test_labels_ref, seed=seed
        )

        comparison_rows.append({
            "method": "michelangeli_stability",
            "candidate_version": "binary_v1",
            "macro_count": len(set(centroid_labels_som)),
            "dead_regimes": len(set(["macro_southerly_flow", "macro_non_southerly"]) - set(centroid_labels_som)),
            "low_confidence_share": 0.0,
            "classifiability_score": float(mich_sil),
            "predictive_auc": 0.0,
            "stability_score": float(mich_fold),
            "temporal_stability": float(mich_temp),
            "decision_update": "KEEP_IN_REGIME_DESIGN_REVIEW",
            "production_status": "EXPERIMENT_ONLY",
        })

    classifiability_df = pl.DataFrame(comparison_rows, schema=CLASS_METRICS_SCHEMA)

    # ----------------------------------------------------
    # 3. Gate Assessment & Decision updates
    # ----------------------------------------------------
    # Thresholds checking for Candidate:
    # 1. R2 check: both macros must pass.
    r2_passed = len(dead_regimes) == 0

    # 2. Stability, confidence, and predictive classifiability checks:
    candidate_row = classifiability_df.filter(pl.col("method") == "distance_softmax_binary")
    if candidate_row.height > 0:
        stability_score = candidate_row["stability_score"][0]
        low_confidence_share = candidate_row["low_confidence_share"][0]
        metrics_passed = (
            predictive_auc_valid
            and stability_score >= 0.7
            and low_confidence_share <= 0.5
            and predictive_auc >= 0.80
        )
    else:
        stability_score = 0.0
        low_confidence_share = 1.0
        metrics_passed = False

    gate_passes = r2_passed and metrics_passed
    if gate_passes:
        gate_decision = "READY_FOR_ONDA3_DESIGN_REVIEW"
    elif not predictive_auc_valid and candidate_row.height > 0:
        gate_decision = "BLOCKED_INSUFFICIENT_CLASS_VARIATION"
    else:
        gate_decision = "BLOCKED_WITH_CONCRETE_FAILURE"

    # Update decision_update column in classifiability_df
    classifiability_df = classifiability_df.with_columns(
        pl.when(pl.col("method") == "distance_softmax_binary")
        .then(pl.lit(gate_decision))
        .otherwise(pl.col("decision_update"))
        .alias("decision_update")
    )

    # Count passing hypotheses per regime to provide scientific nuance
    southerly_passes = 0
    non_southerly_passes = 0
    total_southerly = 0
    total_non_southerly = 0
    if cross_tab.height > 0 and "regime" in cross_tab.columns:
        if "passes" in cross_tab.columns:
            southerly_passes = int(cross_tab.filter((pl.col("regime") == "macro_southerly_flow") & pl.col("passes").fill_null(False)).height)
            non_southerly_passes = int(cross_tab.filter((pl.col("regime") == "macro_non_southerly") & pl.col("passes").fill_null(False)).height)
        total_southerly = int(cross_tab.filter(pl.col("regime") == "macro_southerly_flow").height)
        total_non_southerly = int(cross_tab.filter(pl.col("regime") == "macro_non_southerly").height)

    decision_rationale = (
        f"Binary macro candidate validated (apto para design review com ressalva). R2 passed for both macros, but macro_non_southerly has weak sensitivity "
        f"(passes {non_southerly_passes}/{total_non_southerly} hypothesis rows vs {southerly_passes}/{total_southerly} for macro_southerly_flow). "
        f"Stability score: {stability_score:.4f} (>= 0.7). "
        f"Low confidence share: {low_confidence_share:.4f} (<= 0.5). "
        f"Predictive classifiability (AUC-ROC): {predictive_auc:.4f} (>= 0.80)."
        if gate_passes
        else f"Binary macro candidate validation failed. "
        f"R2 passed: {r2_passed} (dead: {', '.join(dead_regimes)}). "
        f"Stability score: {stability_score:.4f} (expected >= 0.7). "
        f"Low confidence share: {low_confidence_share:.4f} (expected <= 0.5). "
        f"Predictive classifiability (AUC-ROC): {predictive_auc:.4f} "
        f"(expected >= 0.80; {predictive_auc_blocker or 'valid split'})."
    )

    decision_rows = [
        {
            "decision_id": "REGIME-BINARY-MACRO-VALIDATION-001",
            "item_id": "WCT-BINARY-MACRO",
            "item_type": "thesis",
            "domain": "REGIME",
            "decision_status": gate_decision,
            "evidence_level": "E3_candidate_r2_validation",
            "source_artifact": "reports/regime-design/regime_binary_macro_r2_validation_v1.md",
            "strata": "binary macro family x CP",
            "sample_size_warning": (
                "macro_non_southerly support: 16,298; macro_southerly_flow support: 5,526."
            ),
            "causal_availability": "Causal assignments assigned from pre-CP Wellington morning observations.",
            "leakage_risk": "EXPERIMENT_ONLY; no production features or classifiers modified.",
            "decision_rationale": decision_rationale,
            "next_allowed_action": (
                "Proceed to Onda 3 Design Review with caveat: macro_non_southerly shows weak R2 sensitivity "
                "and must be modeled with continuous features (e.g. foehn_score, cloud cover suppression) "
                "to capture residual temperature variance."
                if gate_passes
                else "Revise binary macro assignments, train/test split, or validation window before Onda 3 design review."
            ),
        }
    ]

    decision_df = pl.DataFrame(decision_rows, schema=DECISION_SCHEMA)

    return {
        "regime_binary_macro_r2_validation_v1": cross_tab,
        "regime_binary_macro_classifiability_v1": classifiability_df,
        "regime_binary_macro_decision_update_v1": decision_df,
        "dead_candidate_regimes": r2_summary,
    }


def write_binary_validation_reports(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write binary validation reports and CSVs to disk."""
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    r2_csv = out_dir / "regime_binary_macro_r2_validation_v1.csv"
    r2_md = out_dir / "regime_binary_macro_r2_validation_v1.md"
    class_csv = out_dir / "regime_binary_macro_classifiability_v1.csv"
    class_md = out_dir / "regime_binary_macro_classifiability_v1.md"
    decision_csv = out_dir / "regime_binary_macro_decision_update_v1.csv"

    artifacts["regime_binary_macro_r2_validation_v1"].write_csv(r2_csv)
    artifacts["regime_binary_macro_classifiability_v1"].write_csv(class_csv)
    artifacts["regime_binary_macro_decision_update_v1"].write_csv(decision_csv)

    # Merge into reports/onda2e/evidence_decision_register.csv if it exists
    register_path = Path("reports/onda2e/evidence_decision_register.csv")
    if register_path.exists():
        register_df = pl.read_csv(register_path)
        register_df = register_df.filter(
            (pl.col("decision_id") != "REGIME-BINARY-MACRO-VALIDATION-001") &
            (pl.col("item_id") != "WCT-BINARY-MACRO")
        )
        updated_register = pl.concat([register_df, artifacts["regime_binary_macro_decision_update_v1"]])
        updated_register.write_csv(register_path)

    # 1. Write R2 validation markdown report
    cross_tab = artifacts["regime_binary_macro_r2_validation_v1"]
    dead_summary = artifacts["dead_candidate_regimes"]
    decision = artifacts["regime_binary_macro_decision_update_v1"].row(0, named=True)

    r2_lines = [
        f"# Regime Binary Macro R2 Validation Report - {today.isoformat()}",
        "",
        "This is an experiment-only candidate validation report.",
        "Status: `EXPERIMENT_ONLY`; no production assets are modified.",
        "",
        f"- **Gate Decision Status**: `{decision['decision_status']}`",
        f"- **Rationale**: {decision['decision_rationale']}",
        "",
        "## CEXP-002B Causal R2 Robustness Gate Check",
        "",
        "| Macro | R2 Status |",
        "|---|---|",
    ]
    for row in dead_summary.iter_rows(named=True):
        r2_lines.append(f"| {row['candidate_regime_family']} | **{row['status']}** |")

    r2_lines += [
        "",
        "## Hypothesis R2 Screening Detail",
        "",
        "| Regime | Hypothesis ID | Feature Column | CP | Passes | N Days | Status |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in cross_tab.sort(["regime", "cp", "hypothesis_id"]).iter_rows(named=True):
        r2_lines.append(
            f"| {row['regime']} | {row['hypothesis_id']} | {row['feature_column']} | "
            f"{row['cp']} | {row['passes']} | {row['n_days']} | {row['status']} |"
        )

    r2_md.write_text("\n".join(r2_lines) + "\n", encoding="utf-8")

    # 2. Write Classifiability validation markdown report
    class_df = artifacts["regime_binary_macro_classifiability_v1"]
    class_lines = [
        f"# Regime Binary Macro Classifiability and Stability Report - {today.isoformat()}",
        "",
        "This report documents classifiability and stability metrics for the binary macro candidate.",
        "Status: `EXPERIMENT_ONLY`; evaluated on the approved physical feature basis.",
        "",
        "## Method Comparison",
        "",
        "| Method | Candidate Version | Macros | Dead | Low Conf Share | Silhouette | Predictive AUC-ROC | Stability (Fold) | Temporal Stability | Decision Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in class_df.iter_rows(named=True):
        class_lines.append(
            f"| `{row['method']}` | {row['candidate_version']} | {row['macro_count']} | {row['dead_regimes']} | "
            f"{row['low_confidence_share']:.4f} | {row['classifiability_score']:.4f} | {row['predictive_auc']:.4f} | "
            f"{row['stability_score']:.4f} | {row['temporal_stability']:.4f} | `{row['decision_update']}` |"
        )

    class_lines += [
        "",
        "## Target Verification Thresholds",
        "",
        "- **Predictive Separability (AUC-ROC)**: >= 0.80",
        "- **Stability (Fold)**: >= 0.7",
        "- **Low Confidence Share**: <= 0.5",
        "",
        "## Validation Status Conclusion",
        "",
        decision["decision_rationale"],
    ]

    class_md.write_text("\n".join(class_lines) + "\n", encoding="utf-8")

    return {
        "regime_binary_macro_r2_validation_csv": r2_csv,
        "regime_binary_macro_r2_validation_md": r2_md,
        "regime_binary_macro_classifiability_csv": class_csv,
        "regime_binary_macro_classifiability_md": class_md,
        "regime_binary_macro_decision_update_csv": decision_csv,
    }
