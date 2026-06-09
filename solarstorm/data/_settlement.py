"""P1+P4: Settlement contract — integer rounding, bracket mapping, flip risk.

All internal computation uses decimal (P1). The integer bracket for Polymarket
settlement is derived ONLY at the output layer.

Terminology:
  - **boundary_distance**: How far a decimal value is from the nearest .5°C
    rounding boundary.  0.5 = at integer center (far from boundary, large
    margin against a 0.1°C measurement error).  0.0 = exactly on a .5 boundary
    (a micro-variation flips the bracket).
  - **flip_risk**: The inverse — 0.0 = safe (at integer center), 0.5 = max risk
    (at a .5 boundary).  ``flip_risk = 0.5 - boundary_distance``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def integer_settlement(dec: float) -> int:
    """Commercial rounding (half-up): 14.5 → 15, -2.5 → -2."""
    return math.floor(dec + 0.5)


def bracket_for(dec: float) -> int:
    """The Polymarket bracket for a decimal temperature (P4)."""
    return integer_settlement(dec)


@dataclass
class FlipRisk:
    boundary_distance: float  # 0.5 = at integer center (safe), 0.0 = at .5 boundary (dangerous)
    nearest_boundary: float
    direction: str    # "up", "down", "either", "stable"

    @property
    def flip_risk(self) -> float:
        """0.0 = safe (at integer center).  0.5 = max risk (at .5 boundary)."""
        return 0.5 - self.boundary_distance


def flip_risk(dec: float) -> FlipRisk:
    """Analyse settlement risk for a decimal temperature forecast.

    ``boundary_distance`` is the distance to the nearest .5°C rounding boundary
    (0.5 = far from any boundary, 0.0 = exactly on a boundary).  ``flip_risk``
    inverts this so that higher = more dangerous.

    Direction semantics:
      - ``"stable"`` — exactly on a .5 boundary (always rounds the same way).
      - ``"either"`` — exactly at an integer (measurement noise determines the
        bracket).
      - ``"up"`` / ``"down"`` — which side of the nearest boundary.
    """
    settle = integer_settlement(dec)
    boundary_distance = round(0.5 - abs(dec - settle), 6)
    boundary_distance = max(0.0, boundary_distance)

    frac = dec - math.floor(dec)
    nearest_boundary = math.floor(dec) + 0.5

    if abs(frac - 0.5) < 1e-9:
        direction = "stable"
    elif abs(frac) < 1e-9:
        direction = "either"
    elif dec < settle:
        direction = "down"
    else:
        direction = "up"

    return FlipRisk(
        boundary_distance=boundary_distance,
        nearest_boundary=nearest_boundary,
        direction=direction,
    )
