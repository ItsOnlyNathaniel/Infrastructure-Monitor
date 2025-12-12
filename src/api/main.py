#Imports
from fastapi import FastAPI
from database.models import init_db
import asyncio
import logging

# Logger and app initialisation
logger=logging.getLogger(__name__)
app = FastAPI(
    title="Infrastructure Monitor",
    description="Automated cloud infrastructure monitoring and remediation",
    version="1.0.0"
)
# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Infrastructure Monitor",
        "status": "running",
        "version": "1.0.0"
        }

#Startup and shutdown events
@app.on_event("startup")
async def event_startup():
    await redis_client.conncect()
    logger.info("Starting up Infra Monitor API")
    await init_db()
    logger.info("Database initialized")

@app.on_event("shutdown")
async def event_shutdown():
    logger.info("Shutting down Infra Monitor API")

