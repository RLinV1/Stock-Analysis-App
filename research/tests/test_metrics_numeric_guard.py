"""Unrun numerical rejection cases; no model fitting or GPU dependency."""

import warnings

import numpy as np
import pytest

from portfolio_lab.metrics import evaluate


@pytest.mark.parametrize("cost", [
    True, False, np.bool_(True), None, "1", [1], np.array(1), np.array([1]),
    1j, float("nan"), float("inf"), -float("inf"), -1, 101, 10**400,
])
def test_invalid_cost_is_rejected_as_validation_error(cost):
    with pytest.raises(ValueError, match="Cost must be between"):
        evaluate([[1], [1]], [[0.01], [0.02]], cost)


@pytest.mark.parametrize("cost", [0, 100, np.int64(1), np.float32(0.25), np.float64(1.5)])
def test_valid_scalar_cost_keeps_initial_target_accounting(cost):
    result = evaluate([[1], [1]], [[0], [0]], cost)
    rate = float(cost) / 10000
    np.testing.assert_allclose(result["turnover"], [1, 0])
    np.testing.assert_allclose(result["costs"], [rate, 0])
    np.testing.assert_allclose(result["net_returns"], [-rate, 0])
    np.testing.assert_allclose(result["wealth"], [1 - rate, 1 - rate])
    assert result["metrics"]["total_cost_return_units"] == pytest.approx(rate)
    assert result["metrics"]["max_drawdown"] == pytest.approx(rate)


@pytest.mark.parametrize("weights,returns", [
    ([[1], [1]], [[1e200], [1e200]]),  # compounded wealth overflows
    ([[1], [1]], [[1e160], [0]]),      # variance intermediate overflows
    ([[1e308, 1e308], [0.5, 0.5]], [[0, 0], [0, 0]]),  # invalid weight sum overflows
    ([[1.0000005], [1]], [[np.finfo(np.float64).max], [0]]),  # weighted return overflows
])
def test_nonfinite_arithmetic_cannot_become_a_report(weights, returns):
    with pytest.raises(ValueError, match="arithmetic"):
        evaluate(weights, returns, 0)


def test_unrepresentable_matrix_is_a_validation_error():
    with pytest.raises(ValueError, match="representable numeric matrices"):
        evaluate([[1], [1]], [[10**400], [0]], 0)


@pytest.mark.parametrize("weights,returns", [
    (np.array([[1 + 0j], [1 + 0j]]), [[0.01], [0.02]]),
    ([[1], [1]], np.array([[0.01 + 0.1j], [0.02 + 0.2j]])),
])
def test_complex_matrices_are_not_silently_cast_to_real(weights, returns):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match="representable numeric matrices"):
            evaluate(weights, returns, 0)


def test_large_finite_single_target_remains_valid_with_explicit_opt_in():
    result = evaluate([[1]], [[1e150]], 0, allow_single_observation=True)
    assert result["metrics"]["observations"] == 1
    assert result["metrics"]["sharpe"] is None
    assert result["metrics"]["sharpe_note"]
    assert np.isfinite(result["metrics"]["cumulative_return"])
    assert np.isfinite(result["wealth"]).all()


def test_numeric_error_does_not_change_callers_numpy_policy():
    with np.errstate(over="ignore", invalid="warn", divide="ignore"):
        policy = np.geterr()
        with pytest.raises(ValueError, match="arithmetic"):
            evaluate([[1], [1]], [[1e200], [1e200]], 0)
        assert np.geterr() == policy
