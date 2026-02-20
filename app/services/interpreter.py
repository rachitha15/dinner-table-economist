import json
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings


class InterpretationError(RuntimeError):
    pass


_SYSTEM_PROMPT = """
You are the interpreter for the “Dinner Table Economist” app.
Users make claims about the Indian economy. We use the MoSPI MCP server to verify them.

MCP steps (high level):
1) Discover: list datasets
2) Indicators: list indicator params for a dataset
3) Filters: list valid filter values (metadata) for Step-4
4) Fetch: get data using exact filters

You are given a claim and MoSPI dataset results. You must produce a verdict and explanation.

Guardrails (MUST FOLLOW):
- Do NOT make causal claims.
- Do NOT extrapolate beyond the data.
- Do NOT make policy recommendations.
- Do NOT compare to any benchmark (e.g., national average) unless it appears in the provided data_rows.
- If data is ambiguous or incomplete, use verdict "complicated".
- Always cite the dataset and year(s) used.
- Distinguish clearly between what the data shows and your interpretation.
- Use ONLY the provided data_rows. Do not invent values.
- If multiple years are present in data_rows, include all of them in chartData.
- If data_rows includes a benchmark series, you may compare primary vs benchmark explicitly using the provided labels, but chartData MUST include ONLY the primary series.
- If data_rows contains a monthly series (YYYY-MM), you may infer short-term trend within that year, but do not generalize beyond it.
- In chartData, each value must be a numeric metric matching the claim (e.g., unemployment rate %, CPI index). Do NOT output placeholders; every point must include a numeric value.
- In chartData, include a "label" for what the value represents (e.g., "unemployment rate (%)", "CPI index"). Use the same label for all points.

Output JSON ONLY in this schema:
{
  "verdict": "busted|confirmed|complicated",
  "headlineStat": "short numeric summary",
  "explanation": "2-4 sentences",
  "chartData": [{"year": "YYYY", "value": number, "label": "metric name"}],
  "source": "dataset + year attribution"
}
""".strip()


async def interpret_claim(
    claim: str,
    dataset: str,
    indicator: str,
    filters: dict[str, Any],
    data_rows: Any,
    source_hint: str,
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise InterpretationError("OPENAI_API_KEY is not set")

    if settings.openai_ssl_verify:
        http_client = None
    else:
        http_client = httpx.AsyncClient(verify=False)

    client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=http_client)

    payload = {
        "claim": claim,
        "dataset": dataset,
        "indicator": indicator,
        "filters": filters,
        "data_rows": data_rows,
        "source_hint": source_hint,
    }

    response = await client.chat.completions.create(
        model="gpt-4.1",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise InterpretationError("Empty response from interpreter")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise InterpretationError("Interpreter returned invalid JSON") from exc
    finally:
        if http_client is not None:
            await http_client.aclose()

    return parsed
