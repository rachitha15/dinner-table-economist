from typing import Literal

from pydantic import BaseModel, Field


class ClaimRequest(BaseModel):
    claim: str = Field(..., min_length=1)


class ChartDataPoint(BaseModel):
    year: str
    value: float
    label: str | None = None


class MCPStep(BaseModel):
    id: int
    name: str
    description: str
    result: str
    time: str
    rawJson: str


class VerdictData(BaseModel):
    verdict: Literal["busted", "confirmed", "complicated"]
    headlineStat: str
    explanation: str
    chartData: list[ChartDataPoint]
    source: str
    mcpSteps: list[MCPStep]


class OutOfScopeResponse(BaseModel):
    verdict: Literal["out_of_scope"]
    explanation: str
    availableTopics: str
    mcpSteps: list[MCPStep]
    outOfScope: bool = True


class ErrorResponse(BaseModel):
    error: bool = True
    message: str
