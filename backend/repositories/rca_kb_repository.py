# repositories/rca_kb_repository.py

from supabase import create_client
from core.config import Config

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


# ─────────────────────────────────────────────
# VECTOR SEARCH — RCA KNOWLEDGE BASE
# ─────────────────────────────────────────────
async def search_rca_knowledge_base(query_embedding: list, top_k: int = 3) -> list:
    """
    Vector search against the RCA knowledge base.
    Returns top-k matches sorted by cosine similarity descending.
    """
    try:
        if not query_embedding:
            return []

        query_embedding = [float(x) for x in query_embedding]

        res = supabase.rpc(
            "match_rca_knowledge_base",
            {
                "query_embedding": query_embedding,
                "match_count":     top_k,
            }
        ).execute()

        return res.data or []

    except Exception as e:
        print(f"❌ search_rca_knowledge_base error: {e}")
        return []


# ─────────────────────────────────────────────
# INSERT — RCA KNOWLEDGE BASE
# Called when a generated RCA is confirmed useful
# ─────────────────────────────────────────────
async def insert_rca_knowledge(data: dict) -> dict | None:
    try:
        if data.get("embedding"):
            data["embedding"] = [float(x) for x in data["embedding"]]

        res = supabase.table("rca_knowledge_base").insert(data).execute()
        return res.data[0] if res.data else None

    except Exception as e:
        print(f"❌ insert_rca_knowledge error: {e}")
        return None


# ─────────────────────────────────────────────
# INCREMENT RECURRENCE COUNT
# Called when a KB entry is matched and reused
# ─────────────────────────────────────────────
async def increment_rca_recurrence(kb_id: int) -> bool:
    try:
        res = (
            supabase.table("rca_knowledge_base")
            .update({"recurrence_count": supabase.raw("recurrence_count + 1")})
            .eq("id", kb_id)
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print(f"❌ increment_rca_recurrence error: {e}")
        return False