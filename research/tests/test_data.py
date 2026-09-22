import csv
import json

import numpy as np
import pytest

from portfolio_lab.data import file_hash, load_dataset, make_samples, save_json, synthetic_dataset


def mutate_csv(manifest_path, mutation):
    manifest = json.loads(manifest_path.read_text())
    csv_path = manifest_path.parent / manifest["csv"]
    with csv_path.open(newline="") as handle:
        rows = list(csv.reader(handle))
    mutation(rows)
    with csv_path.open("w", newline="") as handle:
        csv.writer(handle).writerows(rows)
    manifest["sha256"] = file_hash(csv_path)
    save_json(manifest_path, manifest)


@pytest.mark.parametrize("invalid", ["nan", "inf", "0", "-1", ""])
def test_reject_invalid_prices(tmp_path, invalid):
    path = synthetic_dataset(tmp_path / "d", 120)
    mutate_csv(path, lambda rows: rows[4].__setitem__(1, invalid))
    with pytest.raises(ValueError, match="Prices"):
        load_dataset(path)


def test_reject_duplicate_dates_and_wrong_checksum(tmp_path):
    path = synthetic_dataset(tmp_path / "d", 120)
    with (path.parent / "prices.csv").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="checksum"):
        load_dataset(path)
    mutate_csv(path, lambda rows: rows.__setitem__(4, rows[3]))
    with pytest.raises(ValueError, match="strictly increasing"):
        load_dataset(path)


def test_manifest_policy_and_column_order(tmp_path):
    path = synthetic_dataset(tmp_path / "d", 120)
    manifest = json.loads(path.read_text())
    manifest["missing_data"] = "backfill"
    save_json(path, manifest)
    with pytest.raises(ValueError, match="missing-data policy"):
        load_dataset(path)
    manifest["missing_data"] = "reject"
    manifest["assets"] = manifest["assets"][::-1]
    save_json(path, manifest)
    with pytest.raises(ValueError, match="columns"):
        load_dataset(path)


def test_next_period_alignment_and_no_future_scaler_leakage(tmp_path):
    dataset = load_dataset(synthetic_dataset(tmp_path / "d", 120))
    samples = make_samples(dataset, 10, dataset.dates[70], dataset.dates[90])
    np.testing.assert_allclose(samples.y[0], dataset.prices[10] / dataset.prices[9] - 1, rtol=1e-6)
    recovered_features = samples.x[0] * samples.scale + samples.mean
    np.testing.assert_allclose(recovered_features[-1, ::2], dataset.prices[9], rtol=1e-6)
    assert samples.dates[samples.train][-1] < samples.dates[samples.validation][0]
    assert samples.dates[samples.validation][-1] < samples.dates[samples.test][0]
    dataset.prices[91:] *= 5
    changed = make_samples(dataset, 10, dataset.dates[70], dataset.dates[90])
    np.testing.assert_array_equal(samples.mean, changed.mean)
    np.testing.assert_array_equal(samples.scale, changed.scale)
    np.testing.assert_array_equal(samples.x[samples.train | samples.validation], changed.x[changed.train | changed.validation])
    # First held-out decision uses information only through the final validation close.
    np.testing.assert_array_equal(samples.x[samples.test][0], changed.x[changed.test][0])


def test_overlapping_or_empty_splits_are_rejected(tmp_path):
    d = load_dataset(synthetic_dataset(tmp_path / "d", 120))
    with pytest.raises(ValueError, match="train_end <"):
        make_samples(d, 10, d.dates[90], d.dates[70])
    with pytest.raises(ValueError, match="at least two"):
        make_samples(d, 50, d.dates[10], d.dates[100])
