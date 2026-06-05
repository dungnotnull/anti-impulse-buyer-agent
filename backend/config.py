"""Configuration for anti-impulse-buyer backend."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv(
    "AIB_DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'anti_impulse_buyer.db'}",
)
DATABASE_ENCRYPT_KEY = os.getenv("AIB_DB_KEY", "")

# Server
HOST = os.getenv("AIB_HOST", "127.0.0.1")
PORT = int(os.getenv("AIB_PORT", "7432"))

# CORS — only allow the extension origin
ALLOWED_ORIGINS = os.getenv(
    "AIB_ALLOWED_ORIGINS",
    "chrome-extension://*,moz-extension://*,http://localhost:5173",
).split(",")

# Impulsivity score defaults
IMPULSE_DEFAULTS = {
    "midnight_weight": 1.0,
    "afternoon_weight": 0.0,
    "recent_purchase_hours": 48,
    "similar_items_threshold_days": 90,
}

# LLM Router
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_BACKEND_ORDER = os.getenv(
    "AIB_LLM_ORDER", "ollama,claude,openai"
).split(",")
