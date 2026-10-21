"""Unverified cost-aware tensor math; not enabled by any current runner mode.

The caller must supply the prior target and choose/record its window-boundary
policy. This is idealized target turnover, not drift-aware execution accounting.
"""

from __future__ import annotations

import math
from numbers import Real

import torch

from .model import SHARPE_VARIANCE_EPSILON, stabilized_negative_sharpe


COST_OBJECTIVE_CONVENTIONS = {
    "name": "stabilized_negative_net_sharpe_primitive",
    "formula": "-mean(net_returns) / sqrt(population_variance(net_returns) + variance_epsilon)",
    "net_returns": "sum(target_weights * asset_returns) - cost_bps/10000 * L1(target - previous_target)",
    "previous_target": "required caller input; cash or normalized long-only target",
    "within_window_gradients": "through adjacent current-window targets",
    "window_boundary_policy": "not selected; caller must define and retain it",
    "objective_scope": "all supplied window rows; no runner window policy selected",
    "annualization": "none in this objective",
    "variance_epsilon": SHARPE_VARIANCE_EPSILON,
    "execution": "idealized target turnover; no drift, slippage or self-financing execution model",
    "runner_integration": "none; current runner training remains gross-return",
}


def net_returns_for_objective(weights: torch.Tensor, returns: torch.Tensor,
                              cost_bps: float, *, previous_target: torch.Tensor) -> torch.Tensor:
    """Compute net returns with an explicit first-row target boundary.

    No input is converted, clipped or detached. Any gradient through the supplied
    prior target is the caller's explicit choice, not an implicit carry policy.
    """
    tensors = (weights, returns, previous_target)
    if any(not isinstance(value, torch.Tensor) for value in tensors):
        raise ValueError("Cost objective requires tensor weights, returns and previous_target")
    if any(not value.is_floating_point() for value in tensors):
        raise ValueError("Cost objective tensors must be real floating point")
    if (weights.ndim != 2 or returns.shape != weights.shape or len(weights) < 2
            or weights.shape[1] < 1 or previous_target.shape != (weights.shape[1],)):
        raise ValueError("Require matching two-row-or-longer matrices and one previous target vector")
    if any(value.dtype != weights.dtype or value.device != weights.device for value in tensors):
        raise ValueError("Cost objective tensors must share dtype and device")
    if any(not torch.isfinite(value).all() for value in tensors):
        raise ValueError("Cost objective tensors must be finite")
    if torch.any(returns <= -1):
        raise ValueError("Asset returns must be above -100%")
    if (torch.any(weights < 0)
            or not torch.allclose(weights.sum(dim=1), torch.ones_like(weights[:, 0]), atol=1e-6, rtol=0)):
        raise ValueError("Current targets must be normalized and long-only")
    cash = torch.equal(previous_target, torch.zeros_like(previous_target))
    if (torch.any(previous_target < 0)
            or (not cash and not torch.isclose(previous_target.sum(),
                                              torch.ones_like(previous_target.sum()), atol=1e-6, rtol=0))):
        raise ValueError("previous_target must be cash or normalized and long-only")
    if isinstance(cost_bps, bool) or not isinstance(cost_bps, Real):
        raise ValueError("Cost must be a finite real scalar between 0 and 100 bps")
    try:
        cost = float(cost_bps)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Cost must be a finite real scalar between 0 and 100 bps") from exc
    if not math.isfinite(cost) or not 0 <= cost <= 100:
        raise ValueError("Cost must be a finite real scalar between 0 and 100 bps")
    previous = torch.cat([previous_target.unsqueeze(0), weights[:-1]], dim=0)
    turnover = (weights - previous).abs().sum(dim=1)
    net = (weights * returns).sum(dim=1) - cost / 10000 * turnover
    if not torch.isfinite(net).all() or torch.any(net <= -1):
        raise ValueError("Cost objective accounting became nonfinite or bankrupt")
    return net


def negative_net_sharpe(weights: torch.Tensor, returns: torch.Tensor,
                        cost_bps: float, *, previous_target: torch.Tensor) -> torch.Tensor:
    """Apply the existing stabilized loss formula to explicit-boundary net returns."""
    net = net_returns_for_objective(weights, returns, cost_bps, previous_target=previous_target)
    return stabilized_negative_sharpe(net)
