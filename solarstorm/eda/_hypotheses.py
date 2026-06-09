"""Hypothesis framework (P3): every EDA finding → registered hypothesis → gated test.

Each hypothesis runs through the walk-forward harness and returns effect size + bootstrap CI.
Passes if CI95 excludes zero AND direction is beneficial. Failed hypotheses are documented
with the same rigor as passed ones (P5).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Hypothesis:
    id: str
    description: str
    feature_column: str
    test: Callable | None = None
    effect_size: float | None = None
    ci95: tuple[float, float] | None = None
    p_value: float | None = None
    passes: bool | None = None
    source: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        d = {
            "id": self.id, "description": self.description,
            "feature_column": self.feature_column, "source": self.source,
        }
        if self.effect_size is not None:
            d["effect_size"] = round(self.effect_size, 6)
        if self.ci95 is not None:
            d["ci95_low"] = round(self.ci95[0], 6)
            d["ci95_high"] = round(self.ci95[1], 6)
        if self.p_value is not None:
            d["p_value"] = round(self.p_value, 6)
        d["passes"] = self.passes
        if self.notes:
            d["notes"] = self.notes
        return d


def run_hypothesis_test(
    h: Hypothesis,
    *,
    effect_size: float,
    ci95: tuple[float, float],
    p_value: float,
) -> Hypothesis:
    h.effect_size = effect_size
    h.ci95 = ci95
    h.p_value = p_value
    h.passes = ci95[0] > 0.0  # CI95 low > 0 AND direction is beneficial
    return h
