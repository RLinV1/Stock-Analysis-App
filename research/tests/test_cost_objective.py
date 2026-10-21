"""Unrun explicit-boundary net-objective math gates; no training is enabled."""

import math

import pytest
import torch

from portfolio_lab.cost_objective import negative_net_sharpe, net_returns_for_objective
from portfolio_lab.metrics import evaluate
from portfolio_lab.model import SHARPE_VARIANCE_EPSILON, negative_sharpe


def inputs():
    weights = torch.tensor([[1., 0.], [0., 1.], [.5, .5]], dtype=torch.float64)
    returns = torch.tensor([[-.1, .2], [.5, .1], [-.1, .1]], dtype=torch.float64)
    return weights, returns, torch.zeros(2, dtype=torch.float64)


def test_initial_cash_net_paths_and_loss_match_declared_hand_accounting():
    weights, returns, previous = inputs()
    net = net_returns_for_objective(weights, returns, 10, previous_target=previous)
    expected = torch.tensor([-.101, .098, -.001], dtype=torch.float64)
    torch.testing.assert_close(net, expected, rtol=0, atol=1e-15)
    evaluated = evaluate(weights.numpy(), returns.numpy(), 10)
    torch.testing.assert_close(net, torch.tensor(evaluated["net_returns"], dtype=torch.float64), rtol=0, atol=1e-15)
    mean = sum(expected.tolist()) / 3
    variance = sum((value - mean) ** 2 for value in expected.tolist()) / 3
    expected_loss = -mean / math.sqrt(variance + SHARPE_VARIANCE_EPSILON)
    assert float(negative_net_sharpe(weights, returns, 10, previous_target=previous)) == pytest.approx(expected_loss, rel=0, abs=1e-12)


def test_explicit_carried_target_avoids_another_cash_entry_and_preserves_join():
    weights = torch.tensor([[1., 0.], [.5, .5], [.5, .5], [0., 1.]], dtype=torch.float64)
    returns = torch.tensor([[.1, 0.], [.02, .04], [.02, .04], [0., .1]], dtype=torch.float64)
    cash = torch.zeros(2, dtype=torch.float64)
    whole = net_returns_for_objective(weights, returns, 10, previous_target=cash)
    first = net_returns_for_objective(weights[:2], returns[:2], 10, previous_target=cash)
    carried = net_returns_for_objective(weights[2:], returns[2:], 10, previous_target=weights[1])
    reset = net_returns_for_objective(weights[2:], returns[2:], 10, previous_target=cash)
    torch.testing.assert_close(torch.cat([first, carried]), whole, rtol=0, atol=0)
    assert float(carried[0]) == pytest.approx(.03)
    assert float(reset[0]) == pytest.approx(.029)


def test_zero_cost_matches_gross_loss_and_gradient():
    weights, returns, previous = inputs()
    weights.requires_grad_(True)
    gross = negative_sharpe(weights, returns)
    net = negative_net_sharpe(weights, returns, 0, previous_target=previous)
    gross_gradient, = torch.autograd.grad(gross, weights, retain_graph=True)
    net_gradient, = torch.autograd.grad(net, weights)
    torch.testing.assert_close(net, gross, rtol=0, atol=0)
    torch.testing.assert_close(net_gradient, gross_gradient, rtol=0, atol=0)


def test_net_objective_gradient_matches_finite_difference_away_from_turnover_kinks():
    logits = torch.tensor([[2., 0.], [-1., 1.], [.5, -.5]], dtype=torch.float64, requires_grad=True)
    returns = torch.tensor([[.01, -.02], [.03, .02], [-.01, .04]], dtype=torch.float64)
    previous = torch.tensor([.2, .8], dtype=torch.float64)
    def objective(values):
        return negative_net_sharpe(values.softmax(dim=1), returns, 10, previous_target=previous)
    assert torch.autograd.gradcheck(objective, (logits,), eps=1e-6, atol=1e-5, rtol=1e-4)


