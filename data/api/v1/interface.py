"""
Snowflake-compatible statement API endpoints for the `data` service.

This is a copy of the existing `app.api.v1.interface` module but rewritten
to live under the `data` package so the service is exposed as
`data.opteryx.app` in your monorepo layout.
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse

from data.auth.deps import require_bearer_token

from data.api.v1.models import (
    StatementCancelResponse,
    StatementCreateRequest,
    StatementCreateResponse,
    StatementStatus,
    StatementStatusResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Statements"], dependencies=[Depends(require_bearer_token)])


@router.post(
    "/statements",
    response_model=StatementCreateResponse,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Create and execute SQL statement",
    description="Submit a SQL statement for execution. This is a functionless stub that validates input but does not execute queries.",
)
async def create_statement(request: StatementCreateRequest) -> JSONResponse:
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
