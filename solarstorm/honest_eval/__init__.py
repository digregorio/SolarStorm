"""P0 honest evaluation harness (EXPERIMENT_ONLY)."""
from __future__ import annotations

from solarstorm.honest_eval._ablation import (
    PERSISTENCE_BLOCK,
    run_persistence_ablation,
)
from solarstorm.honest_eval._artifacts import (
    render_honest_eval_report,
    write_honest_eval_artifacts,
)
from solarstorm.honest_eval._floor import (
    apply_physical_floor,
    build_floor_violation_audit,
)
from solarstorm.honest_eval._kcp import build_kcp_long
from solarstorm.honest_eval._null import fit_honest_null, predict_honest_null
from solarstorm.honest_eval._review import build_honest_gates
from solarstorm.honest_eval._strata import (
    assign_remaining_warming_strata,
    build_honest_comparison,
)

__all__ = [
    "PERSISTENCE_BLOCK",
    "apply_physical_floor",
    "assign_remaining_warming_strata",
    "build_floor_violation_audit",
    "build_honest_comparison",
    "build_honest_gates",
    "build_kcp_long",
    "fit_honest_null",
    "predict_honest_null",
    "render_honest_eval_report",
    "run_persistence_ablation",
    "write_honest_eval_artifacts",
]
