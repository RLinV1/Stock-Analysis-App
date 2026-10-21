"""Declared target-turnover accounting, shared by learned and baseline portfolios."""

import math
from numbers import Real

import numpy as np


CONVENTIONS = {
    "periods_per_year": 252,
    "risk_free_rate": 0.0,
    "volatility": "population standard deviation",
    "sharpe": "sqrt(252) * mean(net_daily_returns) / std(net_daily_returns)",
    "cost": "cost_rate * sum(abs(target_weights - previous_target_weights))",
    "initial_position": "all cash; charge full initial allocation",
    "terminal_liquidation": False,
    "execution": "decision-close to next-close, idealized; no additional slippage",
    "turnover": "two-sided L1 target change; does not model drift between targets",
}


def baseline_weights(assets: list[dict], n: int) -> dict[str, np.ndarray]:
    count = len(assets)
    result = {"equal_weight": np.full((n, count), 1 / count)}
    stocks = [i for i, a in enumerate(assets) if a["role"] == "stock"]
    bonds = [i for i, a in enumerate(assets) if a["role"] == "bond"]
    if stocks and bonds:
        w = np.zeros((n, count))
        w[:, stocks] = 0.6 / len(stocks)
        w[:, bonds] = 0.4 / len(bonds)
        result["stock_bond_60_40"] = w
    return result


def require_stock_bond(assets: list[dict], n: int) -> np.ndarray:
    portfolios = baseline_weights(assets, n)
    if "stock_bond_60_40" not in portfolios:
        raise ValueError("60/40 requires declared stock and bond assets")
    return portfolios["stock_bond_60_40"]


def evaluate(weights: np.ndarray, returns: np.ndarray, cost_bps: float,
             *, allow_single_observation: bool = False) -> dict:
    if not isinstance(allow_single_observation, bool):
        raise ValueError("allow_single_observation must be a boolean")
    try:
        with np.errstate(over="raise", invalid="raise"):
            if np.iscomplexobj(weights) or np.iscomplexobj(returns):
                raise ValueError("Allocation and return matrices must be real-valued")
            w, r = np.asarray(weights, dtype=np.float64), np.asarray(returns, dtype=np.float64)
    except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
        raise ValueError("Allocations and returns must be representable numeric matrices") from exc
    minimum = 1 if allow_single_observation else 2
    if w.ndim != 2 or w.shape != r.shape or len(w) < minimum:
        required = "one row" if allow_single_observation else "two rows"
        raise ValueError(f"Require matching allocation/return matrices with at least {required}")
    if not np.isfinite(w).all() or not np.isfinite(r).all() or np.any(r <= -1):
        raise ValueError("Returns and weights must be finite, with returns above -100%")
    if isinstance(cost_bps, bool) or not isinstance(cost_bps, Real):
        raise ValueError("Cost must be between 0 and 100 basis points")
    try:
        cost = float(cost_bps)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Cost must be between 0 and 100 basis points") from exc
    if not math.isfinite(cost) or not 0 <= cost <= 100:
        raise ValueError("Cost must be between 0 and 100 basis points")
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            if np.any(w < 0) or not np.allclose(w.sum(axis=1), 1, atol=1e-6, rtol=0):
                raise ValueError("Long-only allocations must sum to one")
            previous = np.vstack([np.zeros(w.shape[1]), w[:-1]])
            turnover = np.abs(w - previous).sum(axis=1)
            gross = (w * r).sum(axis=1)
            costs = cost / 10000 * turnover
            net = gross - costs
            if np.any(net <= -1):
                raise ValueError("Costs produce a bankrupt portfolio under this accounting convention")
            wealth = np.cumprod(1 + net)
            peaks = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
            volatility = float(net.std())
            sharpe = float(np.sqrt(252) * net.mean() / volatility) if volatility > 1e-12 else None
            metrics = {
                "cumulative_return": float(wealth[-1] - 1),
                "annualized_volatility": float(volatility * np.sqrt(252)),
                "sharpe": sharpe,
                "sharpe_note": None if sharpe is not None else "Undefined: zero or near-zero volatility",
                "max_drawdown": float(np.max(1 - wealth / peaks)),
                "total_turnover": float(turnover.sum()),
                "total_cost_return_units": float(costs.sum()),
                "observations": len(net),
            }
            paths = {"gross_returns": gross, "net_returns": net, "costs": costs,
                     "turnover": turnover, "wealth": wealth}
            if (any(not np.isfinite(values).all() for values in paths.values())
                    or any(value is not None and not np.isfinite(value)
                           for key, value in metrics.items() if key != "sharpe_note")):
                raise ValueError("Evaluation arithmetic produced nonfinite results")
    except FloatingPointError as exc:
        raise ValueError("Evaluation arithmetic overflowed or became nonfinite") from exc
    return {"metrics": metrics, **{name: values.tolist() for name, values in paths.items()}}
