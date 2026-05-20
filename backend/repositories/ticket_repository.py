# repositories/ticket_repository.py

from supabase import create_client
from core.config import Config
from services.embedding_service import get_embedding

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

ALLOWED_FIELDS = {
    "issue_key", "child_key", "parent_ticket_key",
    "name", "email",
    "summary", "description",
    "app_name", "component_name", "app_code", "component_code",
    "urgency", "impact",
    "status", "is_duplicate", "duplicate_of",
    "escalated_to", "escalation_channel", "escalated_at",
    "embedding",
    "sop_title", "sop_confluence_id", "sop_url", "sop_category",
    "match_type", "paired_steps",
    # RCA — rca_steps / rca_matched_from / rca_matched_summary removed
    "rca_root_cause", "rca_affected", "rca_confidence", "rca_source",
}


async def insert_ticket(data):
    print("🔥 FINAL RAW PAYLOAD:", data)
    try:
        data = dict(data)
        data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        if data.get("embedding") is not None:
            data["embedding"] = [float(x) for x in data["embedding"]]
        data.setdefault("child_key",         None)
        data.setdefault("parent_ticket_key", None)
        data.setdefault("paired_steps",      [])
        data.setdefault("app_name",          "General")
        data.setdefault("component_name",    "General")
        res = supabase.table("tickets").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print("❌ insert_ticket error:", str(e))
        return None


async def get_all_tickets():
    try:
        res = supabase.table("tickets").select("*").execute()
        return res.data or []
    except Exception as e:
        print("❌ get_all_tickets error:", str(e))
        return []


async def get_ticket(issue_key: str):
    try:
        res = (
            supabase.table("tickets")
            .select("*")
            .eq("issue_key", issue_key)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        print("❌ get_ticket error:", str(e))
        return None


async def search_similar_tickets(
    query_embedding,
    top_k=5,
    app_name="",
    component_name=""
):
    try:
        if not query_embedding:
            return []
        res = supabase.rpc(
            "match_tickets",
            {
                "query_embedding":  [float(x) for x in query_embedding],
                "match_count":      top_k,
                "app_filter":       app_name or None,
                "component_filter": component_name or None,
            }
        ).execute()
        return res.data or []
    except Exception as e:
        print("❌ search_similar_tickets error:", str(e))
        return []


async def search_completed_tickets_with_rca(
    query_embedding: list,
    top_k: int = 5
) -> list:
    try:
        if not query_embedding:
            return []
        res = supabase.rpc(
            "match_completed_tickets_with_rca",
            {
                "query_embedding": [float(x) for x in query_embedding],
                "match_count":     top_k,
            }
        ).execute()
        return res.data or []
    except Exception as e:
        print("❌ search_completed_tickets_with_rca error:", str(e))
        return []


async def update_ticket_rca(
    issue_key:          str,
    root_cause:         str,
    affected_component: str,
    confidence:         str,
    source:             str,
) -> bool:
    try:
        res = (
            supabase.table("tickets")
            .update({
                "rca_root_cause": root_cause,
                "rca_affected":   affected_component,
                "rca_confidence": confidence,
                "rca_source":     source,
            })
            .eq("issue_key", issue_key)
            .execute()
        )
        if res.data:
            return True
        print(f"⚠️  update_ticket_rca: no rows updated for {issue_key}")
        return False
    except Exception as e:
        print(f"❌ update_ticket_rca error: {e}")
        return False


async def delete_ticket(issue_key: str):
    try:
        res = supabase.table("tickets").delete().eq("issue_key", issue_key).execute()
        return bool(res.data)
    except Exception as e:
        print("❌ delete_ticket error:", str(e))
        return False


async def delete_ticket_cascade(parent_key: str):
    try:
        res = (
            supabase.table("tickets")
            .delete()
            .or_(f"issue_key.eq.{parent_key},parent_ticket_key.eq.{parent_key}")
            .execute()
        )
        return bool(res.data)
    except Exception as e:
        print("❌ delete_ticket_cascade error:", str(e))
        return False


async def update_status_cascade(parent_key: str, status: str):
    try:
        res = (
            supabase.table("tickets")
            .update({"status": status})
            .or_(f"issue_key.eq.{parent_key.strip()},parent_ticket_key.eq.{parent_key.strip()}")
            .execute()
        )
        return bool(res.data)
    except Exception as e:
        print("❌ update_status_cascade error:", str(e))
        return False


async def update_ticket_runbook(
    issue_key: str, paired_steps: list,
    sop_title: str = None, sop_confluence_id: str = None,
    sop_url: str = None, sop_category: str = None,
    match_type: str = None,
) -> bool:
    try:
        res = (
            supabase.table("tickets")
            .update({
                "paired_steps":     paired_steps,
                "sop_title":        sop_title,
                "sop_confluence_id": sop_confluence_id,
                "sop_url":          sop_url,
                "sop_category":     sop_category,
                "match_type":       match_type,
            })
            .eq("issue_key", issue_key)
            .execute()
        )
        return bool(res.data)
    except Exception as e:
        print("❌ update_ticket_runbook error:", str(e))
        return False


async def get_children(parent_key: str):
    try:
        res = (
            supabase.table("tickets")
            .select("*")
            .eq("parent_ticket_key", parent_key)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print("❌ get_children error:", str(e))
        return []


async def update_parent(issue_key: str, new_parent: str):
    try:
        res = (
            supabase.table("tickets")
            .update({"parent_ticket_key": new_parent})
            .eq("issue_key", issue_key)
            .execute()
        )
        return bool(res.data)
    except Exception as e:
        print("❌ update_parent error:", str(e))
        return False


async def update_child_keys(updates: list):
    try:
        for item in updates:
            supabase.table("tickets") \
                .update({"child_key": item["child_key"]}) \
                .eq("issue_key", item["issue_key"]) \
                .execute()
        return True
    except Exception as e:
        print("❌ update_child_keys error:", str(e))
        return False


async def promote_first_child_as_parent(old_parent_key: str):
    try:
        children = (
            supabase.table("tickets")
            .select("*")
            .eq("parent_ticket_key", old_parent_key)
            .order("issue_key", desc=False)
            .execute()
        ).data or []
        if not children:
            return None
        new_parent_key = children[0]["issue_key"]
        supabase.table("tickets") \
            .update({"parent_ticket_key": None, "child_key": None, "is_duplicate": False}) \
            .eq("issue_key", new_parent_key).execute()
        for i, child in enumerate(sorted(children[1:], key=lambda x: x["issue_key"]), start=1):
            supabase.table("tickets") \
                .update({"parent_ticket_key": new_parent_key,
                         "child_key": f"{new_parent_key}.{i}"}) \
                .eq("issue_key", child["issue_key"]).execute()
        return new_parent_key
    except Exception as e:
        print("❌ promote_first_child_as_parent error:", str(e))
        return None