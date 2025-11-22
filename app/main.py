from typing import Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.api.v2.snowflake_statements import router as snowflake_router

app = FastAPI(title="Opteryx App - Basic API")

# Include Snowflake-compatible statement API router
app.include_router(snowflake_router)


class QueryRequest(BaseModel):
    row_count: Literal[100, 1000, 10000] = 100
    text: str


@app.get("/", summary="Health / root")
def root():
    return {"status": "ok"}


@app.get(
    "/query",
    summary="Submit SQL statement via query parameters",
    description="Accepts `row_count` (one of 100, 1000, 10000; default 100) and `text` (SQL statement) as query parameters.",
)
def get_query(
    row_count: Literal[100, 1000, 10000] = Query(
        100, description="Row count (one of 100, 1000, 10000)"
    ),
    text: str = Query(..., description="SQL statement text"),
):
    """
    Returns a simple JSON thanking the user for the input.
    This endpoint is accessible via the Swagger UI at /docs.
    """
    return {"message": "Thank you for your input."}


@app.post(
    "/query",
    summary="Submit SQL statement via JSON body",
    description="Accepts a JSON body with `row_count` and `text`. `row_count` must be one of 100, 1000 or 10000.",
)
def post_query(payload: QueryRequest):
    """
    An alternative POST endpoint (useful if the SQL is large or you prefer a JSON body).
    Also returns a simple JSON thanking the user for the input.
    """
    return {"message": "Thank you for your input."}
