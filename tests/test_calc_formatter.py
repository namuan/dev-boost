import re

from devboost.tools.block_editor.formatters import format_calc


def _out(text: str) -> str:
    res, err = format_calc(text)
    assert err is None
    assert res is not None
    return res.strip()


def _line(text: str) -> str:
    return _out(text).splitlines()[0]


def test_arithmetic_basic():
    assert _line("10 + 20") == "10 + 20 → 30"
    assert _line("6 * 7") == "6 * 7 → 42"
    assert _line("100 / 4") == "100 / 4 → 25"
    assert _line("2 ^ 8") == "2 ^ 8 → 256"


def test_percent_of_and_plus():
    assert _line("20% of 150") == "20% of 150 → 30"
    assert _line("100 + 15%") == "100 + 15% → 115"


def test_currency_minus_percent():
    assert _line("$50 - 10%") == "$50 - 10% → $45"


def test_variables_currency_plus_percent():
    text = "\n".join([
        "price = $100",
        "tax = 8%",
        "price + tax",
    ])
    out = _out(text)
    lines = out.splitlines()
    assert lines[0] == "price = $100 → $100"
    assert lines[1] == "tax = 8% → 8%"
    assert lines[2] == "price + tax → $108"


def test_duration_addition_hours_minutes():
    line = _line("2 hours + 30 min")
    assert re.match(r"^2 hours \+ 30 min → (2 h 30 min|150 min)$", line)


def test_assignment_and_recalc_arrow_replaced():
    text = "\n".join([
        "x = 100",
        "x + 10% → 111",
        "x - 10%",
    ])
    out = _out(text)
    lines = out.splitlines()
    assert lines[1] == "x + 10% → 110"
    assert lines[2] == "x - 10% → 90"


def test_inline_equals_expression():
    assert _line("100/10=") == "100/10 = 10"
