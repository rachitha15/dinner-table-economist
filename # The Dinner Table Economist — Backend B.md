# The Dinner Table Economist — Backend Build Plan for Codex

## Project Context

I'm building "The Dinner Table Economist" — a web app that fact-checks common Indian economic claims using real government data via MCP (Model Context Protocol).

The user types a claim like "Nobody's hiring anymore" or "Inflation is out of control." The backend:
1. Classifies whether the claim can be answered using government data
2. Runs a 4-step MCP tool chain against MoSPI's (Ministry of Statistics, India) live MCP server to fetch real data
3. Sends the raw data to an LLM (Open AI - I have API key) for interpretation with strict guardrails
4. Returns a structured verdict (busted/confirmed/complicated) with the data, chart points, source attribution, and a full MCP trace for the frontend's "backstage" panel

The frontend is already built in React (attached). The backend needs to serve the API that the frontend consumes.

## Architecture

- **Backend:** Python FastAPI, I will be deploying on Railway by syncing Git repo
- **Frontend:** React/Vite on Vercel (the attached designs)
- **MCP Server:** MoSPI's hosted server at URL we tested https://mcp.mospi.gov.in (NOT self-hosted)
- **MCP Client:** FastMCP Python client
- **LLM:** OpenAI API (Choose the model that is best suited for this)

## MoSPI MCP — What I've Validated

The MoSPI MCP server exposes 4 sequential tools:

```
1_know_about_mospi_api()  →  2_get_indicators(dataset)  →  3_get_metadata(dataset, ...)  →  4_get_data(dataset, filters)
```

**Critical findings from validation:**
- Tools MUST be called in order. Skipping step 3 causes invalid filter codes in step 4.
- Each dataset has DIFFERENT required parameters:
  - CPI needs: base_year, series, state_code, year (all as strings)
  - PLFS needs: indicator_code, frequency_code, state_code, year (all as strings). Step 3 also requires indicator_code.
  - NAS needs: indicator_code, frequency_code, approach, year
- ALL filter values must be strings, even numeric codes (e.g., state_code: "1" not 1)
- Response times: ~0.5-1.5s per step, full chain ~3-5s
- Server URL: https://mcp.mospi.gov.in (connect with FastMCP Client at this URL or https://mcp.mospi.gov.in/mcp — test both)

**7 available datasets:**
- PLFS: jobs, unemployment, wages, workforce participation
- CPI: retail inflation, cost of living, commodity prices
- IIP: industrial growth, manufacturing output
- ASI: factory performance, industrial employment
- NAS: GDP, economic growth, national income
- WPI: wholesale inflation, producer prices
- ENERGY: energy production, consumption, fuel mix

## API Contract

The frontend expects this from the backend:

### POST /api/check-claim

**Request:**
```json
{
  "claim": "Nobody's hiring anymore"
}
```

**Success Response:**
```json
{
  "verdict": "busted",
  "headlineStat": "Unemployment dropped from 4.2% to 3.2% since 2021",
  "explanation": "According to the Periodic Labour Force Survey (PLFS) 2024...",
  "chartData": [
    {"year": "2021", "value": 4.2},
    {"year": "2022", "value": 3.6},
    {"year": "2023", "value": 3.4},
    {"year": "2024", "value": 3.2}
  ],
  "source": "Periodic Labour Force Survey 2024, Ministry of Statistics, Govt. of India",
  "mcpSteps": [
    {
      "id": 1,
      "name": "Discover",
      "description": "Asked MoSPI what datasets are available",
      "result": "7 datasets found → Selected PLFS (jobs & employment)",
      "time": "0.71s",
      "rawJson": "{...actual response...}"
    },
    {
      "id": 2,
      "name": "Explore",
      "description": "Found unemployment indicators in PLFS",
      "result": "8 indicators found. Selected: UR (Unemployment Rate)",
      "time": "0.58s",
      "rawJson": "{...actual response...}"
    },
    {
      "id": 3,
      "name": "Prepare",
      "description": "Retrieved available filters: years, states, gender, age",
      "result": "Filters: years 2017-2024, 36 states, gender, age groups",
      "time": "0.88s",
      "rawJson": "{...actual response...}"
    },
    {
      "id": 4,
      "name": "Fetch",
      "description": "Retrieved unemployment rate data for All India",
      "result": "Data retrieved successfully",
      "time": "1.90s",
      "rawJson": "{...actual response...}"
    }
  ],
  "outOfScope": false
}
```

