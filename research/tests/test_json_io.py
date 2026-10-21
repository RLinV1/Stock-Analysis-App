"""Unrun stdlib JSON policy regression source; no model fitting required."""

import pytest

from portfolio_lab.json_io import load_json, load_json_object, parse_json, parse_json_object


def test_utf8_types_and_large_integer_identity_are_preserved():
    raw = '{"label":"research – synthetic","seed":9007199254740993,"number":1,"flag":true,"none":null,"items":[0.0]}'
    value = parse_json(raw.encode("utf-8"))
    assert value["label"] == "research – synthetic"
    assert value["seed"] == 9007199254740993
    assert type(value["number"]) is int
    assert type(value["flag"]) is bool
    assert value["none"] is None
    assert type(value["items"][0]) is float


@pytest.mark.parametrize("raw", [
    '{"seed":7,"seed":7}', '{"nested":[{"value":1,"value":2}]}',
    r'{"seed":7,"se\u0065d":9}',
])
def test_duplicate_keys_at_any_depth_are_rejected(raw):
    with pytest.raises(ValueError, match="duplicate JSON field"):
        parse_json(raw)


@pytest.mark.parametrize("raw", ['NaN', 'Infinity', '-Infinity', '{"unused":NaN}', '[1e9999]', '-1e9999'])
def test_nonfinite_values_and_float_exponent_overflow_are_rejected(raw):
    with pytest.raises(ValueError):
        parse_json(raw)


def test_finite_float_endpoints_and_json_scalars_remain_supported():
    assert parse_json('[1e308,-1e308]') == [1e308, -1e308]
    assert parse_json('false') is False
    assert parse_json('null') is None


@pytest.mark.parametrize("raw", ['[]', 'null', '"text"', 'true', '1'])
def test_object_reader_rejects_other_top_level_types(raw):
    with pytest.raises(ValueError, match="must contain an object"):
        parse_json_object(raw)


def test_invalid_utf8_is_not_reinterpreted():
    with pytest.raises(ValueError):
        parse_json(b'\xff')


def test_file_reader_preserves_input_bytes(tmp_path):
    source = tmp_path / "input.json"
    raw = b'{\n "value": 1.0, "items": [true, null]\n}\n'
    source.write_bytes(raw)
    assert load_json(source) == {"value": 1.0, "items": [True, None]}
    assert load_json_object(source)["value"] == 1.0
    assert source.read_bytes() == raw
