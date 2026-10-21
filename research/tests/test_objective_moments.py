"""Unrun finite-intermediate and hand-derived stabilized-loss gradient gates."""

import math

import pytest
import torch

from portfolio_lab.model import negative_sharpe, stabilized_negative_sharpe


def test_two_return_loss_and_gradient_match_hand_derivative():
    portfolio = torch.tensor([.1, .2], dtype=torch.float64, requires_grad=True)
    denominator = math.sqrt(.0025 + 1e-8)
    loss = stabilized_negative_sharpe(portfolio)
    gradient, = torch.autograd.grad(loss, portfolio)
    expected = torch.tensor([
        -1 / (2 * denominator) - .15 * .05 / (2 * denominator**3),
        -1 / (2 * denominator) + .15 * .05 / (2 * denominator**3),
    ], dtype=torch.float64)
    assert float(loss.detach()) == pytest.approx(-.15 / denominator, rel=0, abs=1e-12)
    torch.testing.assert_close(gradient, expected, rtol=0, atol=1e-12)


def test_zero_return_loss_keeps_finite_declared_stabilized_gradient():
    portfolio = torch.zeros(4, dtype=torch.float64, requires_grad=True)
    loss = stabilized_negative_sharpe(portfolio)
    gradient, = torch.autograd.grad(loss, portfolio)
    assert float(loss.detach()) == 0
    torch.testing.assert_close(gradient, torch.full_like(portfolio, -2500), rtol=0, atol=1e-12)


def test_gross_objective_rejects_finite_return_variance_overflow():
    weights = torch.tensor([[1., 0.]] * 3, dtype=torch.float32)
    returns = torch.tensor([[1e20, 0.], [1., 0.], [2e20, 0.]], dtype=torch.float32)
    with pytest.raises(ValueError, match="moments became nonfinite"):
        negative_sharpe(weights, returns)


def test_finite_moments_with_unrepresentable_loss_reject():
    portfolio = torch.tensor([1e38, 1e38], dtype=torch.float32)
    with pytest.raises(ValueError, match="loss became nonfinite"):
        stabilized_negative_sharpe(portfolio)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_portfolio_moments_reject(value):
    with pytest.raises(ValueError, match="moments became nonfinite"):
        stabilized_negative_sharpe(torch.tensor([value, 0.], dtype=torch.float64))
