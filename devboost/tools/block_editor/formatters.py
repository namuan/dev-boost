import json
import logging
import re
from dataclasses import dataclass

from defusedxml.minidom import parseString

logger = logging.getLogger(__name__)


def format_json(text: str) -> tuple[str | None, str | None]:
    """Attempt to pretty-format JSON.

    Returns (formatted_text, error_message). If formatting fails, formatted_text is None and error_message contains context.
    """
    try:
        parsed = json.loads(text)
        formatted = json.dumps(parsed, indent=2, sort_keys=True, ensure_ascii=False)
        return formatted, None
    except Exception as exc:
        msg = f"JSON format error: {exc}"
        logger.warning(msg)
        return None, msg


def format_xml(text: str) -> tuple[str | None, str | None]:
    """Attempt to pretty-format XML using minidom.

    Returns (formatted_text, error_message). Note: minidom may add whitespace/newlines.
    """
    try:
        dom = parseString(text)
        formatted = dom.toprettyxml(indent="  ")
        return formatted, None
    except Exception as exc:
        msg = f"XML format error: {exc}"
        logger.warning(msg)
        return None, msg


def try_auto_format(language: str, text: str) -> tuple[str | None, str | None]:
    """Auto-format content if language is supported.

    Supports: json, xml. Returns (formatted, error). Unsupported languages return (None, None).
    """
    lang = (language or "").lower()
    if lang == "json":
        return format_json(text)
    if lang == "xml":
        return format_xml(text)
    if lang == "calc":
        return format_calc(text)
    return None, None


@dataclass
class CalcValue:
    kind: str
    amount: float
    unit: str | None = None


_re_currency = re.compile(r"^\s*(?P<symbol>\$)\s*(?P<num>-?\d+(?:\.\d+)?)\s*$")
_re_number = re.compile(r"^\s*(?P<num>-?\d+(?:\.\d+)?)\s*$")
_re_percent = re.compile(r"^\s*(?P<num>-?\d+(?:\.\d+)?)\s*%\s*$")
_re_assign = re.compile(r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.+?)\s*$")
_re_of = re.compile(r"^\s*(?P<left>.+?)\s+of\s+(?P<right>.+?)\s*$", re.IGNORECASE)
_re_hours = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*(hours?|hrs?|h)", re.IGNORECASE)
_re_minutes = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*(minutes?|mins?|min|m)", re.IGNORECASE)
_re_seconds = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*(seconds?|secs?|sec|s)", re.IGNORECASE)


def _parse_value(token: str, vars_map: dict[str, CalcValue]) -> CalcValue | None:
    t = token.strip()
    if t in vars_map:
        return vars_map[t]
    m = _re_currency.match(t)
    if m:
        return CalcValue("currency", float(m.group("num")), m.group("symbol"))
    m = _re_percent.match(t)
    if m:
        return CalcValue("percent", float(m.group("num")) / 100.0)
    m = _re_number.match(t)
    if m:
        return CalcValue("number", float(m.group("num")))
    dur_minutes = 0.0
    for rx in (_re_hours, _re_minutes, _re_seconds):
        for dm in rx.finditer(t):
            v = float(dm.group("num"))
            if rx is _re_hours:
                dur_minutes += v * 60.0
            elif rx is _re_minutes:
                dur_minutes += v
            else:
                dur_minutes += v / 60.0
    if dur_minutes > 0:
        return CalcValue("duration", dur_minutes, "min")
    return None


def _format_value(v: CalcValue) -> str:
    if v.kind == "currency":
        return f"{v.unit}{_fmt_num(v.amount)}"
    if v.kind == "percent":
        return f"{_fmt_num(v.amount * 100)}%"
    if v.kind == "duration":
        total = int(round(v.amount))
        h = total // 60
        m = total % 60
        if h > 0:
            return f"{h} h {m} min" if m > 0 else f"{h} h"
        return f"{m} min"
    return _fmt_num(v.amount)


def _fmt_num(n: float) -> str:
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f"{n:.4f}".rstrip("0").rstrip(".")


def _op_pow(a: CalcValue, b: CalcValue) -> CalcValue:
    res = a.amount**b.amount
    kind = "currency" if a.kind == "currency" else "number"
    unit = a.unit if kind == "currency" else None
    return CalcValue(kind, res, unit)


