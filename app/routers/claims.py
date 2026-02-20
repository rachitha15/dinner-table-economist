import json
import asyncio
import logging
import os
import time
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastmcp import Client

from app.config import settings
from app.models.schemas import ClaimRequest, ErrorResponse, OutOfScopeResponse, VerdictData
from app.services.classifier import classify_claim
from app.services.interpreter import interpret_claim
from app.services.mcp_client import MCPClientError, _truncate_raw
from app.services.selector_a import select_indicator_params
from app.services.selector_b import select_filters

router = APIRouter()
logger = logging.getLogger("app.claims")
DEBUG_LOG = os.getenv("DEBUG_CLAIM_LOG", "false").lower() == "true"
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
REL_TIME_RE = re.compile(r"\b(years ago|decade|decades|since|in the \d{2}s)\b", re.IGNORECASE)
MCP_CALL_TIMEOUT = 30.0


def _write_debug(name: str, payload: Any) -> None:
    if not DEBUG_LOG:
        return
    try:
        with open(name, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to write debug file: %s", name)

_RATE_WINDOW = 3600
_RATE_LIMIT = 20
_RATE_STATE: dict[str, tuple[int, float]] = {}

_STEP1_CACHE: dict[str, Any] | None = None


def _rate_limit(ip: str) -> bool:
    now = time.time()
    count, start = _RATE_STATE.get(ip, (0, now))
    if now - start >= _RATE_WINDOW:
        _RATE_STATE[ip] = (1, now)
        return False
    if count >= _RATE_LIMIT:
        return True
    _RATE_STATE[ip] = (count + 1, start)
    return False


def _payload(result: Any) -> Any:
    return getattr(result, "structured_content", None) or getattr(result, "data", None) or result


async def _call_tool_with_timeout(client: Client, tool: str, payload: dict[str, Any]) -> Any:
    return await asyncio.wait_for(client.call_tool(tool, payload), timeout=MCP_CALL_TIMEOUT)


def _log_step_duration(step: str, duration: float) -> None:
    logger.info("MCP step=%s duration=%.2fs", step, duration)


def _valid_values(step3_payload: dict[str, Any]) -> dict[str, dict[str, str]]:
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
        if isinstance(value, str) and "," in value:
            key_lower = key.lower()
            if "year" not in key_lower and key_lower not in {"month_code", "month"}:
                value = value.split(",")[0].strip()
        if key in valid_map and isinstance(value, str):
            cleaned[key] = valid_map[key].get(value, value)
        else:
            cleaned[key] = value
    return cleaned


def _label_from_filters(primary: dict[str, Any], benchmark: dict[str, Any]) -> tuple[str, str]:
    diffs = []
    for key in set(primary.keys()) | set(benchmark.keys()):
        if primary.get(key) != benchmark.get(key):
            diffs.append((key, primary.get(key), benchmark.get(key)))
    if not diffs:
        return ("primary", "benchmark")
    key, pval, bval = diffs[0]
    return (f"{key}={pval}", f"{key}={bval}")


def _expand_filters(filters: dict[str, Any], max_years: int = 5) -> list[dict[str, Any]]:
    expanded = [filters]
    for key, value in list(filters.items()):
        if isinstance(value, str) and "," in value:
            key_lower = key.lower()
            if "year" in key_lower or key_lower in {"month_code", "month"}:
                # Allow comma-separated time fields to pass through in one call
                parts = [item.strip() for item in value.split(",") if item.strip()]
                if "year" in key_lower and len(parts) > max_years:
                    parts = parts[:max_years]
                    expanded = [{**item, key: ",".join(parts)} for item in expanded]
                continue
            parts = [item.strip() for item in value.split(",") if item.strip()]
            expanded = [{**item, key: part} for item in expanded for part in parts]
    return expanded


async def _run_step4(
    client: Client,
    dataset: str,
    filters: dict[str, Any],
    step4_steps: list[dict[str, Any]],
    label: str,
    optional_drop_filters: list[str],
    step3_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    api_params = step3_payload.get("api_params", []) if isinstance(step3_payload, dict) else []
    param_names = {p.get("name") for p in api_params if p.get("name")}

    async def _call(
        filters_to_use: dict[str, Any],
        attempt: str,
    ) -> tuple[list[dict[str, Any]], bool]:
        rows: list[dict[str, Any]] = []
        paginated = False
        base_filters = dict(filters_to_use)
        if "limit" in param_names and "limit" not in base_filters:
            base_filters["limit"] = "100"
        if "page" in param_names and "page" not in base_filters:
            base_filters["page"] = "1"

        for idx, one_filter in enumerate(_expand_filters(base_filters)):
            start = time.perf_counter()
            result = await _call_tool_with_timeout(
                client,
                "4_get_data",
                {"dataset": dataset, "filters": one_filter},
            )
            duration = time.perf_counter() - start
            _log_step_duration(f"step4_{label}_{attempt}", duration)
            payload = _payload(result)
            if isinstance(payload, dict):
                meta = payload.get("meta_data")
                if isinstance(meta, dict) and meta.get("totalPages", 1) > 1:
                    paginated = True
            _write_debug(f"debug_step4_{label}_{attempt}_{idx}.json", payload)
            _write_debug(f"debug_step4_{label}_{attempt}_{idx}_filters.json", one_filter)
            step4_steps.append(
                {
                    "id": 4,
                    "name": "Fetch",
                    "description": f"Fetched data for {dataset} ({label}, {attempt})",
                    "result": payload.get("msg", "Data retrieved") if isinstance(payload, dict) else "Data retrieved",
                    "time": f"{duration:.2f}s",
                    "rawJson": _truncate_raw(payload),
                }
            )
            if isinstance(payload, dict) and isinstance(payload.get("data"), list):
                rows.extend(payload.get("data", []))
        return rows, paginated

    rows, paginated = await _call(filters, "primary")
    if rows:
        return rows, paginated

    # One retry: drop optional filters (max 3), but never required
    api_params = step3_payload.get("api_params", []) if isinstance(step3_payload, dict) else []
    required = {p["name"] for p in api_params if p.get("required")}
    drops = [k for k in optional_drop_filters if k in filters and k not in required][:3]
    if drops:
        reduced = {k: v for k, v in filters.items() if k not in drops}
        rows, paginated = await _call(reduced, "retry")
        return rows, paginated

    return [], paginated


@router.post("/api/check-claim")
async def check_claim(request: Request, payload: ClaimRequest):
    ip = request.client.host if request.client else "unknown"
    if _rate_limit(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        classification = await classify_claim(payload.claim)
    except Exception:
        logger.exception("Classifier failed")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error=True, message="Classifier failed").model_dump(),
        )

    if not classification.get("is_answerable"):
        out = OutOfScopeResponse(
            verdict="out_of_scope",
            explanation="This question can't be answered using government economic statistics.",
            availableTopics=(
                "Employment & wages (PLFS), retail inflation (CPI), wholesale prices (WPI), "
                "industrial output (IIP, ASI), GDP & national accounts (NAS), and energy statistics."
            ),
            mcpSteps=[],
            outOfScope=True,
        )
        return JSONResponse(status_code=200, content=out.model_dump())

    datasets = classification.get("datasets", [])
    if not datasets:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error=True, message="No dataset selected").model_dump(),
        )

    dataset_info = datasets[0]
    dataset = dataset_info.get("dataset")
    indicator_hint = dataset_info.get("indicator_hint", payload.claim)

    steps: list[dict[str, Any]] = []
    try:
        for url in [settings.mospi_mcp_url, f"{settings.mospi_mcp_url}/mcp"]:
            for attempt, delay in enumerate((0.0, 0.5, 1.0), start=1):
                try:
                    current_step = "connect"
                    async with Client(url) as client:
                        global _STEP1_CACHE
                        if _STEP1_CACHE is None:
                            current_step = "step1"
                            start = time.perf_counter()
                            step1 = await _call_tool_with_timeout(client, "1_know_about_mospi_api", {})
                            duration = time.perf_counter() - start
                            _log_step_duration("step1", duration)
                            step1_payload = _payload(step1)
                            _STEP1_CACHE = step1_payload
                            steps.append(
                                {
                                    "id": 1,
                                    "name": "Discover",
                                    "description": "Asked MoSPI what datasets are available",
                                    "result": "Dataset overview retrieved",
                                    "time": f"{duration:.2f}s",
                                    "rawJson": _truncate_raw(step1_payload),
                                }
                            )
                        else:
                            steps.append(
                                {
                                    "id": 1,
                                    "name": "Discover",
                                    "description": "Used cached dataset overview",
                                    "result": "Dataset overview cached",
                                    "time": "0.00s",
                                    "rawJson": _truncate_raw(_STEP1_CACHE),
                                }
                            )

                        current_step = "step2"
                        start = time.perf_counter()
                        step2 = await _call_tool_with_timeout(
                            client,
                            "2_get_indicators",
                            {"dataset": dataset, "user_query": indicator_hint},
                        )
                        duration = time.perf_counter() - start
                        _log_step_duration("step2", duration)
                        step2_payload = _payload(step2)
                        steps.append(
                            {
                                "id": 2,
                                "name": "Indicators",
                                "description": f"Found indicators for {dataset}",
                                "result": "Indicator list retrieved",
                                "time": f"{duration:.2f}s",
                                "rawJson": _truncate_raw(step2_payload),
                            }
                        )

                        current_step = "selector_a"
                        selector_a = await select_indicator_params(payload.claim, dataset, step2_payload)
                        _write_debug("debug_selector_a_api.json", selector_a)
                        indicator_params = selector_a.get("params", {})
                        claim_type = selector_a.get("claim_type", "trend")

                        current_step = "step3"
                        start = time.perf_counter()
                        step3 = await _call_tool_with_timeout(
                            client,
                            "3_get_metadata",
                            {"dataset": dataset, **indicator_params},
                        )
                        duration = time.perf_counter() - start
                        _log_step_duration("step3", duration)
                        step3_payload = _payload(step3)
                        steps.append(
                            {
                                "id": 3,
                                "name": "Filters",
                                "description": f"Retrieved valid filters for {dataset}",
                                "result": "Filter metadata retrieved",
                                "time": f"{duration:.2f}s",
                                "rawJson": _truncate_raw(step3_payload),
                            }
                        )

                        current_step = "selector_b"
                        selector_b = await select_filters(
                            payload.claim,
                            dataset,
                            claim_type,
                            step3_payload,
                            indicator_params,
                        )
                        _write_debug("debug_selector_b_api.json", selector_b)

                        filters = _clean_filters(selector_b.get("filters", {}), step3_payload)
                        benchmark_filters = selector_b.get("benchmark_filters")
                        if claim_type not in ("level", "comparison", "intra_comparison"):
                            benchmark_filters = None
                        if isinstance(benchmark_filters, dict):
                            benchmark_filters = _clean_filters(benchmark_filters, step3_payload)

                        optional_drop_filters = selector_b.get("optional_drop_filters", [])

                        step4_steps: list[dict[str, Any]] = []
                        current_step = "step4_primary"
                        primary_series, primary_paginated = await _run_step4(
                            client,
                            dataset,
                            filters,
                            step4_steps,
                            "primary",
                            optional_drop_filters,
                            step3_payload,
                        )

                        benchmark_series = None
                        benchmark_paginated = False
                        if isinstance(benchmark_filters, dict) and benchmark_filters:
                            current_step = "step4_benchmark"
                            benchmark_series, benchmark_paginated = await _run_step4(
                                client,
                                dataset,
                                benchmark_filters,
                                step4_steps,
                                "benchmark",
                                optional_drop_filters,
                                step3_payload,
                            )

                        if primary_paginated or benchmark_paginated:
                            current_step = "selector_b_retry"
                            selector_b = await select_filters(
                                payload.claim,
                                dataset,
                                claim_type,
                                step3_payload,
                                indicator_params,
                                pagination_hint=(
                                    "Previous Step-4 results were paginated (totalPages>1). "
                                    "Include any aggregation/granularity field (e.g., level) and choose the highest "
                                    "aggregation that still matches the claim. Avoid extra subcategory filters."
                                ),
                            )
                            _write_debug("debug_selector_b_api_retry.json", selector_b)
                            filters = _clean_filters(selector_b.get("filters", {}), step3_payload)
                            benchmark_filters = selector_b.get("benchmark_filters")
                            if claim_type not in ("level", "comparison", "intra_comparison"):
                                benchmark_filters = None
                            if isinstance(benchmark_filters, dict):
                                benchmark_filters = _clean_filters(benchmark_filters, step3_payload)
                            optional_drop_filters = selector_b.get("optional_drop_filters", [])

                            current_step = "step4_primary_retry"
                            primary_series, _ = await _run_step4(
                                client,
                                dataset,
                                filters,
                                step4_steps,
                                "primary_retry",
                                optional_drop_filters,
                                step3_payload,
                            )
                            if isinstance(benchmark_filters, dict) and benchmark_filters:
                                current_step = "step4_benchmark_retry"
                                benchmark_series, _ = await _run_step4(
                                    client,
                                    dataset,
                                    benchmark_filters,
                                    step4_steps,
                                    "benchmark_retry",
                                    optional_drop_filters,
                                    step3_payload,
                                )
                            else:
                                benchmark_series = None

                        if isinstance(benchmark_series, dict) or isinstance(benchmark_series, list):
                            primary_label, benchmark_label = _label_from_filters(filters, benchmark_filters or {})
                            normalized = {
                                "primary_label": primary_label,
                                "benchmark_label": benchmark_label,
                                "primary": primary_series,
                                "benchmark": benchmark_series,
                            }
                        else:
                            normalized = primary_series

                        steps.extend(step4_steps)

                        current_step = "interpreter"
                        interpretation = await interpret_claim(
                            claim=payload.claim,
                            dataset=dataset,
                            indicator=indicator_hint,
                            filters=filters,
                            data_rows=normalized,
                            source_hint=f"{dataset} (MoSPI)",
                        )

                        response = VerdictData(
                            verdict=interpretation["verdict"],
                            headlineStat=interpretation["headlineStat"],
                            explanation=interpretation["explanation"],
                            chartData=interpretation["chartData"],
                            source=interpretation["source"],
                            mcpSteps=steps,
                        )
                        return JSONResponse(status_code=200, content=response.model_dump())
                except MCPClientError:
                    if delay:
                        await asyncio.sleep(delay)
                    continue
                except Exception:
                    logger.exception("MCP pipeline failed for url=%s at step=%s", url, current_step)
                    if delay:
                        await asyncio.sleep(delay)
                    continue
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error=True, message="MCP server not responding").model_dump(),
        )
    except Exception:
        logger.exception("Unexpected error in check-claim")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error=True, message="Unexpected error").model_dump(),
        )
