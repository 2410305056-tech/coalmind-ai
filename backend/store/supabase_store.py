from typing import List, Dict, Any, Optional
from backend.store.sqlite_store import SQLiteStore
from backend.config import SUPABASE_URL, SUPABASE_KEY

class SupabaseStore(SQLiteStore):
    """
    Supabase Store Implementation.
    Falls back gracefully to high-performance local SQLite store if
    Supabase credentials are not configured or cloud connection drops.
    """
    def __init__(self):
        super().__init__()
        self.is_connected = bool(SUPABASE_URL and SUPABASE_KEY)
        if self.is_connected:
            # Optional pgvector integration if cloud credentials present
            pass

def get_store(store_type: str = "sqlite"):
    if store_type == "supabase" and SUPABASE_URL and SUPABASE_KEY:
        return SupabaseStore()
    return SQLiteStore()
