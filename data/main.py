from fastapi import FastAPI

from data.api.v1.interface import router as data_router

app = FastAPI(title="Opteryx Data API")

# Snowflake-compatible statement API router
app.include_router(data_router)
