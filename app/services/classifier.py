import json
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings


class ClassificationError(RuntimeError):
    pass


_SYSTEM_PROMPT = """
You are a strict classifier for an app called "The Dinner Table Economist".
Your job: decide if a user claim can be answered using MoSPI economic datasets.
If answerable, map to the most relevant dataset(s) and suggest indicator + filters.
Never guess beyond the data. Do NOT answer the claim. Only classify.

Available datasets (use exact codes):
- PLFS: jobs, unemployment, wages, workforce participation
- CPI: retail inflation, cost of living, commodity prices
- WPI: wholesale inflation, producer prices
- IIP: industrial growth, manufacturing output
- ASI: factory performance, industrial employment
- NAS: GDP, economic growth, national income
- ENERGY: energy production, consumption, fuel mix

Rules:
- If no dataset directly addresses the claim, set is_answerable=false and return empty datasets.
- Some claims may need multiple datasets (e.g., wages vs prices -> PLFS + CPI). If so, return multiple datasets.
- Use only the dataset codes listed above.
- Provide indicator_hint and optional filter hints as strings (ALL filter values must be strings).
- If unsure, mark is_answerable=false.

Return ONLY valid JSON matching this schema:
{
  "is_answerable": true|false,
  "reasoning": "short rationale",
  "datasets": [
    {
      "dataset": "PLFS|CPI|WPI|IIP|ASI|NAS|ENERGY",
      "indicator_hint": "short hint",
      "metadata_params": {"key": "value"},
      "data_filters": {"key": "value"},
      "notes": "why this dataset"
    }
  ]
}
""".strip()


async def classify_claim(claim: str) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise ClassificationError("OPENAI_API_KEY is not set")

    if settings.openai_ssl_verify:
        http_client = None
    else:
        http_client = httpx.AsyncClient(verify=False)

    client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=http_client)

    step1_overview = None
    step1_path = Path("step1_overview.json")
    if step1_path.exists():
        try:
            step1_overview = json.loads(step1_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            step1_overview = None

    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"claim": claim, "step1_overview": step1_overview},
                    ensure_ascii=True,
                ),
            },
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content
    if not content:
        raise ClassificationError("Empty response from classifier")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ClassificationError("Classifier returned invalid JSON") from exc

    if http_client is not None:
        await http_client.aclose()

    return parsed
