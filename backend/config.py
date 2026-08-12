"""Application configuration, read from environment."""
import os

# Storage: SQLite for the zero-dependency demo; swap to Postgres via DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digest.db")

# LLM config — leave unset to use the deterministic fallback (no API key needed).
# Set LLM_PROVIDER/LLM_MODEL/LLM_API_KEY to enable a real model (LiteLLM hook).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Pipeline limits.
DEFAULT_SOURCES = ["hackernews", "arxiv"]
MAX_ITEMS_PER_TOPIC = int(os.getenv("MAX_ITEMS_PER_TOPIC", "8"))
ITEMS_PER_SOURCE = int(os.getenv("ITEMS_PER_SOURCE", "10"))
