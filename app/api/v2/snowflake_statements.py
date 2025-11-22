"""
Snowflake-compatible statement API endpoints.

This module implements functionless stubs for the Snowflake statement API.
These endpoints validate input/output using Pydantic models but return HTTP 501
(Not Implemented) to indicate that the functionality is not yet available.

To wire this router into the main application, add this to your app/main.py:

    from app.api.v2.snowflake_statements import router as snowflake_router
    app.include_router(snowflake_router)

Endpoints:
- POST /api/v2/statements - Create and execute a new SQL statement
- GET /api/v2/statements/{statementHandle} - Get the status of a statement
- POST /api/v2/statements/{statementHandle}/cancel - Cancel a running statement
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.v2.models import (
    StatementCancelResponse,
    StatementCreateRequest,
    StatementCreateResponse,
    StatementStatus,
    StatementStatusResponse,
)

router = APIRouter(prefix="/api/v2", tags=["Snowflake Statements"])


@router.post(
    "/statements",
    response_model=StatementCreateResponse,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Create and execute SQL statement",
    description="Submit a SQL statement for execution. This is a functionless stub that validates input but does not execute queries.",
)
async def create_statement(request: StatementCreateRequest) -> JSONResponse:
    """
    Create a new SQL statement execution.

    This is a functionless stub that:
    - Validates the request payload using Pydantic
    - Generates a sample response with proper structure
    - Returns HTTP 501 (Not Implemented)

    Args:
        request: Statement creation request containing SQL and parameters

    Returns:
        JSONResponse with StatementCreateResponse structure and 501 status
    """
    # Generate a sample response
    sample_response = StatementCreateResponse(
        statementHandle=str(uuid4()),
        status=StatementStatus(
            state="NOT_IMPLEMENTED",
            description="This endpoint is a stub and does not execute queries",
        ),
        created_at=datetime.now(timezone.utc),
    )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=sample_response.model_dump(mode="json"),
    )


@router.get(
    "/statements/{statementHandle}",
    response_model=StatementStatusResponse,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Get statement status",
    description="Retrieve the execution status of a previously submitted statement. This is a functionless stub.",
)
async def get_statement_status(statementHandle: str) -> JSONResponse:
    """
    Get the status of a SQL statement execution.

    This is a functionless stub that:
    - Validates the statement handle parameter
    - Generates a sample response with proper structure
    - Returns HTTP 501 (Not Implemented)

    Args:
        statementHandle: Unique identifier for the statement

    Returns:
        JSONResponse with StatementStatusResponse structure and 501 status
    """
    # Generate a sample response
    sample_response = StatementStatusResponse(
        statementHandle=statementHandle,
        status=StatementStatus(
            state="NOT_IMPLEMENTED",
            description="This endpoint is a stub and does not track statement execution",
        ),
        progress=None,
        started_at=None,
        finished_at=None,
    )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=sample_response.model_dump(mode="json"),
    )


@router.post(
    "/statements/{statementHandle}/cancel",
    response_model=StatementCancelResponse,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Cancel statement execution",
    description="Cancel a running SQL statement. This is a functionless stub.",
)
async def cancel_statement(statementHandle: str) -> JSONResponse:
    """
    Cancel a running SQL statement execution.

    This is a functionless stub that:
    - Validates the statement handle parameter
    - Generates a sample response with proper structure
    - Returns HTTP 501 (Not Implemented)

    Args:
        statementHandle: Unique identifier for the statement to cancel

    Returns:
        JSONResponse with StatementCancelResponse structure and 501 status
    """
    # Generate a sample response
    sample_response = StatementCancelResponse(
        statementHandle=statementHandle,
        cancelled=False,
        status=StatementStatus(
            state="NOT_IMPLEMENTED",
            description="This endpoint is a stub and does not perform cancellation",
        ),
    )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=sample_response.model_dump(mode="json"),
    )
