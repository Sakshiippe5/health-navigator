# main.py — The entry point of your entire backend application

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import engine
from database import models
from api.routes import health
from api.routes import documents
from api.routes import chat
from api.routes import agents
from api.routes import auth
# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Health Navigator",
    description="An AI-powered backend for health document analysis and symptom checking",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Create Database Tables
# ---------------------------------------------------------------------------
# This runs on startup — creates all tables if they don't exist yet
# Safe to run multiple times — won't drop existing tables
models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])

# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI Health Navigator API is running 🚀"}