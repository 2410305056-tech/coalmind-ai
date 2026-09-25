import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
REPORTS_DIR = STORAGE_DIR / "reports"
DB_PATH = STORAGE_DIR / "coalmind.db"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

# Create required directories
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Hardware & LLM Configuration
# STRICT NO-HEAVY-ML POLICY: Intel i5 8GB RAM profile
EMBEDDING_DIM = 384
MAX_UPLOAD_SIZE_MB = 25

# API Keys from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Dual Store Configuration
STORE_TYPE = os.getenv("STORE_TYPE", "sqlite") # "sqlite" or "supabase"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
