from fastapi import FastAPI
import logging

logger=logging.getLogger(__name__)

app = FastAPI(
    title="Infrastructure Monitor",
    description="Automated cloud infrastructure monitoring and remediation",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "service": "Infrastructure Monitor",
        "status": "running",
        "version": "1.0.0"
        }

@app.on_event("startup")
def event_startup():
    logger.info("Starting up Infra Monitor API")

@app.on_event("shutdown")
def event_shutdown():
    logger.info("Shutting down Infra Monitor API")

