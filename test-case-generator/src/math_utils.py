# src/math_utils.py

from __future__ import annotations


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ZeroDivisionError("b must not be zero")
    return a / b


def clamp(value: float, low: float, high: float) -> float:
    """Clamp value to the inclusive range [low, high]."""
    if low > high:
        raise ValueError("low must be <= high")
    if value < low:
        return low
    if value > high:
        return high
    return value


def parse_int(s: str) -> int:
    """Parse a base-10 integer from a string with optional whitespace."""
    s = s.strip()
    if s == "":
        raise ValueError("empty string")
    return int(s, 10)