import datetime as dt

import pytest

from solarstorm._contracts import require_causal


def test_require_causal_passes_when_feature_before_cp():
    require_causal(
        feature_max_ts=dt.datetime(2025, 6, 15, 22, 30, tzinfo=dt.UTC),
        cp_utc=dt.datetime(2025, 6, 15, 23, 0, tzinfo=dt.UTC),
    )


def test_require_causal_raises_when_feature_at_cp():
    with pytest.raises(RuntimeError, match="causality"):
        require_causal(
            feature_max_ts=dt.datetime(2025, 6, 15, 23, 0, tzinfo=dt.UTC),
            cp_utc=dt.datetime(2025, 6, 15, 23, 0, tzinfo=dt.UTC),
        )


def test_require_causal_raises_when_feature_after_cp():
    with pytest.raises(RuntimeError, match="causality"):
        require_causal(
            feature_max_ts=dt.datetime(2025, 6, 15, 23, 30, tzinfo=dt.UTC),
            cp_utc=dt.datetime(2025, 6, 15, 23, 0, tzinfo=dt.UTC),
        )
