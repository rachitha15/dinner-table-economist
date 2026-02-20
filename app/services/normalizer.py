import re
from typing import Any


YEAR_RE = re.compile(r"(\d{4}(?:-\d{2})?)")
MONTH_NAME_TO_NUM = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return [row for row in payload["data"] if isinstance(row, dict)]
        if isinstance(payload.get("rows"), list):
            return [row for row in payload["rows"] if isinstance(row, dict)]
    return []


def _match_filters(rows: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    if not filters:
        return rows
    filtered: list[dict[str, Any]] = []
    for row in rows:
        ok = True
        for key, value in filters.items():
            if key not in row:
                continue
            if str(row[key]) != str(value):
                ok = False
                break
        if ok:
            filtered.append(row)
    return filtered if filtered else rows


def _find_year(row: dict[str, Any]) -> str | None:
    # Prefer explicit 'year' key over base_year or other year-like fields
    if "year" in row:
        candidate = str(row["year"])
        match = YEAR_RE.search(candidate)
        if match:
            year = match.group(1)
        else:
            year = None
    else:
        year = None

    # Fall back to other keys containing 'year' but skip base_year
    if year is None:
        for key in row:
            if "year" in key.lower() and key.lower() != "base_year":
                candidate = str(row[key])
                match = YEAR_RE.search(candidate)
                if match:
                    year = match.group(1)
                    break

    # If month info exists, append it to year
    month = None
    if "month" in row:
        month_val = row.get("month")
        if isinstance(month_val, str):
            month = MONTH_NAME_TO_NUM.get(month_val.strip().lower())
        elif isinstance(month_val, (int, float)):
            month = f"{int(month_val):02d}"
    if month is None:
        for key in row:
            if "month" in key.lower():
                month_val = row.get(key)
                if isinstance(month_val, str):
                    month = MONTH_NAME_TO_NUM.get(month_val.strip().lower())
                elif isinstance(month_val, (int, float)):
                    month = f"{int(month_val):02d}"
                if month:
                    break

    if year and month:
        return f"{year}-{month}"
    if year:
        return year
    # Fallback: any value with a year-like pattern
    for value in row.values():
        if isinstance(value, str):
            match = YEAR_RE.search(value)
            if match:
                return match.group(1)
    return None


def _find_value(row: dict[str, Any]) -> float | None:
    # Prefer common numeric keys
    preferred_keys = [
        "value",
        "index_value",
        "index",
        "rate",
        "val",
        "current_price",
        "constant_price",
    ]
    for key in preferred_keys:
        if key in row and isinstance(row[key], (int, float, str)):
            try:
                return float(row[key])
            except ValueError:
                pass
    # Fallback: first numeric-looking field, skipping date/time-like fields
    for key, value in row.items():
        if isinstance(key, str) and ("year" in key.lower() or "month" in key.lower()):
            continue
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def normalize_timeseries(payload: Any, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = _extract_rows(payload)
    rows = _match_filters(rows, filters or {})

    series_map: dict[str, float] = {}
    for row in rows:
        year = _find_year(row)
        value = _find_value(row)
        if year is None or value is None:
            continue
        if year not in series_map:
            series_map[year] = value

    series = [
        {"year": year, "value": value}
        for year, value in sorted(series_map.items())
    ]

    values = [point["value"] for point in series]
    summary = {}
    if values:
        summary = {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
        }

    return {"series": series, "summary": summary}
