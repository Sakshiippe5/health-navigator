# main.py — The entry point of your entire backend application
# This is equivalent to index.js in a Node/Express app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import health
from api.routes import documents 
from api.routes import chat    


# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
# FastAPI() creates your application instance — think of it like `express()`
app = FastAPI(
    title="AI Health Navigator",
    description="An AI-powered backend for health document analysis and symptom checking",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
# CORS = Cross-Origin Resource Sharing
# Your frontend (localhost:3000) and backend (localhost:8000) are on different
# "origins". Browsers BLOCK these requests by default for security.
# This middleware tells the browser: "Yes, I trust requests from these origins."
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],   # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Allow any headers
)

# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------
# Instead of putting all routes in one file (messy), we split them into
# separate files and "include" them here with a prefix.
# This is called a "router" pattern — standard in production APIs.
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"]) 
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"]) 

# ---------------------------------------------------------------------------
# Root endpoint — sanity check
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """The very base URL of your API."""
    return {"message": "AI Health Navigator API is running 🚀"}