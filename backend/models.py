from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class BusinessRole(str, Enum):
    CEO = "CEO"
    COO = "COO"
    CFO = "CFO"
    CRO = "CRO"
    CPO = "CPO"
    CMO = "CMO"
    CSO = "CSO"


class Action(BaseModel):
    roles_relevant: List[str] = Field(default_factory=list)


class TrendInfo(BaseModel):
    """Model for industry and sector trend information."""
    trend: str = Field(description="One-sentence description of the trend")
    evidence: str = Field(description="URL or source providing evidence for the trend")
    impact: str = Field(description="Why this trend matters for SaaS AI builders")
    date: str = Field(description="Date in YYYY-MM format")
    source_domain: str = Field(description="The domain of the source", default="")
    confidence_score: float = Field(description="Confidence score between 0-1", default=0.0) 