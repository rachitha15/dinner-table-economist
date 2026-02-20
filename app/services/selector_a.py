import json
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings


class SelectorAError(RuntimeError):
    pass


_SYSTEM_PROMPT = """
You are Selector-A for the “Dinner Table Economist” app.
Users make claims about the Indian economy. We use the MoSPI MCP server to verify them.

MCP steps (high level):
1) Discover: list datasets
2) Indicators: list indicator params for a dataset
3) Filters: list valid filter values (metadata) for Step-4
4) Fetch: get data using exact filters

Your job: choose the exact Step-2 indicator parameters needed for Step-3 so the app can fetch real data.

Dataset cheat-sheet (high level):
- PLFS: jobs, unemployment, wages, workforce participation
- CPI: retail inflation, cost of living, commodity prices
- WPI: wholesale inflation, producer prices
- IIP: industrial growth, manufacturing output
- ASI: factory performance, industrial employment
- NAS: GDP, GVA, and sectoral output (agriculture/industry/services)
- ENERGY: energy production/consumption/fuel mix

Input: claim text + dataset + Step-2 JSON (already fetched).
Output: strict JSON ONLY (no prose) with the exact parameters required for Step-3 and a claim_type.

Rules:
- Use only values that exist in Step-2.
- Return all required params for Step-3 for the dataset.
- If multiple values could fit, pick the most general / default option unless the claim specifies otherwise.
- Return ONLY raw codes/values, not labels (e.g., use "1" not "frequency_code_1_Annual").
- If Step-2 exposes an aggregation/granularity dimension (e.g., level/granularity/category_level), you MUST include it and choose the highest aggregation that still matches the claim.
- Classify the claim into one of: trend, level, comparison, distribution, compound, intra_comparison, other.
- If the claim does not clearly fit a category, set claim_type="trend" to prefer multi-year series.
- Use "compound" when the claim explicitly compares two different quantities (e.g., wages vs prices, salaries vs inflation).
- Use "intra_comparison" when the claim compares two series that are available within the same dataset (e.g., two options within Step-2), so you can use benchmark_filters in Selector-B.
- If Step-2 presents a single dimension with exactly two options and the claim compares those two, set claim_type="intra_comparison".
- If the claim uses exclusivity language (e.g., "only", "just", "compared to other sectors") or compares sectors/groups within the same dataset, set claim_type="comparison" or "intra_comparison" accordingly.
- Example: if Step-2 shows use_of_energy_balance with Supply vs Consumption and the claim compares consumption vs production/supply, set claim_type="intra_comparison".
- For CPI, choose base_year + series + level.
- For PLFS, choose frequency_code + indicator_code.
- For NAS, choose series + frequency_code + indicator_code.
- For ASI, choose classification_year + indicator_code.
- For ENERGY, choose indicator_code + use_of_energy_balance_code.
- For IIP/WPI, Step-2 has no indicators; return an empty params object and note that Step-3 needs base params.

Return JSON schema:
{
  "dataset": "CPI|PLFS|NAS|ASI|IIP|WPI|ENERGY",
  "params": {"key": "value"},
  "claim_type": "trend|level|comparison|distribution|compound|intra_comparison|other",
  "reasoning": "short reason"
}
""".strip()


def _normalize_params(dataset: str, params: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in params.items():
        if isinstance(value, str):
            raw = value
        else:
            raw = str(value)
        if dataset == "PLFS" and key == "frequency_code":
            # Allow values like "frequency_code_1_Annual" -> "1"
            if raw.startswith("frequency_code_") and "_" in raw:
                raw = raw.split("_")[2]
        normalized[key] = raw
    return normalized


async def select_indicator_params(claim: str, dataset: str, step2: dict[str, Any]) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise SelectorAError("OPENAI_API_KEY is not set")

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
                        "step2": step2,
                    },
                    ensure_ascii=True,
                ),
            },
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content
    if not content:
        raise SelectorAError("Empty response from selector A")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SelectorAError("Selector A returned invalid JSON") from exc
    finally:
        if http_client is not None:
            await http_client.aclose()

    if "params" in parsed and isinstance(parsed["params"], dict):
        parsed["params"] = _normalize_params(dataset, parsed["params"])

    if "claim_type" not in parsed:
        parsed["claim_type"] = "other"

    return parsed
