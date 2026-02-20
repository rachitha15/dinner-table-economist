import json
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings


class SelectorBError(RuntimeError):
    pass


_SYSTEM_PROMPT = """
You are Selector-B for the “Dinner Table Economist” app.
Users make claims about the Indian economy. We use the MoSPI MCP server to verify them.

MCP steps (high level):
1) Discover: list datasets
2) Indicators: list indicator params for a dataset
3) Filters: list valid filter values (metadata) for Step-4
4) Fetch: get data using exact filters

Your job: choose the exact Step-4 filters from Step-3 metadata.

Input: claim + dataset + claim_type + Step-3 JSON + indicator_params.
Output: JSON only (no prose) with filters, benchmark_filters, optional_drop_filters.

Core rules:
- Use ONLY valid values from Step-3 (search nested structures).
- All filter values must be strings.
- Include all required api_params (e.g., Format).
- Keep indicator params fixed to Selector-A’s choices.
- Prefer the broadest valid defaults (All/Total/Combined, All-India) unless the claim specifies otherwise. Broadest means a SINGLE total/overall code, not a list of all codes.
- Time range: pick the latest 3 years when Step-3 provides multiple years, unless the claim specifies a single year. Never collapse to one year if multiple are available.
- If Step-3 exposes an aggregation/granularity field (e.g., level), you MUST include it and choose the highest aggregation that still matches the claim. Avoid lower-level filters unless explicitly mentioned.
- Avoid subcategory filters (group/item/nic/etc.) unless the claim explicitly names them.
- If Step-3 doesn’t mark required vs optional, choose the minimum set that still yields data.
- You may return comma-separated values ONLY for time fields (year, month_code) to reduce API calls.
- claim_type handling:
  - trend → no benchmark_filters
  - comparison / level → include benchmark_filters for a clear comparison group
  - intra_comparison → include benchmark_filters for the complementary series (within same dataset)
  - compound → no benchmark_filters (comparison happens across datasets)
- Provide optional_drop_filters (up to 3) that can be removed if Step-4 returns no data, without breaking claim relevance.

Return schema:
{
  "dataset": "CPI|PLFS|NAS|ASI|IIP|WPI|ENERGY",
  "filters": {"key": "value"},
  "benchmark_filters": {"key": "value"},
  "optional_drop_filters": ["key1","key2","key3"],
  "reasoning": "short reason"
}
""".strip()


async def select_filters(
    claim: str,
    dataset: str,
    claim_type: str,
    step3: dict[str, Any],
    indicator_params: dict[str, Any],
    pagination_hint: str | None = None,
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise SelectorBError("OPENAI_API_KEY is not set")

    if settings.openai_ssl_verify:
        http_client = None
    else:
        http_client = httpx.AsyncClient(verify=False)

    client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=http_client)

    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "claim": claim,
                        "dataset": dataset,
                        "claim_type": claim_type,
                        "step3": step3,
                        "indicator_params": indicator_params,
                        "pagination_hint": pagination_hint,
                    },
                    ensure_ascii=True,
                ),
            },
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content
    if not content:
        raise SelectorBError("Empty response from selector B")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SelectorBError("Selector B returned invalid JSON") from exc
    finally:
        if http_client is not None:
            await http_client.aclose()

    if "filters" in parsed and isinstance(parsed["filters"], dict):
        parsed["filters"] = {key: str(value) for key, value in parsed["filters"].items()}
    if "benchmark_filters" in parsed and isinstance(parsed["benchmark_filters"], dict):
        parsed["benchmark_filters"] = {
            key: str(value) for key, value in parsed["benchmark_filters"].items()
        }

    return parsed
