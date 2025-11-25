"""
Pydantic models for Snowflake-compatible statement API (data service).
"""

from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class JobDocument(BaseModel):
    statementHandle: str
    sqlText: str
    status: str = Field(..., description="Status of the job")
    description: Optional[str] = Field(None)
    progress: Optional[float] = Field(0.0)
    created_at: Optional[datetime] = Field(None)
    started_at: Optional[datetime] = Field(None)
    finished_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)


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
