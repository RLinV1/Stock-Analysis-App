from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from portfolio_lab.data import Dataset, make_samples
from portfolio_lab.protocol import make_fold_samples, plan_walk_forward


def sessions(start="2010-01-01", end="2021-12-31"):
    current, stop = date.fromisoformat(start), date.fromisoformat(end)
    result = []
    while current <= stop:
        if current.weekday() < 5:
            result.append(current.isoformat())
        current += timedelta(days=1)
    return result


def dataset():
    dates = np.array(sessions())
    t = np.arange(len(dates))
    prices = np.stack([100 + t * 0.05 + np.sin(t / 11), 120 + t * 0.03 + np.cos(t / 13)], axis=1)
    return Dataset(dates, prices, {}, Path("synthetic-protocol-fixture.json"))


def test_expanding_folds_are_anchored_to_24_months_and_cover_every_target():
    dates = sessions()
    plan = plan_walk_forward(dates, "2013-01-01", "2020-04-30")
    assert plan.effective_start == "2013-01-01"
    assert plan.effective_end == "2020-04-30"
    assert plan.exclusions == ()
    assert [fold.scheduled_start for fold in plan.folds] == ["2013-01-01", "2015-01-01", "2017-01-01", "2019-01-01"]
    # 2017-01-01 is a Sunday; use the next observed date without changing the anchor.
    assert plan.folds[2].test_start == "2017-01-02"
    assert [i for fold in plan.folds for i in fold.test_indices] == list(range(dates.index(plan.effective_start), dates.index(plan.effective_end) + 1))
    previous_training = 0
    for fold in plan.folds:
        assert len(fold.train_indices) > previous_training
        assert len(fold.train_indices) >= 252
        previous_training = len(fold.train_indices)
        prior = len(fold.train_indices) + len(fold.validation_indices)
        assert len(fold.validation_indices) == max(63, (prior + 9) // 10)
        assert max(fold.train_indices) < min(fold.validation_indices)
        assert max(fold.validation_indices) < min(fold.test_indices)
        assert fold.train_end < fold.validation_end < fold.test_start <= fold.test_end


def test_insufficient_history_moves_start_and_records_reason_without_synthetic_dates():
    dates = sessions("2010-01-01", "2012-12-31")
    plan = plan_walk_forward(dates, dates[60], dates[-1], lookback=50)
    assert plan.effective_start == dates[365]  # 50 context + 252 train + 63 validation.
    assert plan.requested_start == dates[60]
    assert len(plan.exclusions) == 1 and "history" in plan.exclusions[0]
    assert len(plan.folds[0].train_indices) == 252
    assert len(plan.folds[0].validation_indices) == 63


def test_insufficient_history_at_requested_end_fails_instead_of_borrowing_future_data():
    dates = sessions()
    with pytest.raises(ValueError, match="No evaluation dates"):
        plan_walk_forward(dates, dates[100], dates[364])


def test_leap_boundaries_use_original_anchor_without_drift():
    dates = sessions("2010-01-01", "2025-03-01")
    # Leap day can be a session in a supplied calendar; do not impose exchange rules.
    dates = sorted(set(dates + ["2020-02-29", "2024-02-29"]))
    plan = plan_walk_forward(dates, "2020-02-29", "2024-03-01")
    assert [f.scheduled_start for f in plan.folds] == ["2020-02-29", "2022-02-28", "2024-02-29"]


def test_long_session_gap_skips_empty_intervals_and_preserves_evaluation_targets():
    dates = [day for day in sessions() if not "2014-01-01" <= day < "2019-01-01"]
    plan = plan_walk_forward(dates, "2013-01-01", "2020-04-30")
    assert [f.scheduled_start for f in plan.folds] == ["2013-01-01", "2019-01-01"]
    assert [i for fold in plan.folds for i in fold.test_indices] == list(range(dates.index(plan.effective_start), dates.index(plan.effective_end) + 1))


@pytest.mark.parametrize("dates", [[], ["2020-02-30"], ["2020-1-01"], ["2020-01-02", "2020-01-01"], ["2020-01-01", "2020-01-01"], "2020-01-01", [123]])
def test_invalid_observed_dates_fail(dates):
    with pytest.raises(ValueError):
        plan_walk_forward(dates, "2020-01-01", "2021-01-01")


@pytest.mark.parametrize("lookback", [0, 1, -1, True, 2.5, "50"])
def test_invalid_lookback_fails(lookback):
    with pytest.raises(ValueError, match="Lookback"):
        plan_walk_forward(sessions(), "2013-01-01", "2014-01-01", lookback=lookback)


def test_invalid_or_empty_requested_range_fails():
    for start, end in [("2014-01-01", "2013-01-01"), ("2013-02-30", "2014-01-01"), ("2030-01-01", "2031-01-01")]:
        with pytest.raises(ValueError):
            plan_walk_forward(sessions(), start, end)


def test_fold_samples_use_training_inputs_and_next_return_alignment():
    data = dataset()
    fold = plan_walk_forward(data.dates, "2013-01-01", "2020-04-30").folds[0]
    samples = make_fold_samples(data, fold)
    assert str(samples.dates[-1]) == fold.test_end
    assert samples.train.sum() == len(fold.train_indices)
    assert samples.validation.sum() == len(fold.validation_indices)
    assert samples.test.sum() == len(fold.test_indices)
    first_test = fold.test_indices[0]
    np.testing.assert_allclose(samples.y[samples.test][0], data.prices[first_test] / data.prices[first_test - 1] - 1, rtol=1e-6)
    raw_last_input = samples.x[samples.test][0][-1] * samples.scale + samples.mean
    np.testing.assert_allclose(raw_last_input[::2], data.prices[first_test - 1], rtol=1e-6)
    before = samples
    data.prices[fold.train_indices[-1] + 1:] *= 3
    changed = make_fold_samples(data, fold)
    np.testing.assert_array_equal(before.mean, changed.mean)
    np.testing.assert_array_equal(before.scale, changed.scale)
    np.testing.assert_array_equal(before.x[before.train], changed.x[changed.train])
    np.testing.assert_array_equal(before.y[before.train], changed.y[changed.train])


def test_prices_after_fold_end_cannot_change_any_fold_sample():
    data = dataset()
    fold = plan_walk_forward(data.dates, "2013-01-01", "2020-04-30").folds[0]
    before = make_fold_samples(data, fold)
    data.prices[fold.test_indices[-1] + 1:] *= 100
    after = make_fold_samples(data, fold)
    for name in ["x", "y", "mean", "scale", "dates"]:
        np.testing.assert_array_equal(getattr(before, name), getattr(after, name))


def test_single_target_final_fold_is_supported_without_relaxing_a0_default():
    data = dataset()
    fold = plan_walk_forward(data.dates, "2013-01-01", "2015-01-01").folds[-1]
    assert len(fold.test_indices) == 1
    samples = make_fold_samples(data, fold)
    assert samples.test.sum() == 1
    assert str(samples.dates[samples.test][0]) == "2015-01-01"
    stop = fold.test_indices[-1] + 1
    bounded = replace(data, dates=data.dates[:stop], prices=data.prices[:stop])
    with pytest.raises(ValueError, match="target observations"):
        make_samples(bounded, fold.lookback, fold.train_end, fold.validation_end)
    np.testing.assert_allclose(samples.y[samples.test][0], data.prices[stop - 1] / data.prices[stop - 2] - 1, rtol=1e-6)


@pytest.mark.parametrize("invalid_flag", [1, "true", None])
def test_single_target_opt_in_rejects_coercion(invalid_flag):
    data = dataset()
    with pytest.raises(ValueError, match="boolean"):
        make_samples(data, 50, "2012-01-02", "2012-12-31", allow_single_test=invalid_flag)


@pytest.mark.parametrize("corruption", ["overlap", "future_train", "reordered", "wrong_date", "wrong_lookback", "list_indices", "boolean_index", "wrong_schedule"])
def test_deliberate_lookahead_and_forged_fold_identity_fail(corruption):
    data = dataset()
    fold = plan_walk_forward(data.dates, "2013-01-01", "2020-04-30").folds[0]
    if corruption == "overlap": fold = replace(fold, train_indices=fold.train_indices + fold.validation_indices[:1])
    elif corruption == "future_train": fold = replace(fold, train_indices=fold.train_indices + fold.test_indices[:1])
    elif corruption == "reordered": fold = replace(fold, validation_indices=fold.validation_indices[::-1])
    elif corruption == "wrong_date": fold = replace(fold, train_end=fold.test_start)
    elif corruption == "wrong_lookback": fold = replace(fold, lookback=49)
    elif corruption == "list_indices": fold = replace(fold, train_indices=list(fold.train_indices))
    elif corruption == "boolean_index": fold = replace(fold, train_indices=(True,) + fold.train_indices[1:])
    elif corruption == "wrong_schedule": fold = replace(fold, scheduled_end_exclusive=fold.test_end)
    with pytest.raises(ValueError):
        make_fold_samples(data, fold)
