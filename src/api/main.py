#Imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Cross-Origin Resource Sharing
import asyncio
import logging
from src.database.models import init_db
from src.api.routes import services, remediations
from src.core.redis_client import redis_client

# Logger and app initialisation
logger=logging.getLogger(__name__)
app = FastAPI(
    title="Infrastructure Monitor",
    description="Automated cloud infrastructure monitoring and remediation",
    version="1.0.0"
)

# Allows requests from browsers running on different domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[""],
)

# Include routers
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(remediations.router, prefix="/api/remediations", tags=["remediations"])

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
    await redis_client.connect()
    logger.info("Starting up Infra Monitor API")
    await init_db()
    logger.info("Database initialized")

@app.on_event("shutdown")
async def event_shutdown():
    logger.info("Shutting down Infra Monitor API")