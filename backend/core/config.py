# core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

# ── Auth ──────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# ── Validation ────────────────────────────────────────────────────────────────
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in .env")