**Out-of-scope Response:**
```json
{
  "verdict": "out_of_scope",
  "explanation": "This question can't be answered using government economic statistics.",
  "availableTopics": "Employment & wages (PLFS), retail inflation (CPI), wholesale prices (WPI), industrial output (IIP, ASI), GDP & national accounts (NAS), and energy statistics.",
  "mcpSteps": [],
  "outOfScope": true
}
```

**Error Response:**
```json
{
  "error": true,
  "message": "The government data server isn't responding right now"
}
```

## Curated Claims (12)

These should work reliably. Map each to its dataset and optimal MCP parameters:

1. "Inflation is out of control" → CPI
2. "Food prices have doubled" → CPI (food group)
3. "Rural India has it worse than cities" → CPI (rural vs urban sector)
4. "Nobody's hiring anymore" → PLFS (unemployment rate, indicator_code: 3)
5. "Youth unemployment is a crisis" → PLFS (age_code for 15-29)
6. "Women are leaving the workforce" → PLFS (gender_code, LFPR indicator_code: 1)
7. "Educated people are more unemployed than uneducated" → PLFS (education_code)
8. "Salaries haven't kept up with prices" → PLFS (earnings) + CPI
9. "Manufacturing is dead in India" → IIP or ASI
10. "Only services sector is growing" → NAS (sector breakdown)
11. "India's economy is slowing down" → NAS (GDP growth)
12. "India doesn't care about environment" → ENERGY

## LLM Prompt Guardrails (CRITICAL)

The LLM interpretation must follow three layers:

### Layer 1: Claim Classification
Before any MCP calls, classify whether the claim can be answered from the 7 MoSPI datasets. If not → return out_of_scope immediately. Do NOT attempt to answer claims about social trends, cultural topics, politics, or anything outside economic/statistical data.

### Layer 2: Indicator Matching
After getting indicators, evaluate if available indicators actually measure what the claim is about. If the match is weak, say so explicitly in the explanation. Do NOT silently stretch tangentially related data to fit the claim.

### Layer 3: Data Interpretation
When generating the verdict and explanation:
- Present the data and state what it shows
- Do NOT draw causal conclusions
- Do NOT extrapolate trends beyond the data
- Do NOT make policy recommendations
- If data is ambiguous or incomplete, use verdict "complicated" and say so
- Always attribute data to the specific MoSPI dataset and year
- Distinguish clearly between what the data says and what the LLM interprets

---

## TASK PLAN (Sequential — complete each before moving to next)

### Task 1: Project Setup

Create a FastAPI project with this structure:
```
dinner-table-economist/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, routes
│   ├── config.py             # Environment variables, settings
│   ├── routers/
│   │   └── claims.py         # POST /api/check-claim endpoint
│   ├── services/
│   │   ├── classifier.py     # Layer 1: Claim classification
│   │   ├── mcp_client.py     # MCP orchestration (4-step chain)
│   │   └── interpreter.py    # Layer 2+3: LLM data interpretation
│   └── models/
│       └── schemas.py        # Pydantic models matching API contract
├── requirements.txt
├── .env.example
├── Procfile                  # For Railway deployment
└── README.md
```

Dependencies: fastapi, uvicorn, fastmcp, httpx, anthropic, python-dotenv, pydantic

Environment variables needed: OPENAI_API_KEY

Include CORS middleware allowing requests from any origin (for Vercel frontend).

### Task 2: Pydantic Models (schemas.py)

Create request/response models matching the API contract above exactly. The response models must match the TypeScript interfaces in the frontend's mockData.ts:

```typescript
// Frontend expects this shape:
interface VerdictData {
  verdict: 'busted' | 'confirmed' | 'complicated';
  headlineStat: string;
  explanation: string;
  chartData: { year: string; value: number }[];
  source: string;
  mcpSteps: {
    id: number;
    name: string;
    description: string;
    result: string;
    time: string;
    rawJson: string;
  }[];
}
```

