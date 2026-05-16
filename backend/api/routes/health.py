# health.py — A dedicated router for health/status check endpoints
#
# WHY have a health check endpoint?
# In production, services like AWS, Kubernetes, and Docker constantly ping
# /health to know if your server is alive. If it returns 200 OK, the server
# is healthy. If not, it gets restarted automatically.
# This is called a "liveness probe" — a very common DevOps/backend interview topic.

from fastapi import APIRouter
from datetime import datetime, timezone

# APIRouter is like a mini-app — it holds a group of related routes
# We'll merge it into the main app via app.include_router() in main.py
router = APIRouter()


@router.get("/health", summary="Health Check", response_description="Server status")
def health_check():
    """
    Checks whether the API server is running and healthy.

    Returns:
        - status: 'ok' if running
        - timestamp: current UTC time (useful for debugging lag/timezone issues)
        - version: API version
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "service": "AI Health Navigator",
    }