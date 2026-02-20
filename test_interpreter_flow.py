import asyncio
import json
from typing import Any
import traceback
import re

from fastmcp import Client

from app.services.selector_a import select_indicator_params
from app.services.selector_b import select_filters
from app.services.interpreter import interpret_claim
from app.services.normalizer import normalize_timeseries

MOSPI_MCP_URLS = ["https://mcp.mospi.gov.in", "https://mcp.mospi.gov.in/mcp"]
MAX_YEARS = 3
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
REL_TIME_RE = re.compile(r"\b(years ago|decade|decades|since|in the \d{2}s)\b", re.IGNORECASE)


def _get_payload(result: Any) -> Any:
    return getattr(result, "structured_content", None) or getattr(result, "data", None) or result


def _write_json(name: str, payload: Any) -> None:
    with open(name, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _log_debug(message: str) -> None:
    with open("debug_log.txt", "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return [row for row in payload["data"] if isinstance(row, dict)]
        if isinstance(payload.get("rows"), list):
            return [row for row in payload["rows"] if isinstance(row, dict)]
    return []


def _find_indicator_label(dataset: str, step2_payload: dict, params: dict) -> str:
    if dataset == "PLFS":
        freq = params.get("frequency_code")
        if isinstance(step2_payload, dict):
            indicators = step2_payload.get("indicators_by_frequency", {})
            for key, items in indicators.items():
                if freq and str(freq) in key:
                    for item in items:
                        if str(item.get("indicator_code")) == str(params.get("indicator_code")):
                            return item.get("description", "PLFS indicator")
        return "PLFS indicator"
    if dataset == "NAS":
        indicators = step2_payload.get("data", {}).get("indicator", []) if isinstance(step2_payload, dict) else []
        for item in indicators:
            if str(item.get("indicator_code")) == str(params.get("indicator_code")):
                return item.get("description", "NAS indicator")
        return "NAS indicator"
    if dataset == "ASI":
        indicators = step2_payload.get("indicators", []) if isinstance(step2_payload, dict) else []
        for item in indicators:
            if str(item.get("indicator_code")) == str(params.get("indicator_code")):
                return item.get("indicator_name", "ASI indicator")
        return "ASI indicator"
    if dataset == "ENERGY":
        indicators = step2_payload.get("data", {}).get("indicator", []) if isinstance(step2_payload, dict) else []
        for item in indicators:
            if str(item.get("indicator_code")) == str(params.get("indicator_code")):
                return item.get("description", "Energy indicator")
        return "Energy indicator"
    if dataset == "CPI":
        return f"CPI {params.get('base_year', '')} {params.get('series', '')} {params.get('level', '')}".strip()
    return dataset


async def run_flow(claim: str, dataset: str):
    last_error = None
    for url in MOSPI_MCP_URLS:
        try:
            async with Client(url) as client:
                _log_debug(f"Using MCP URL: {url}")
                step2 = await client.call_tool(
                    "2_get_indicators",
                    {"dataset": dataset, "user_query": claim},
                )
                step2_payload = _get_payload(step2)
                _write_json(f"debug_step2_{dataset}.json", step2_payload)
                selector_a = await select_indicator_params(claim, dataset, step2_payload)
                params = selector_a.get("params", {})
                _write_json(f"debug_selector_a_{dataset}.json", selector_a)

                step3 = await client.call_tool(
                    "3_get_metadata",
                    {"dataset": dataset, **params},
                )
                step3_payload = _get_payload(step3)
                _write_json(f"debug_step3_{dataset}.json", step3_payload)
                selector_b = await select_filters(
                    claim,
                    dataset,
                    selector_a.get("claim_type", "other"),
                    step3_payload,
                    selector_a.get("params", {}),
                )
                filters = selector_b.get("filters", {})
                claim_type = selector_a.get("claim_type", "other")
                benchmark_filters = selector_b.get("benchmark_filters")
                if claim_type not in ("level", "comparison", "intra_comparison"):
                    benchmark_filters = None
                optional_drop_filters = selector_b.get("optional_drop_filters", [])
                _write_json(f"debug_selector_b_{dataset}.json", selector_b)

                def _valid_values(step3_payload: dict[str, Any]) -> dict[str, dict[str, str]]:
                    # Map from param name -> {label: code, code: code}
                    mapping: dict[str, dict[str, str]] = {}
                    data = step3_payload.get("data") if isinstance(step3_payload, dict) else None
                    if isinstance(data, dict):
                        items = data.items()
                    elif isinstance(data, list) and data:
                        items = data[0].items()
                    else:
                        items = []
                    for key, values in items:
                        if isinstance(values, list):
                            for entry in values:
                                if isinstance(entry, dict):
                                    code_key = None
                                    name_key = None
                                    for k in entry.keys():
                                        if k.endswith("_code"):
                                            code_key = k
                                        if k.endswith("_name"):
                                            name_key = k
                                    if code_key:
                                        code = str(entry.get(code_key))
                                        mapping.setdefault(code_key, {})[code] = code
                                        if name_key:
                                            name = str(entry.get(name_key))
                                            mapping[code_key][name] = code
                    return mapping

                def _clean_filters(filters_in: dict[str, Any], step3_payload: dict[str, Any]) -> dict[str, Any]:
                    api_params = step3_payload.get("api_params", []) if isinstance(step3_payload, dict) else []
                    allowed = {p["name"] for p in api_params if p.get("name")}
                    valid_map = _valid_values(step3_payload)
                    cleaned: dict[str, Any] = {}
                    for key, value in filters_in.items():
                        if key not in allowed:
                            continue
                        if key in valid_map:
                            if isinstance(value, str):
                                cleaned[key] = valid_map[key].get(value, value)
                            else:
                                cleaned[key] = value
                        else:
                            cleaned[key] = value
                    return cleaned

                filters = _clean_filters(filters, step3_payload)
                if isinstance(benchmark_filters, dict):
                    benchmark_filters = _clean_filters(benchmark_filters, step3_payload)

                has_time = YEAR_RE.search(claim) or REL_TIME_RE.search(claim)
                if not has_time and "year" in filters and isinstance(filters["year"], str):
                    if isinstance(step3_payload, dict):
                        year_list = step3_payload.get("data", {}).get("year")
                        if isinstance(year_list, list) and year_list:
                            years = [str(item.get("year", "")) for item in year_list if item.get("year")]
                            if years:
                                filters["year"] = ",".join(years[:5])
                                if isinstance(benchmark_filters, dict):
                                    benchmark_filters["year"] = filters["year"]

                def _required_params(step3_payload: dict[str, Any]) -> set[str]:
                    api_params = step3_payload.get("api_params", []) if isinstance(step3_payload, dict) else []
                    return {p["name"] for p in api_params if p.get("required")}

                async def _fetch_series(active_filters: dict[str, Any], label: str) -> dict[str, Any]:
                    def _expand_filters(filters: dict[str, Any]) -> list[dict[str, Any]]:
                        expanded = [filters]
                        for key, value in list(filters.items()):
                            if isinstance(value, str) and "," in value:
                                parts = [item.strip() for item in value.split(",") if item.strip()]
                                if key == "year" and len(parts) > MAX_YEARS:
                                    parts = parts[:MAX_YEARS]
                                expanded = [
                                    {**item, key: part} for item in expanded for part in parts
                                ]
                        return expanded

                    async def _run_once(filters_to_use: dict[str, Any], attempt: str) -> list[dict[str, Any]]:
                        rows: list[dict[str, Any]] = []
                        expanded_filters = _expand_filters(filters_to_use)
                        for idx, one_filter in enumerate(expanded_filters):
                            _write_json(f"debug_step4_{dataset}_{label}_{attempt}_{idx}_filters.json", one_filter)
                            step4 = await client.call_tool(
                                "4_get_data",
                                {"dataset": dataset, "filters": one_filter},
                            )
                            step4_payload = _get_payload(step4)
                            _write_json(f"debug_step4_{dataset}_{label}_{attempt}_{idx}.json", step4_payload)
                            rows.extend(_extract_rows(step4_payload))
                        return rows

                    combined_rows = await _run_once(active_filters, "primary")
                    if combined_rows:
                        return normalize_timeseries(combined_rows, active_filters)

                    # One retry: drop up to 3 optional filters suggested by selector_b
                    required = _required_params(step3_payload)
                    drops = [k for k in optional_drop_filters if k in active_filters and k not in required]
                    drops = drops[:3]
                    if drops:
                        reduced = {k: v for k, v in active_filters.items() if k not in drops}
                        combined_rows = await _run_once(reduced, "retry")
                        return normalize_timeseries(combined_rows, reduced)

                    return normalize_timeseries([], active_filters)

                primary_series = await _fetch_series(filters, "primary")
                def _label_from_filters(primary: dict[str, Any], benchmark: dict[str, Any]) -> tuple[str, str]:
                    diffs = []
                    for key in set(primary.keys()) | set(benchmark.keys()):
                        if primary.get(key) != benchmark.get(key):
                            diffs.append((key, primary.get(key), benchmark.get(key)))
                    if not diffs:
                        return ("primary", "benchmark")
                    # Use first diff as label
                    key, pval, bval = diffs[0]
                    return (f"{key}={pval}", f"{key}={bval}")

                if isinstance(benchmark_filters, dict) and benchmark_filters:
                    benchmark_series = await _fetch_series(benchmark_filters, "benchmark")
                    primary_label, benchmark_label = _label_from_filters(filters, benchmark_filters)
                    normalized = {
                        "primary_label": primary_label,
                        "benchmark_label": benchmark_label,
                        "primary": primary_series,
                        "benchmark": benchmark_series,
                    }
                else:
                    normalized = primary_series

                indicator_label = _find_indicator_label(dataset, step2_payload, params)

                interpretation = await interpret_claim(
                    claim=claim,
                    dataset=dataset,
                    indicator=indicator_label,
                    filters=filters,
                    data_rows=normalized,
                    source_hint=f"{dataset} (MoSPI)",
                )

                return {
                    "selector_a": selector_a,
                    "selector_b": selector_b,
                    "interpretation": interpretation,
                }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log_debug(f"Error: {exc}")
            _log_debug(traceback.format_exc())
            continue

    raise RuntimeError(f"All MCP URLs failed: {last_error}")


async def main():
    claim = "Energy consumption is rising faster than production"
    dataset = "ENERGY"
    result = await run_flow(claim, dataset)
    print(result)


asyncio.run(main())
