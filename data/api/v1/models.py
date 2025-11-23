"""
Pydantic models for Snowflake-compatible statement API (data service).
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class StatementStatus(BaseModel):
    state: str = Field(..., description="Current state of the statement")
    description: Optional[str] = Field(None, description="Human-readable description")


class StatementCreateRequest(BaseModel):
    sqlText: str = Field(..., description="SQL statement to execute")
    describeOnly: Optional[bool] = Field(None)
    bindValues: Optional[dict[str, Any]] = Field(None)
    parameters: Optional[dict[str, Any]] = Field(None)


class StatementCreateResponse(BaseModel):
    statementHandle: str
    status: StatementStatus
    created_at: datetime


class StatementStatusResponse(BaseModel):
    statementHandle: str
    status: StatementStatus
    progress: Optional[float] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class StatementCancelResponse(BaseModel):
    statementHandle: str
    cancelled: bool
    status: StatementStatus
