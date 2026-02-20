import json
import time
from typing import Any

from fastmcp import Client

from app.config import settings


class MCPClientError(RuntimeError):
    pass


_STEP1_CACHE: dict[str, Any] | None = None


def _truncate_raw(value: Any, limit: int = 500) -> str:
    if isinstance(value, str):
        raw = value
    else:
        raw = json.dumps(value, ensure_ascii=True, default=str)
    if len(raw) <= limit:
        return raw
    return raw[: limit - 3] + "..."


def _stringify_filters(filters: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in filters.items()}


def _format_step(step_id: int, name: str, description: str, result: str, duration: float, raw: Any) -> dict[str, Any]:
    return {
        "id": step_id,
        "name": name,
        "description": description,
        "result": result,
        "time": f"{duration:.2f}s",
        "rawJson": _truncate_raw(raw),
    }


def _candidate_urls() -> list[str]:
    base = settings.mospi_mcp_url.rstrip("/")
    if base.endswith("/mcp"):
        return [base]
    return [base, f"{base}/mcp"]


async def run_mcp_chain(
    dataset: str,
    indicator_hint: str,
    metadata_params: dict[str, Any],
    data_filters: dict[str, Any],
) -> dict[str, Any]:
    global _STEP1_CACHE

    trace: list[dict[str, Any]] = []
    last_error: Exception | None = None

    for url in _candidate_urls():
        try:
            async with Client(url) as client:
                if _STEP1_CACHE is None:
                    start = time.perf_counter()
                    step1 = await client.call_tool("1_know_about_mospi_api", {})
                    duration = time.perf_counter() - start
                    trace.append(
                        _format_step(
                            1,
                            "Discover",
                            "Asked MoSPI what datasets are available",
                            "Dataset overview retrieved",
                            duration,
                            step1,
                        )
                    )
                    _STEP1_CACHE = step1
                else:
                    trace.append(
                        _format_step(
                            1,
                            "Discover",
                            "Used cached dataset overview",
                            "Dataset overview cached",
                            0.0,
                            _STEP1_CACHE,
                        )
                    )

                start = time.perf_counter()
                step2 = await client.call_tool(
                    "2_get_indicators",
                    {"dataset": dataset, "user_query": indicator_hint},
                )
                duration = time.perf_counter() - start
                trace.append(
                    _format_step(
                        2,
                        "Indicators",
                        f"Found indicators for {dataset}",
                        "Indicator list retrieved",
                        duration,
                        step2,
                    )
                )

                start = time.perf_counter()
                step3 = await client.call_tool(
                    "3_get_metadata",
                    {"dataset": dataset, **_stringify_filters(metadata_params)},
                )
                duration = time.perf_counter() - start
                trace.append(
                    _format_step(
                        3,
                        "Filters",
                        f"Retrieved valid filters for {dataset}",
                        "Filter metadata retrieved",
                        duration,
                        step3,
                    )
                )

                start = time.perf_counter()
                step4 = await client.call_tool(
                    "4_get_data",
                    {"dataset": dataset, "filters": _stringify_filters(data_filters)},
                )
                duration = time.perf_counter() - start
                trace.append(
                    _format_step(
                        4,
                        "Fetch",
                        f"Fetched data for {dataset}",
                        "Data retrieved",
                        duration,
                        step4,
                    )
                )

                return {
                    "overview": _STEP1_CACHE,
                    "indicators": step2,
                    "metadata": step3,
                    "data": step4,
                    "trace": trace,
                }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            trace.append(
                _format_step(
                    0,
                    "Connection",
                    f"Failed connecting to {url}",
                    str(exc),
                    0.0,
                    {"error": str(exc)},
                )
            )
            continue

    raise MCPClientError("MCP server connection failed") from last_error
