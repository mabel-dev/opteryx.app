"""
Pydantic models for Snowflake-compatible statement API.

These models define the request and response structures for the Snowflake
statement endpoints. They are used for input validation and response serialization.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class StatementStatus(BaseModel):
    """Status information for a statement execution."""

    state: str = Field(
        ...,
        description="Current state of the statement (e.g., QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED)",
    )
    description: Optional[str] = Field(
        None, description="Human-readable description of the current state"
    )


class StatementCreateRequest(BaseModel):
    """Request model for creating a new statement execution."""

    sqlText: str = Field(..., description="SQL statement to execute")
    describeOnly: Optional[bool] = Field(
        None, description="If true, only describe the result schema without executing"
    )
    bindValues: Optional[dict[str, Any]] = Field(
        None, description="Values to bind to SQL parameters"
    )
    parameters: Optional[dict[str, Any]] = Field(
        None, description="Additional execution parameters"
    )


class StatementCreateResponse(BaseModel):
    """Response model for statement creation."""

    statementHandle: str = Field(..., description="Unique handle for the statement")
    status: StatementStatus = Field(..., description="Current status of the statement")
    created_at: datetime = Field(..., description="Timestamp when the statement was created")


class StatementStatusResponse(BaseModel):
    """Response model for statement status queries."""

    statementHandle: str = Field(..., description="Unique handle for the statement")
    status: StatementStatus = Field(..., description="Current status of the statement")
    progress: Optional[float] = Field(
        None, description="Execution progress as a percentage (0.0 to 100.0)"
    )
    started_at: Optional[datetime] = Field(
        None, description="Timestamp when execution started"
    )
    finished_at: Optional[datetime] = Field(
        None, description="Timestamp when execution finished"
    )


class StatementCancelResponse(BaseModel):
    """Response model for statement cancellation."""

    statementHandle: str = Field(..., description="Unique handle for the statement")
    cancelled: bool = Field(..., description="Whether the cancellation was successful")
    status: StatementStatus = Field(..., description="Current status after cancellation")
