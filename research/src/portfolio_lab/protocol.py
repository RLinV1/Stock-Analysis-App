"""Causal expanding fold plans; no model training or historical result claims."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from typing import Sequence

from .data import Dataset, Samples, make_samples


@dataclass(frozen=True)
class Fold:
    number: int
    lookback: int
    scheduled_start: str
    scheduled_end_exclusive: str
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    train_end: str
    validation_end: str
    test_start: str
    test_end: str


@dataclass(frozen=True)
class FoldPlan:
    requested_start: str
    requested_end: str
    effective_start: str
    effective_end: str
    folds: tuple[Fold, ...]
    exclusions: tuple[str, ...]


def _date(value: str) -> date:
    if not isinstance(value, str):
        raise ValueError("Dates must be canonical ISO calendar-date strings")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Dates must be canonical ISO calendar-date strings") from error
    if parsed.isoformat() != value:
        raise ValueError("Dates must be canonical ISO calendar-date strings")
    return parsed


def _dates(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("Supply a nonempty sequence of strictly increasing dates")
    result = tuple(values)
    if not result:
        raise ValueError("Supply a nonempty sequence of strictly increasing dates")
    for index, value in enumerate(result):
        _date(value)
        if index and result[index - 1] >= value:
            raise ValueError("Dates must be strictly increasing without duplicates")
    # numpy.str_ passes isinstance(str) but pickles as a numpy global that weights-only loads reject.
    return tuple(str(value) for value in result)


def _lookback(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 2:
        raise ValueError("Lookback must be a whole number of at least two observations")


def _boundary(anchor: date, fold_number: int) -> str:
    # Always calculate from the original anchor, including leap-day anniversaries.
    year = anchor.year + 2 * fold_number
    if year > 9999:
        # A Python date cannot represent the exclusive end after year 9999.
        raise ValueError("Fold calendar boundary exceeds the supported date range")
    return date(year, anchor.month, min(anchor.day, monthrange(year, anchor.month)[1])).isoformat()


def plan_walk_forward(dates: Sequence[str], test_start: str, test_end: str,
                      *, lookback: int = 50) -> FoldPlan:
    """Plan 24-month folds using only supplied sessions and prior target history.

    Indices refer to raw dataset rows. The first ``lookback`` rows provide context
    and cannot be prediction targets. Requested evaluation bounds are inclusive.
    """
    observed = _dates(dates)
    requested_start, requested_end = _date(test_start), _date(test_end)
    _lookback(lookback)
    if requested_start > requested_end:
        raise ValueError("Requested evaluation start must not follow its end")
    first_requested = bisect_left(observed, test_start)
    end = bisect_right(observed, test_end)
    first = max(first_requested, lookback)
    while first < end:
        count = first - lookback
        validation_count = max(63, (count + 9) // 10)
        if count - validation_count >= 252:
            break
        first += 1
    if first >= end:
        raise ValueError("No evaluation dates have 252 training and 63 validation targets plus lookback history")
    exclusions = ()
    if first > max(first_requested, lookback):
        exclusions = (f"Requested start {test_start} moved to {observed[first]} for minimum training/validation/lookback history",)
    elif first_requested < lookback:
        exclusions = (f"Requested start {test_start} moved to {observed[first]} for lookback history",)
    anchor = _date(observed[first])
    folds = []
    number, start = 0, first
    while start < end:
        scheduled_start = _boundary(anchor, number)
        scheduled_end = _boundary(anchor, number + 1)
        stop = min(end, bisect_left(observed, scheduled_end))
        # A long data gap can skip whole calendar intervals. Do not invent an empty fold.
        if stop <= start:
            number += 1
            continue
        count = start - lookback
        validation_count = max(63, (count + 9) // 10)
        validation_start = start - validation_count
        folds.append(Fold(
            number=len(folds), lookback=lookback,
            scheduled_start=scheduled_start, scheduled_end_exclusive=scheduled_end,
            train_indices=tuple(range(lookback, validation_start)),
            validation_indices=tuple(range(validation_start, start)),
            test_indices=tuple(range(start, stop)),
            train_end=observed[validation_start - 1], validation_end=observed[start - 1],
            test_start=observed[start], test_end=observed[stop - 1],
        ))
        start, number = stop, number + 1
    return FoldPlan(test_start, test_end, observed[first], observed[end - 1], tuple(folds), exclusions)


def make_fold_samples(dataset: Dataset, fold: Fold) -> Samples:
    """Validate fold identity/partitions and fit the existing causal scaler."""
    observed = _dates(dataset.dates)
    _lookback(fold.lookback)
    parts = (fold.train_indices, fold.validation_indices, fold.test_indices)
    if any(not isinstance(part, tuple) or not part for part in parts):
        raise ValueError("Fold partitions must be nonempty immutable index tuples")
    indices = tuple(index for part in parts for index in part)
    if any(isinstance(index, bool) or not isinstance(index, int) for index in indices):
        raise ValueError("Fold indices must be whole numbers")
    if (indices[-1] < fold.lookback or indices[-1] >= len(observed)
            or indices != tuple(range(fold.lookback, indices[-1] + 1))):
        raise ValueError("Fold partitions must be contiguous, ordered and disjoint within the dataset")
    prior_count = len(fold.train_indices) + len(fold.validation_indices)
    if len(fold.train_indices) < 252 or len(fold.validation_indices) != max(63, (prior_count + 9) // 10):
        raise ValueError("Fold does not meet the training/validation history contract")
    actual = (observed[fold.train_indices[-1]], observed[fold.validation_indices[-1]],
              observed[fold.test_indices[0]], observed[fold.test_indices[-1]])
    if actual != (fold.train_end, fold.validation_end, fold.test_start, fold.test_end):
        raise ValueError("Fold dates do not match the dataset")
    _date(fold.scheduled_start)
    _date(fold.scheduled_end_exclusive)
    if not fold.scheduled_start <= fold.test_start <= fold.test_end < fold.scheduled_end_exclusive:
        raise ValueError("Fold test dates do not fit their scheduled interval")
    stop = fold.test_indices[-1] + 1
    bounded = Dataset(dataset.dates[:stop], dataset.prices[:stop], dataset.manifest, dataset.manifest_path)
    return make_samples(bounded, fold.lookback, fold.train_end, fold.validation_end,
                        allow_single_test=True, normalization="train-only")