@pytest.mark.parametrize("cost", [True, False, "1", None, [1], float("nan"), float("inf"), -.1, 100.1, 10**400])
def test_invalid_scalar_cost_is_rejected(cost):
    weights, returns, previous = inputs()
    with pytest.raises(ValueError, match="Cost must"):
        net_returns_for_objective(weights, returns, cost, previous_target=previous)


def test_tensor_cost_is_not_silently_converted():
    weights, returns, previous = inputs()
    with pytest.raises(ValueError, match="real scalar"):
        net_returns_for_objective(weights, returns, torch.tensor(1.), previous_target=previous)


def test_previous_target_is_required():
    weights, returns, _ = inputs()
    with pytest.raises(TypeError, match="previous_target"):
        net_returns_for_objective(weights, returns, 1)


@pytest.mark.parametrize("case", ["not_tensor", "integer", "complex", "one_row", "shape",
                                  "previous_shape", "dtype", "negative_weight", "unnormalized",
                                  "negative_previous", "partial_previous", "nonfinite", "bankrupt_asset"])
def test_invalid_tensor_contract_rejects(case):
    weights, returns, previous = inputs()
    if case == "not_tensor":
        weights = weights.tolist()
    elif case == "integer":
        weights = weights.to(torch.int64)
    elif case == "complex":
        returns = returns.to(torch.complex128)
    elif case == "one_row":
        weights, returns = weights[:1], returns[:1]
    elif case == "shape":
        returns = returns[:, :1]
    elif case == "previous_shape":
        previous = previous.unsqueeze(0)
    elif case == "dtype":
        returns = returns.to(torch.float32)
    elif case == "negative_weight":
        weights[0] = torch.tensor([1.1, -.1], dtype=torch.float64)
    elif case == "unnormalized":
        weights *= .5
    elif case == "negative_previous":
        previous = torch.tensor([1.1, -.1], dtype=torch.float64)
    elif case == "partial_previous":
        previous = torch.tensor([.2, .3], dtype=torch.float64)
    elif case == "nonfinite":
        returns[0, 0] = float("inf")
    else:
        returns[0, 0] = -1
    with pytest.raises(ValueError):
        net_returns_for_objective(weights, returns, 10, previous_target=previous)


def test_mismatched_device_rejects_without_gpu_tensors():
    weights, returns, previous = inputs()
    returns = torch.empty_like(returns, device="meta")
    with pytest.raises(ValueError, match="dtype and device"):
        net_returns_for_objective(weights, returns, 10, previous_target=previous)


def test_explicit_prior_target_gradient_is_not_silently_detached():
    weights, returns, _ = inputs()
    previous = torch.tensor([.2, .8], dtype=torch.float64, requires_grad=True)
    loss = negative_net_sharpe(weights, returns, 10, previous_target=previous)
    gradient, = torch.autograd.grad(loss, previous)
    assert torch.isfinite(gradient).all()
    assert torch.any(gradient != 0)


def test_cost_induced_bankruptcy_is_rejected():
    weights = torch.tensor([[1., 0.], [1., 0.]], dtype=torch.float64)
    returns = torch.tensor([[-.999, 0.], [-.5, 0.]], dtype=torch.float64)
    with pytest.raises(ValueError, match="bankrupt"):
        net_returns_for_objective(weights, returns, 100, previous_target=torch.zeros(2, dtype=torch.float64))


def test_finite_returns_with_overflowing_variance_do_not_become_zero_loss():
    weights = torch.tensor([[1., 0.]] * 3, dtype=torch.float32)
    returns = torch.tensor([[1e20, 0.], [1., 0.], [2e20, 0.]], dtype=torch.float32)
    with pytest.raises(ValueError, match="moments became nonfinite"):
        negative_net_sharpe(weights, returns, 0, previous_target=torch.zeros(2, dtype=torch.float32))
