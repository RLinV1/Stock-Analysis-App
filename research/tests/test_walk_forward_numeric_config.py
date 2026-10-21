"""Unrun finite-input rejection cases; no fitting or dataset access needed."""

from dataclasses import replace

import pytest

from portfolio_lab.walk_forward import WalkForwardConfig


@pytest.mark.parametrize("field", ["learning_rate", "cost_bps"])
@pytest.mark.parametrize("value", [True, "1", None, float("nan"), float("inf"), -float("inf"), 10**400])
def test_nonfinite_or_mistyped_values_fail_before_fold_access(field, value):
    config = WalkForwardConfig("2024-01-01", "2024-01-03", 10, 8, 1, 32, 0.001, 7, 1, "cpu")
    with pytest.raises(ValueError, match=f"{field} must be a finite number"):
        replace(config, **{field: value}).for_fold(None)
