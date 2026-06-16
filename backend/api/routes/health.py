# api/routes/health.py
from fastapi import APIRouter
from datetime import datetime, timezone
from api.schemas import HealthResponse

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,    # ← ADD THIS
    summary="Health Check"
)
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "service": "AI Health Navigator",
    }