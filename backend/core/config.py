# core/config.py
#
# RESPONSIBILITY: Load and validate all environment variables.
# Every secret and config value lives here — one place.
#
# WHY a config file?
# If you hardcode your API key in 5 different files, changing it
# means editing 5 files. With a config file, you change it once.
# Also centralizes validation — if a key is missing, you get a
# clear error at startup, not a cryptic crash later.

import os
from dotenv import load_dotenv

# load_dotenv() reads your .env file and loads each line
# as an environment variable — accessible via os.getenv()
load_dotenv()

# ── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Validation ────────────────────────────────────────────────────────────────
# Fail loudly at startup if critical config is missing.
# Better to crash immediately with a clear message than
# to crash mysteriously when the first request comes in.
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Add it to your .env file: GEMINI_API_KEY=your_key_here"
    )