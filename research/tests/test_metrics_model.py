import math

import numpy as np
import pytest
import torch

from portfolio_lab.metrics import evaluate, require_stock_bond
from portfolio_lab.model import Allocator, OBJECTIVE_CONVENTIONS, negative_sharpe


def test_costs_returns_and_initial_drawdown_by_hand():
    w = np.array([[1., 0.], [0., 1.], [0.5, 0.5]])
    r = np.array([[-0.1, 0.2], [0.5, 0.1], [-0.1, 0.1]])
    result = evaluate(w, r, 10)
    np.testing.assert_allclose(result["turnover"], [1, 2, 1])
    np.testing.assert_allclose(result["net_returns"], [-0.101, 0.098, -0.001])
    assert result["metrics"]["cumulative_return"] == pytest.approx(0.899 * 1.098 * 0.999 - 1)
    assert result["metrics"]["max_drawdown"] == pytest.approx(0.101)
    assert result["metrics"]["total_cost_return_units"] == pytest.approx(0.004)


def test_undefined_sharpe_and_invalid_weights():
    w = np.full((4, 2), 0.5)
    result = evaluate(w, np.zeros((4, 2)), 0)
    assert result["metrics"]["sharpe"] is None
    assert result["metrics"]["max_drawdown"] == 0
    with pytest.raises(ValueError, match="sum to one"):
        evaluate(w * 2, np.zeros((4, 2)), 1)


def test_single_observation_fold_keeps_actual_cost_wealth_and_null_sharpe():
    weights, returns = np.array([[0.6, 0.4]]), np.array([[0.1, -0.05]])
    with pytest.raises(ValueError):
        evaluate(weights, returns, 10)
    result = evaluate(weights, returns, 10, allow_single_observation=True)
    np.testing.assert_allclose(result["gross_returns"], [0.04])
    np.testing.assert_allclose(result["turnover"], [1])
    np.testing.assert_allclose(result["costs"], [0.001])
    np.testing.assert_allclose(result["wealth"], [1.039])
    assert result["metrics"]["observations"] == 1
    assert result["metrics"]["sharpe"] is None
    assert result["metrics"]["sharpe_note"]
    assert result["metrics"]["cumulative_return"] == pytest.approx(0.039)


@pytest.mark.parametrize("weights,returns", [([], []), ([[0.5, 0.4]], [[0.1, 0.2]]),
                                            ([[1.0]], [[float('nan')]]), ([[1.0]], [[-1.0]])])
def test_short_fold_opt_in_does_not_relax_invalid_input_guards(weights, returns):
    with pytest.raises(ValueError):
        evaluate(np.asarray(weights), np.asarray(returns), 1, allow_single_observation=True)


def test_short_fold_flag_is_explicit_boolean():
    with pytest.raises(ValueError, match="boolean"):
        evaluate(np.array([[1.0]]), np.array([[0.1]]), 1, allow_single_observation=1)


def test_baseline_universe_and_allocations():
    assets = [{"role": "stock"}, {"role": "bond"}, {"role": "other"}]
    np.testing.assert_allclose(require_stock_bond(assets, 2), [[.6, .4, 0], [.6, .4, 0]])
    with pytest.raises(ValueError, match="requires"):
        require_stock_bond([{"role": "stock"}, {"role": "other"}], 2)


def test_paper_model_weights_and_finite_gradients():
    torch.set_num_threads(1)
    model = Allocator(3)
    x = torch.randn(8, 50, 6)
    w = model(x)
    assert w.shape == (8, 3)
    assert torch.all(w >= 0)
    torch.testing.assert_close(w.sum(dim=1), torch.ones(8))
    for returns in (torch.zeros(8, 3), torch.randn(8, 3) * .01):
        model.zero_grad()
        loss = negative_sharpe(model(x), returns)
        loss.backward()
        assert torch.isfinite(loss)
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())


def test_gross_objective_and_declared_stabilization_match_hand_calculation():
    weights = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.float64)
    returns = torch.tensor([[0.1, 0.0], [0.0, 0.2]], dtype=torch.float64)
    expected = -0.15 / math.sqrt(0.0025 + 1e-8)
    assert float(negative_sharpe(weights, returns)) == pytest.approx(expected, rel=0, abs=1e-12)
    assert OBJECTIVE_CONVENTIONS["variance_epsilon"] == 1e-8
    assert OBJECTIVE_CONVENTIONS["transaction_costs"] == "evaluation_only"