Also create: ClaimRequest, OutOfScopeResponse, ErrorResponse.

### Task 3: MCP Client Service (mcp_client.py)

Build the MCP orchestration service that:
1. Connects to https://mcp.mospi.gov.in using FastMCP Client
2. Runs the 4-step tool chain sequentially
3. Logs each step: input, output, time taken
4. Returns structured trace data for the backstage panel
5. Handles errors gracefully (timeout, connection failure, invalid data)

Important implementation details:
- ALL filter values must be strings
- PLFS requires indicator_code in Step 3 (unlike CPI)
- Each dataset has different valid parameters — the classifier must provide the right ones
- Step 1 result can be cached (it rarely changes)
- Truncate rawJson responses to max 500 chars for the frontend trace (full responses can be huge)

The service should accept: dataset name, indicator info, and filter parameters from the classifier. It should NOT decide which dataset to query — that's the classifier's job.

### Task 4: Claim Classifier (classifier.py)

Build the classification service using Claude API that:

1. Takes the user's free-text claim
2. Returns a structured classification:
   - is_answerable: boolean (can MoSPI data answer this?)
   - dataset: which dataset to query (PLFS, CPI, NAS, IIP, ASI, WPI, ENERGY)
   - indicator_hint: what to look for (e.g., "unemployment rate", "CPI general index")
   - filter_hints: suggested filters (e.g., {"frequency_code": "1", "state_code": "1"})
   - reasoning: brief explanation of classification

The system prompt should:
- List all 7 datasets and what they contain
- Be explicit that if no dataset matches with high confidence, return is_answerable: false
- Not try to be creative — only match claims to datasets where the data directly addresses the claim
- Return structured JSON (use Claude's JSON mode or structured output)

### Task 5: LLM Interpreter (interpreter.py)

Build the interpretation service using Claude API that:

1. Takes: original claim + raw data from MCP Step 4 + dataset metadata
2. Returns: verdict, headlineStat, explanation, chartData, source

The system prompt must enforce ALL Layer 3 guardrails listed above.

Output format must be structured JSON matching the VerdictData interface.

The prompt should receive:
- The original claim text
- The dataset name and indicator description
- The raw data rows from MCP
- Instructions to extract time-series data for the chart (year + value pairs)
- Instructions to determine verdict (busted/confirmed/complicated)
- Instructions to write a concise explanation citing specific numbers

### Task 6: Wire Everything Together (claims.py router)

The POST /api/check-claim endpoint should:

1. Receive claim text
2. Call classifier → if not answerable, return OutOfScopeResponse
3. Call MCP client with classifier's output → collect trace data
4. Call interpreter with raw MCP data → get verdict
5. Assemble full response matching the API contract
6. Return to frontend

Add error handling:
- MCP connection failure → return error response
- MCP timeout (>15s) → return error response  
- Classifier failure → return error response
- Rate limiting: max 20 requests per IP per hour (protect Claude API costs)

### Task 7: Test with Curated Claims

Test all 12 curated claims end-to-end. For each:
- Does the classifier pick the right dataset?
- Does the MCP chain complete without errors?
- Does the interpreter produce a reasonable verdict?
- Does the response match the frontend's expected schema?
- Is the MCP trace populated correctly?

Also test 5 out-of-scope claims:
- "How many people celebrate Valentine's Day?"
- "Is cricket more popular than football?"
- "Are Indians happy?"
- "Who will win the next election?"
- "Should I invest in gold?"

### Task 8: Railway Deployment

- Add Procfile: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Ensure all environment variables are documented
- Add health check endpoint: GET /health
- Test the deployed API with curl before connecting frontend

---

## Important Notes for you

- Do NOT self-host the MoSPI MCP server. Connect to their hosted server as a CLIENT.
- Do NOT over-engineer. No database needed. No user auth. No caching layer (yet). Keep it simple.
- The frontend code is attached for reference — match its data interfaces exactly.
- Test against the LIVE MoSPI MCP server, not mocks. I can help run the tests, let me know