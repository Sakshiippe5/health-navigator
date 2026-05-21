import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Only validate Groq now since we're using it
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. "
        "Add it to your .env file: GROQ_API_KEY=your_key_here"
    )