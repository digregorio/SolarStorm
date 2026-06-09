"""Tests for settlement contract: rounding, brackets, flip_risk."""
import pytest

from solarstorm.data._settlement import (
    bracket_for,
    flip_risk,
    integer_settlement,
)


def test_integer_settlement_standard():
    assert integer_settlement(14.4) == 14
    assert integer_settlement(14.5) == 15
    assert integer_settlement(14.6) == 15


def test_integer_settlement_negative():
    assert integer_settlement(-2.4) == -2
    assert integer_settlement(-2.5) == -2   # commercial: half-up, not banker's
    assert integer_settlement(-2.6) == -3


def test_flip_risk_at_integer_center():
    """At integer center (15.0), boundary_distance is max (0.5) — far from .5 boundary."""
    r = flip_risk(15.0)
    assert r.boundary_distance == pytest.approx(0.5)
    assert r.flip_risk == pytest.approx(0.0)  # safe: far from boundary


def test_flip_risk_at_boundary():
    """At .5 boundary (15.5), boundary_distance is zero — micro-variation flips bracket."""
    r = flip_risk(15.5)
    assert r.boundary_distance == pytest.approx(0.0)
    assert r.flip_risk == pytest.approx(0.5)  # max risk: on the boundary


def test_flip_risk_inside_bucket():
    """Inside the bucket, boundary_distance is between 0 and 0.5."""
    r = flip_risk(15.3)
    assert 0.15 < r.boundary_distance < 0.25
    assert 0.25 < r.flip_risk < 0.35


def test_flip_risk_properties_consistent():
    """boundary_distance + flip_risk == 0.5 always."""
    for val in [15.0, 15.2, 15.5, 14.7, -2.5]:
        r = flip_risk(val)
        assert r.boundary_distance + r.flip_risk == pytest.approx(0.5)


def test_bracket_for_maps_to_contract_bucket():
    assert bracket_for(14.2) == 14
    assert bracket_for(14.7) == 15
    assert bracket_for(0.3) == 0


def test_0_1_c_crosses_bracket_boundary():
    """The catastrophic case: 14.4→14, 14.5→15. Must be systematic (P4)."""
    assert bracket_for(14.4) == 14
    assert bracket_for(14.5) == 15
    assert bracket_for(14.4) != bracket_for(14.5)


def test_half_up_vs_bankers():
    """Half-up rounding differs from Python's round() at .5."""
    assert integer_settlement(20.5) == 21
    assert integer_settlement(14.5) == 15
    assert round(20.5) == 20  # banker's — the exact bug being prevented
