"""Unambiguous UTF-8 JSON for explicit local control and owned artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("JSON floating-point number exceeds finite representation")
    return result


def parse_json(content: str | bytes) -> object:
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    if not isinstance(content, str):
        raise TypeError("JSON content must be text or UTF-8 bytes")
    return json.loads(content, object_pairs_hook=_object, parse_constant=_constant, parse_float=_float)


def parse_json_object(content: str | bytes) -> dict:
    result = parse_json(content)
    if not isinstance(result, dict):
        raise ValueError("JSON document must contain an object")
    return result


def load_json(path: Path) -> object:
    return parse_json(Path(path).read_bytes())


def load_json_object(path: Path) -> dict:
    return parse_json_object(Path(path).read_bytes())
