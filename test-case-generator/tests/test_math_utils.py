from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from math_utils import divide, clamp, parse_int


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (10, 2, 5.0),
        (7.5, 2.5, 3.0),
        (-9, 3, -3.0),
        (0, 5, 0.0),
    ],
)
def test_divide_returns_expected_quotient(a: float, b: float, expected: float) -> None:
    assert divide(a, b) == expected


def test_divide_by_zero_raises_zero_division_error_with_message() -> None:
    with pytest.raises(ZeroDivisionError, match="b must not be zero"):
        divide(1, 0)


@pytest.mark.parametrize(
    ("value", "low", "high", "expected"),
    [
        (5, 0, 10, 5),
        (-1, 0, 10, 0),
        (11, 0, 10, 10),
        (0, 0, 10, 0),
        (10, 0, 10, 10),
        (3.5, 1.0, 4.0, 3.5),
    ],
)
def test_clamp_returns_expected_value(
    value: float, low: float, high: float, expected: float
) -> None:
    assert clamp(value, low, high) == expected


def test_clamp_raises_value_error_when_low_greater_than_high() -> None:
    with pytest.raises(ValueError, match="low must be <= high"):
        clamp(5, 10, 0)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", 0),
        ("42", 42),
        ("   17   ", 17),
        ("\n\t-8\r", -8),
        ("+12", 12),
        ("00123", 123),
    ],
)
def test_parse_int_parses_base_10_integers_with_optional_whitespace(
    text: str, expected: int
) -> None:
    assert parse_int(text) == expected


@pytest.mark.parametrize("text", ["", "   ", "\n\t  "])
def test_parse_int_raises_value_error_for_empty_or_whitespace_only_strings(
    text: str,
) -> None:
    with pytest.raises(ValueError, match="empty string"):
        parse_int(text)


@pytest.mark.parametrize("text", ["abc", "12.3", "0x10", "1 2"])
def test_parse_int_raises_value_error_for_invalid_base_10_strings(text: str) -> None:
    with pytest.raises(ValueError):
        parse_int(text)
