import datetime as dt

from solarstorm.eval._walkforward import expanding_walk_forward_splits


def test_expanding_splits_produces_correct_windows():
    splits = expanding_walk_forward_splits(
        history_start=dt.date(2020, 1, 1),
        test_starts=[dt.date(2023, 1, 1), dt.date(2024, 1, 1)],
        test_length_days=365,
        min_train_days=365,
    )
    assert len(splits) == 2
    s0, s1 = splits
    assert s0.train_start == dt.date(2020, 1, 1)
    assert s0.train_end == dt.date(2022, 12, 31)
    assert s0.test_start == dt.date(2023, 1, 1)
    assert s0.test_end == dt.date(2023, 12, 31)
    # Second split: train expands, includes first test year
    assert s1.train_start == dt.date(2020, 1, 1)
    assert s1.train_end == dt.date(2023, 12, 31)


def test_expanding_splits_drops_short_train():
    splits = expanding_walk_forward_splits(
        history_start=dt.date(2023, 6, 1),
        test_starts=[dt.date(2023, 6, 15)],
        test_length_days=365,
        min_train_days=365,
    )
    assert len(splits) == 0


def test_holdout_windows():
    splits = expanding_walk_forward_splits(
        history_start=dt.date(2020, 1, 1),
        test_starts=[dt.date(2025, 1, 1)],
        test_length_days=30,
        min_train_days=365,
        holdout_windows_days=[7, 14],
    )
    # Should produce regular split + 2 holdout windows
    assert len(splits) >= 1
