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