"""Onda 2E thesis-atlas EDA helpers."""

from __future__ import annotations

from solarstorm.onda2e._atlas import (
    Thesis,
    build_prerequisite_artifacts,
    parse_thesis_atlas,
    thesis_testability_audit,
    write_onda2e_artifacts,
)
from solarstorm.onda2e._cloud_cover_baseline_experiment import (
    build_cloud_cover_baseline_experiment,
    write_cloud_cover_baseline_experiment_artifacts,
)
from solarstorm.onda2e._cooling import (
    build_cooling_decision_updates,
    build_cooling_domain_artifacts,
    write_cooling_domain_artifacts,
)
from solarstorm.onda2e._decision_gate import (
    apply_decision_updates,
    build_decision_gate_artifacts,
    remove_decision_items,
    write_decision_gate_artifacts,
)
from solarstorm.onda2e._eda_feature_candidate_review import (
    build_eda_feature_candidate_review,
    write_eda_feature_candidate_review_artifacts,
)
from solarstorm.onda2e._foehn import (
    build_foehn_decision_updates,
    build_foehn_domain_artifacts,
    write_foehn_domain_artifacts,
)
from solarstorm.onda2e._foundation_experiment_results import (
    build_foundation_experiment_results,
    write_foundation_experiment_result_artifacts,
)
from solarstorm.onda2e._foundation_experiments import (
    build_foundation_experiment_catalog,
    load_foundation_experiment_inputs,
    write_foundation_experiment_catalog_artifacts,
)
from solarstorm.onda2e._full_eda import (
    build_full_eda_artifacts,
    build_regime_design_decision_updates,
    refresh_full_eda_decision_review,
    write_full_eda_artifacts,
)
from solarstorm.onda2e._regime_binary_macro_candidate import (
    build_regime_binary_macro_candidate_artifacts,
    write_regime_binary_macro_candidate_artifacts,
)
from solarstorm.onda2e._regime_binary_macro_validation import (
    validate_binary_macro_regimes,
    write_binary_validation_reports,
)
from solarstorm.onda2e._regime_candidate_revision import (
    build_regime_design_candidate_v2,
    write_regime_design_candidate_v2_artifacts,
)
from solarstorm.onda2e._regime_classifiability import (
    build_regime_classifiability_artifacts,
    write_regime_classifiability_artifacts,
)
from solarstorm.onda2e._regime_deadlock_pivot import (
    build_regime_deadlock_pivot_artifacts,
    write_regime_deadlock_pivot_artifacts,
)
from solarstorm.onda2e._regime_design_validation import (
    build_regime_candidate_artifacts,
    build_regime_candidate_v2_assignment_artifacts,
    compare_regime_candidate_r2,
    compare_regime_candidate_v2_v21,
    validate_regime_candidate_r2,
    validate_regime_design_queue,
    write_regime_candidate_v2_validation_artifacts,
    write_regime_candidate_v21_validation_artifacts,
    write_regime_candidate_validation_artifacts,
)
from solarstorm.onda2e._regime_repair_diagnostics import (
    build_regime_repair_diagnostics,
    write_regime_repair_diagnostics_artifacts,
)
from solarstorm.onda2e._regime_residual_absorption import (
    build_regime_residual_absorption_artifacts,
    write_regime_residual_absorption_artifacts,
)
from solarstorm.onda2e._regime_v22_calm_radiative import (
    build_regime_v22_calm_radiative_artifacts,
    compare_regime_candidate_v21_v22,
    write_regime_v22_calm_radiative_artifacts,
)
from solarstorm.onda2e._regime_v23_calm_cloud_signal_validation import (
    build_regime_calm_radiative_cloud_signal_validation,
    write_regime_calm_radiative_cloud_signal_validation_artifacts,
)
from solarstorm.onda2e._regime_v23_calm_failure_diagnostics import (
    build_regime_v23_calm_failure_diagnostics,
    write_regime_v23_calm_failure_diagnostics_artifacts,
)
from solarstorm.onda2e._regime_v23_calm_feature_hypotheses import (
    build_regime_calm_radiative_feature_hypotheses,
    write_regime_calm_radiative_feature_hypotheses_artifacts,
)
from solarstorm.onda2e._regime_v23_calm_target_diagnostics import (
    build_regime_calm_radiative_target_diagnostics,
    write_regime_calm_radiative_target_diagnostics_artifacts,
)
from solarstorm.onda2e._thesis_domain_eda import (
    build_thesis_domain_eda_artifacts,
    build_thesis_domain_eda_decision_updates,
    write_thesis_domain_eda_artifacts,
)
from solarstorm.onda2e._timing import (
    build_timing_decision_updates,
    build_timing_domain_artifacts,
    write_timing_domain_artifacts,
)
from solarstorm.onda2e._wind import (
    build_wind_decision_updates,
    build_wind_domain_artifacts,
    write_wind_domain_artifacts,
)

