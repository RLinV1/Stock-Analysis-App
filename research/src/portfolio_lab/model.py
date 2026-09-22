"""The paper's small LSTM allocation architecture."""

import torch
from torch import nn


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
    # Smooth positive denominator also keeps gradients finite for a constant series.
    return -portfolio.mean() / torch.sqrt(portfolio.var(unbiased=False) + 1e-8)
