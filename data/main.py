from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from data.api.v1.interface import router as data_router

app = FastAPI(title="Opteryx Data API", default_response_class=ORJSONResponse)

# Snowflake-compatible statement API router
app.include_router(data_router)