def _op_mul_div(a: CalcValue, b: CalcValue, op: str) -> CalcValue:
    res = a.amount * b.amount if op == "*" else (a.amount / b.amount if b.amount != 0 else float("nan"))
    kind = "currency" if a.kind == "currency" else "number"
    unit = a.unit if kind == "currency" else None
    return CalcValue(kind, res, unit)


def _op_add_sub(a: CalcValue, b: CalcValue, op: str) -> CalcValue:
    if b.kind == "percent":
        delta = a.amount * b.amount
        res = a.amount + delta if op == "+" else a.amount - delta
        kind = "currency" if a.kind == "currency" else "number"
        unit = a.unit if kind == "currency" else None
        return CalcValue(kind, res, unit)
    if a.kind == "duration" and b.kind == "duration":
        res = a.amount + b.amount if op == "+" else a.amount - b.amount
        return CalcValue("duration", res, "min")
    res = a.amount + b.amount if op == "+" else a.amount - b.amount
    kind = "currency" if (a.kind == "currency" or b.kind == "currency") else "number"
    unit = a.unit if kind == "currency" else (b.unit if b.kind == "currency" else None)
    return CalcValue(kind, res, unit)


def _binary_op(a: CalcValue, op: str, b: CalcValue) -> CalcValue | None:
    if op == "^":
        return _op_pow(a, b)
    if op in {"*", "/"}:
        return _op_mul_div(a, b, op)
    if op in {"+", "-"}:
        return _op_add_sub(a, b, op)
    return None


def _apply_of(left: CalcValue, right: CalcValue) -> CalcValue | None:
    if left.kind == "percent":
        base = right.amount
        res = base * left.amount
        unit = right.unit
        kind = right.kind
        return CalcValue(kind, res, unit)
    return None


def _eval_expression(expr: str, vars_map: dict[str, CalcValue]) -> CalcValue | None:
    m = _re_of.match(expr)
    if m:
        l = _parse_value(m.group("left"), vars_map)
        r = _parse_value(m.group("right"), vars_map)
        if l and r:
            return _apply_of(l, r)
        return None
    parts = re.split(r"\s*([\^*/+-])\s*", expr)
    if not parts:
        return None
    cur = _parse_value(parts[0], vars_map)
    if cur is None:
        return None
    i = 1
    while i < len(parts) - 1:
        op = parts[i]
        nxt = _parse_value(parts[i + 1], vars_map)
        if nxt is None:
            return None
        cur = _binary_op(cur, op, nxt)
        if cur is None:
            return None
        i += 2
    return cur


def format_calc(text: str) -> tuple[str | None, str | None]:
    try:
        vars_map: dict[str, CalcValue] = {}
        out_lines: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                out_lines.append(raw_line)
                continue
            am = _re_assign.match(line)
            if am:
                val = _parse_value(am.group("value"), vars_map)
                if val is not None:
                    vars_map[am.group("name")] = val
                    formatted_val = _format_value(val)
                    expr = raw_line.split("→", 1)[0].strip()
                    out_lines.append(f"{expr} → {formatted_val}")
                    logger.info("calc assign '%s' -> %s", expr, formatted_val)
                else:
                    out_lines.append(raw_line)
                continue
            m_eq = re.match(r"^(?P<expr>.+?)\s*=\s*$", line)
            if m_eq:
                expr = m_eq.group("expr").strip()
                result = _eval_expression(expr, vars_map)
                if result is None:
                    out_lines.append(raw_line)
                    continue
                formatted = _format_value(result)
                out_lines.append(f"{expr} = {formatted}")
                logger.info("calc inline '=' '%s' -> %s", expr, formatted)
                continue
            expr = line.split("→", 1)[0].strip()
            result = _eval_expression(expr, vars_map)
            if result is None:
                out_lines.append(raw_line)
                continue
            formatted = _format_value(result)
            out_lines.append(f"{expr} → {formatted}")
            logger.info("calc eval '%s' -> %s", expr, formatted)
        return "\n".join(out_lines), None
    except Exception as exc:
        msg = f"Calc format error: {exc}"
        logger.warning(msg)
        return None, msg
