# repositories/rca_kb_repository.py

from supabase import create_client
from core.config import Config

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


async def search_rca_knowledge_base(
    query_embedding: list,
    top_k:           int  = 3,
    app_code:        str  = None,
    component_code:  str  = None,
) -> list:
    """
    Vector search the RCA KB filtered by app/component when provided.
    Falls back to unfiltered search when no app/component given.
    """
    try:
        if not query_embedding:
            return []

        res = supabase.rpc(
            "match_rca_knowledge_base",
            {
                "query_embedding":  [float(x) for x in query_embedding],
                "match_count":      top_k,
                "app_filter":       app_code,
                "component_filter": component_code,
            }
        ).execute()

        return res.data or []

    except Exception as e:
        print(f"❌ search_rca_knowledge_base error: {e}")
        return []


async def insert_rca_knowledge(data: dict) -> dict | None:
    try:
        if data.get("embedding"):
            data["embedding"] = [float(x) for x in data["embedding"]]
        res = supabase.table("rca_knowledge_base").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"❌ insert_rca_knowledge error: {e}")
        return None