__all__ = [
    "Thesis",
    "apply_decision_updates",
    "build_cloud_cover_baseline_experiment",
    "build_cooling_decision_updates",
    "build_cooling_domain_artifacts",
    "build_decision_gate_artifacts",
    "build_eda_feature_candidate_review",
    "build_foehn_decision_updates",
    "build_foehn_domain_artifacts",
    "build_foundation_experiment_catalog",
    "build_foundation_experiment_results",
    "build_full_eda_artifacts",
    "build_prerequisite_artifacts",
    "build_regime_binary_macro_candidate_artifacts",
    "build_regime_calm_radiative_cloud_signal_validation",
    "build_regime_calm_radiative_feature_hypotheses",
    "build_regime_calm_radiative_target_diagnostics",
    "build_regime_candidate_artifacts",
    "build_regime_candidate_v2_assignment_artifacts",
    "build_regime_classifiability_artifacts",
    "build_regime_deadlock_pivot_artifacts",
    "build_regime_design_candidate_v2",
    "build_regime_design_decision_updates",
    "build_regime_repair_diagnostics",
    "build_regime_residual_absorption_artifacts",
    "build_regime_v22_calm_radiative_artifacts",
    "build_regime_v23_calm_failure_diagnostics",
    "build_thesis_domain_eda_artifacts",
    "build_thesis_domain_eda_decision_updates",
    "build_timing_decision_updates",
    "build_timing_domain_artifacts",
    "build_wind_decision_updates",
    "build_wind_domain_artifacts",
    "compare_regime_candidate_r2",
    "compare_regime_candidate_v2_v21",
    "compare_regime_candidate_v21_v22",
    "load_foundation_experiment_inputs",
    "parse_thesis_atlas",
    "refresh_full_eda_decision_review",
    "remove_decision_items",
    "thesis_testability_audit",
    "validate_binary_macro_regimes",
    "validate_regime_candidate_r2",
    "validate_regime_design_queue",
    "write_binary_validation_reports",
    "write_cloud_cover_baseline_experiment_artifacts",
    "write_cooling_domain_artifacts",
    "write_decision_gate_artifacts",
    "write_eda_feature_candidate_review_artifacts",
    "write_foehn_domain_artifacts",
    "write_foundation_experiment_catalog_artifacts",
    "write_foundation_experiment_result_artifacts",
    "write_full_eda_artifacts",
    "write_onda2e_artifacts",
    "write_regime_binary_macro_candidate_artifacts",
    "write_regime_calm_radiative_cloud_signal_validation_artifacts",
    "write_regime_calm_radiative_feature_hypotheses_artifacts",
    "write_regime_calm_radiative_target_diagnostics_artifacts",
    "write_regime_candidate_v2_validation_artifacts",
    "write_regime_candidate_v21_validation_artifacts",
    "write_regime_candidate_validation_artifacts",
    "write_regime_classifiability_artifacts",
    "write_regime_deadlock_pivot_artifacts",
    "write_regime_design_candidate_v2_artifacts",
    "write_regime_repair_diagnostics_artifacts",
    "write_regime_residual_absorption_artifacts",
    "write_regime_v22_calm_radiative_artifacts",
    "write_regime_v23_calm_failure_diagnostics_artifacts",
    "write_thesis_domain_eda_artifacts",
    "write_timing_domain_artifacts",
    "write_wind_domain_artifacts",
]
