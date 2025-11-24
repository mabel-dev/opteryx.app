from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="Opteryx Worker")


class JobSubmit(BaseModel):
    job_ref: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/submit")
def submit(job: JobSubmit):
    # Minimal stub: accept and echo job reference.
    if not job.job_ref:
        raise HTTPException(status_code=400, detail="missing job_ref")
    # In real system we'd enqueue to a queue; here we just return accepted.
    return {"accepted": True, "job_ref": job.job_ref}
