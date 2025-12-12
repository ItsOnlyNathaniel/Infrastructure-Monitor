from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/health/{service_id}", status_code=200)
async def health_check(service_id: str):
    return {"status": "healthy", "service_id": service_id}