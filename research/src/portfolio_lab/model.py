"""The paper's small LSTM allocation architecture."""

import torch
from torch import nn


SHARPE_VARIANCE_EPSILON = 1e-8
OBJECTIVE_CONVENTIONS = {
    "name": "stabilized_negative_gross_sharpe",
    "formula": "-mean(gross_returns) / sqrt(population_variance(gross_returns) + variance_epsilon)",
    "variance_epsilon": SHARPE_VARIANCE_EPSILON,
    "training_scope": "each chronological minibatch",
    "validation_scope": "all validation targets; select minimum validation loss",
    "annualization": "none in the training or validation objective",
    "transaction_costs": "evaluation_only",
}


def objective_conventions(window: str) -> dict:
    """Declare the local objective window without changing the loss formula."""
    if not isinstance(window, str) or window not in ("minibatch", "full-training"):
        raise ValueError("objective_window must be minibatch or full-training")
    return {**OBJECTIVE_CONVENTIONS,
            "training_scope": (OBJECTIVE_CONVENTIONS["training_scope"] if window == "minibatch"
                               else "all training targets; one optimizer update per epoch")}


class Allocator(nn.Module):
    def __init__(self, assets: int, hidden_size: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(2 * assets, hidden_size, num_layers=1, batch_first=True)
        self.output = nn.Linear(hidden_size, assets)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        sequence, _ = self.lstm(x)
        return self.output(sequence[:, -1]).softmax(dim=-1)


def negative_sharpe(weights: torch.Tensor, returns: torch.Tensor) -> torch.Tensor:
    portfolio = (weights * returns).sum(dim=-1)
    return stabilized_negative_sharpe(portfolio)


def stabilized_negative_sharpe(portfolio: torch.Tensor) -> torch.Tensor:
    """Apply the existing formula, rejecting invalid intermediate moments."""
    mean, variance = portfolio.mean(), portfolio.var(unbiased=False)
    if not torch.isfinite(mean) or not torch.isfinite(variance):
        raise ValueError("Objective moments became nonfinite")
    # Smooth positive denominator also keeps gradients finite for a constant series.
    loss = -mean / torch.sqrt(variance + SHARPE_VARIANCE_EPSILON)
    if not torch.isfinite(loss):
        raise ValueError("Objective loss became nonfinite")
    return loss
