"""Application configuration, read from environment."""
import os

from dotenv import load_dotenv

load_dotenv()
# Storage: SQLite for the zero-dependency demo; swap to Postgres via DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digest.db")

# API auth — shared key required by the mobile app (empty = no auth, for local dev).
API_KEY = os.getenv("API_KEY", "")

# LLM config — any OpenAI-compatible /chat/completions endpoint (DeepSeek, OpenAI, Ollama, vLLM, Groq…).
# Leave LLM_API_KEY unset to use the deterministic fallback (no key needed).
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Pipeline limits.
DEFAULT_SOURCES = ["hackernews", "arxiv"]
MAX_ITEMS_PER_TOPIC = int(os.getenv("MAX_ITEMS_PER_TOPIC", "8"))
ITEMS_PER_SOURCE = int(os.getenv("ITEMS_PER_SOURCE", "10"))
RECENT_WINDOW_HOURS = int(os.getenv("RECENT_WINDOW_HOURS", "24"))
