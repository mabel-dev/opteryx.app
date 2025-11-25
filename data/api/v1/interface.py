"""
Snowflake-compatible statement API endpoints for the `data` service.

This is a copy of the existing `app.api.v1.interface` module but rewritten
to live under the `data` package so the service is exposed as
`data.opteryx.app` in your monorepo layout.
"""

import os
from datetime import datetime
from datetime import timezone
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import ORJSONResponse
from google.cloud import firestore  # directly import firestore; dependency declared in pyproject

from data.api.v1.models import JobDocument
from data.api.v1.models import StatementCancelResponse
from data.api.v1.models import StatementCreateRequest
from data.api.v1.models import StatementCreateResponse
from data.api.v1.models import StatementStatus
from data.api.v1.models import StatementStatusResponse
from data.auth.deps import require_bearer_token

router = APIRouter(
    prefix="/api/v1", tags=["Statements"], dependencies=[Depends(require_bearer_token)]
)


# Firestore-backed jobs collection; we explicitly require Firestore to be
# available and will return 504 (gateway timeout) if it is not.

 
def _get_firestore_client():
    try:
        proj = (
            os.environ.get("GCP_PROJECT")
            or os.environ.get("GCP_PROJECT_ID")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        return firestore.Client(project=proj) if proj else firestore.Client()
    except Exception:
        # Return None on error; callers treat this as a dependent service
        # failure and return 504.
        return None


@router.post(
    "/statements",
    response_model=StatementCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute SQL statement",
    description="Submit a SQL statement for execution. This is a functionless stub that validates input but does not execute queries.",
)
async def create_statement(request: StatementCreateRequest) -> ORJSONResponse:
    # Create a job in Firestore to represent the queued statement. Return the
    # created record to the client.
    handle = str(uuid4())
    now = datetime.now(timezone.utc)
    db = _get_firestore_client()
    if db is None:
        raise HTTPException(status_code=504, detail="dependent service unavailable: firestore")
    # Build a validated job document and serialize it for Firestore write.
    job = JobDocument(
        statementHandle=handle,
        sqlText=request.sqlText,
        status="SUBMITTED",
        description="Queued for execution",
        progress=0.0,
        created_at=now,
    )
    job_doc = job.model_dump(mode="json", exclude_none=True)
    # Use Firestore server timestamp for created_at in the persisted document
    job_doc["created_at"] = firestore.SERVER_TIMESTAMP
    try:
        db.collection("jobs").document(handle).set(job_doc)
    except Exception as exc:
        # Treat write failures as dependent service failure
        raise HTTPException(status_code=504, detail="failed to write to firestore") from exc

    response = StatementCreateResponse(
        statementHandle=handle,
        status=StatementStatus(state="SUBMITTED", description="Queued for execution"),
        created_at=now,
    )

    return ORJSONResponse(
        status_code=status.HTTP_201_CREATED, content=response.model_dump(mode="json")
    )


@router.get(
    "/statements/{statementHandle}",
    response_model=StatementStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get statement status",
    description="Retrieve the execution status of a previously submitted statement. This is a functionless stub.",
)
async def get_statement_status(statementHandle: str) -> ORJSONResponse:
    # Fetch the job record from Firestore. If Firestore is unavailable, return 504.
    db = _get_firestore_client()
    if db is None:
        raise HTTPException(status_code=504, detail="dependent service unavailable: firestore")
    rec = None
    if db is not None:
        try:
            doc = db.collection("jobs").document(statementHandle).get()
            if doc.exists:
                rec = doc.to_dict()
                # Convert Firestore timestamps to datetime if needed
                for key in ("created_at", "started_at", "finished_at", "updated_at"):
                    if key in rec and hasattr(rec[key], "to_datetime"):
                        try:
                            rec[key] = rec[key].to_datetime()
                        except Exception:
                            pass
                # Convert to typed model instance for validation
                job_record = JobDocument.model_validate(rec)
                rec = job_record.model_dump(mode="json")
        except Exception as exc:
            # Consider fetch failures as a dependent service failure
            raise HTTPException(status_code=504, detail="failed to read from firestore") from exc

    if not rec:
        raise HTTPException(status_code=404, detail="statement not found")

    response = StatementStatusResponse(
        statementHandle=statementHandle,
        status=StatementStatus(
            state=rec.get("status", "UNKNOWN"), description=rec.get("description")
        ),
        progress=rec.get("progress"),
        started_at=rec.get("started_at"),
        finished_at=rec.get("finished_at"),
    )
    return ORJSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump(mode="json"))


@router.post(
    "/statements/{statementHandle}/cancel",
    response_model=StatementCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel statement execution",
    description="Cancel a running SQL statement. This is a functionless stub.",
)
async def cancel_statement(statementHandle: str) -> ORJSONResponse:
    # Attempt to update the job status to 'user-cancelled' in Firestore and
    # return the current status.
    db = _get_firestore_client()
    if db is None:
        raise HTTPException(status_code=504, detail="dependent service unavailable: firestore")
    cancelled = False
    rec = None
    if db is not None:
        try:
            doc_ref = db.collection("jobs").document(statementHandle)
            doc = doc_ref.get()
            if not doc.exists:
                raise HTTPException(status_code=404, detail="statement not found")
            rec = doc.to_dict()
            # Update status if it's not already in a terminal state
            doc_ref.update({"status": "user-cancelled", "updated_at": firestore.SERVER_TIMESTAMP})
            # Re-fetch the doc so we return the same data Firestore stores
            doc = doc_ref.get()
            rec = doc.to_dict()
            for key in ("created_at", "started_at", "finished_at", "updated_at"):
                if key in rec and hasattr(rec[key], "to_datetime"):
                    try:
                        rec[key] = rec[key].to_datetime()
                    except Exception:
                        pass
            job_record = JobDocument.model_validate(rec)
            rec = job_record.model_dump(mode="json")
            cancelled = True
        except HTTPException:
            # re-raise 4xx exceptions (like Not Found)
            raise
        except Exception as exc:
            # Consider update failures as a dependent service failure
            raise HTTPException(status_code=504, detail="failed to update firestore") from exc
    # If we reached here and rec is still None something's wrong
    if not rec:
        raise HTTPException(status_code=500, detail="failed to cancel statement")

    response = StatementCancelResponse(
        statementHandle=statementHandle,
        cancelled=cancelled,
        status=StatementStatus(
            state=rec.get("status", "UNKNOWN"), description=rec.get("description")
        ),
    )
    return ORJSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump(mode="json"))
