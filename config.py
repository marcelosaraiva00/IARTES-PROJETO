import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "45"))
GEMINI_BATCH_SIZE = int(os.getenv("GEMINI_BATCH_SIZE", "10"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "1"))
GEMINI_RETRY_BASE_DELAY_S = float(os.getenv("GEMINI_RETRY_BASE_DELAY_S", "1.5"))
GEMINI_FALLBACK_MODELS = [
    m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash").split(",") if m.strip()
]

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
