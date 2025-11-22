from fastapi import FastAPI, Response
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="opteryx.app - minimal example")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting opteryx.app FastAPI application")

@app.get("/")
async def read_root():
    return {"message": "Hello from opteryx.app!"}

@app.get("/health")
async def health_check():
    return Response(content="ok", media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, log_level="info")
