#Imports
from fastapi import FastAPI
import asyncio
import logging
from database.models import init_db
from src.api.routes import services, remediations

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

# Include routers
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(remediations.router, prefix="/api/remediations", tags=["remediations"])

#Startup and shutdown events
@app.on_event("startup")
async def event_startup():
    await redis_client.connect()
    logger.info("Starting up Infra Monitor API")
    await init_db()
    logger.info("Database initialized")

@app.on_event("shutdown")
async def event_shutdown():
    logger.info("Shutting down Infra Monitor API")

