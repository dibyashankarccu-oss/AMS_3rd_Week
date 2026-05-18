# repositories/ticket_repository.py

from supabase import create_client
from core.config import Config
from services.embedding_service import get_embedding

supabase = create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_KEY
)

ALLOWED_FIELDS = {

    # ── identifiers ──
    "issue_key", "child_key", "parent_ticket_key",

    # ── user ──
    "name", "email",

    # ── ticket content ──
    "summary", "description",

    # ── app details ──
    "app_name", "component_name",

    # ── priority ──
    "urgency", "impact",

    # ── status ──
    "status", "is_duplicate",

    # ── escalation ──
    "escalated_to",
    "escalation_channel",
    "escalated_at",

    # ── AI vector ──
    "embedding",

    # ── runbook ──
    "paired_steps",
    "runbook_title",
    "runbook_category",
    "match_type",

    # ── RCA ──
    "rca_root_cause", "rca_affected",
    "rca_steps",
    "rca_confidence",
    "rca_source",
    "rca_matched_from",
    "rca_matched_summary",
}


async def insert_ticket(data):
    print("🔥 FINAL RAW PAYLOAD:", data)

    try:
        data = dict(data)

        # filter only valid DB columns
        data = {
            k: v
            for k, v in data.items()
            if k in ALLOWED_FIELDS
        }

        if data.get("embedding") is not None:
            data["embedding"] = [
                float(x)
                for x in data["embedding"]
            ]

        # defaults
        data.setdefault("child_key", None)
        data.setdefault("parent_ticket_key", None)
        data.setdefault("paired_steps", [])
        data.setdefault("rca_steps", [])

        # optional fallback values
        data.setdefault("app_name", "General")
        data.setdefault("component_name", "General")

        res = (
            supabase
            .table("tickets")
            .insert(data)
            .execute()
        )

        return res.data[0] if res.data else None

    except Exception as e:
        print("❌ insert_ticket error:", str(e))
        return None

# ─────────────────────────────────────────────
# GET ALL TICKETS
# ─────────────────────────────────────────────
async def get_all_tickets():
    try:
        res = supabase.table("tickets").select("*").execute()
        return res.data or []
    except Exception as e:
        print("❌ get_all_tickets error:", str(e))
        return []


# ─────────────────────────────────────────────
# GET SINGLE TICKET
# ─────────────────────────────────────────────
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

        query_embedding = [
            float(x)
            for x in query_embedding
        ]

        res = supabase.rpc(
            "match_tickets",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "app_filter": app_name,
                "component_filter": component_name
            }
        ).execute()

        return res.data or []

    except Exception as e:

        print(
            "❌ vector search error:",
            str(e)
        )

        return []

        
# ─────────────────────────────────────────────
# SEARCH COMPLETED TICKETS WITH RCA
# Used by rca_routes.py Layer B to find past
# resolved tickets that already have an RCA,
# so the result can be copied to the new ticket.
# ─────────────────────────────────────────────
async def search_completed_tickets_with_rca(query_embedding: list, top_k: int = 5) -> list:
    """
    Vector-similarity search over completed parent tickets that already
    have an rca_root_cause stored.  Returns the top_k closest matches
    sorted by cosine similarity descending, each row including all RCA
    fields so rca_routes.py can copy them directly.
    """
    try:
        if not query_embedding:
            return []

        query_embedding = [float(x) for x in query_embedding]

        res = supabase.rpc(
            "match_completed_tickets_with_rca",
            {
                "query_embedding": query_embedding,
                "match_count":     top_k,
            }
        ).execute()

        return res.data or []

    except Exception as e:
        print("❌ search_completed_tickets_with_rca error:", str(e))
        return []


# ─────────────────────────────────────────────
# UPDATE TICKET RCA
# Persists the generated / matched / human RCA
# back into the tickets row in Supabase.
# ─────────────────────────────────────────────
async def update_ticket_rca(
    issue_key:          str,
    root_cause:         str,
    affected_component: str,
    resolution_steps:   list,
    confidence:         str,
    source:             str,
    matched_from:       str | None = None,
    matched_summary:    str | None = None,
) -> bool:
    """
    Writes all RCA fields to the tickets table row identified by issue_key.
    """
    try:
        res = (
            supabase.table("tickets")
            .update({
                "rca_root_cause":    root_cause,
                "rca_affected":      affected_component,
                "rca_steps":         resolution_steps,
                "rca_confidence":    confidence,
                "rca_source":        source,
                "rca_matched_from":  matched_from,
                "rca_matched_summary": matched_summary,
            })
            .eq("issue_key", issue_key)
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print(f"❌ update_ticket_rca error: {e}")
        return False


# ─────────────────────────────────────────────
# DELETE SINGLE
# ─────────────────────────────────────────────
async def delete_ticket(issue_key: str):
    try:
        res = (
            supabase.table("tickets")
            .delete()
            .eq("issue_key", issue_key)
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print("❌ delete_ticket error:", str(e))
        return False


# ─────────────────────────────────────────────
# DELETE CASCADE
# ─────────────────────────────────────────────
async def delete_ticket_cascade(parent_key: str):
    try:
        res = (
            supabase.table("tickets")
            .delete()
            .or_(
                f"issue_key.eq.{parent_key},"
                f"parent_ticket_key.eq.{parent_key}"
            )
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print("❌ delete_ticket_cascade error:", str(e))
        return False


# ─────────────────────────────────────────────
# UPDATE STATUS CASCADE
# ─────────────────────────────────────────────
async def update_status_cascade(parent_key: str, status: str):
    try:
        res = (
            supabase.table("tickets")
            .update({"status": status})
            .or_(
                f"issue_key.eq.{parent_key.strip()},"
                f"parent_ticket_key.eq.{parent_key.strip()}"
            )
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print("❌ update_status_cascade error:", str(e))
        return False


# ─────────────────────────────────────────────
# RUNBOOK UPDATE
# paired_steps stores checklist + commands together
# ─────────────────────────────────────────────
async def update_ticket_runbook(
    issue_key:               str,
    paired_steps:            list,
    runbook_title:           str = None,
    runbook_category:        str = None,
    match_type:              str = None,
) -> bool:
    try:
        res = (
            supabase.table("tickets")
            .update({
                "paired_steps":            paired_steps,
                "runbook_title":           runbook_title,
                "runbook_category":        runbook_category,
                "match_type":              match_type,
            })
            .eq("issue_key", issue_key)
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print("❌ update_ticket_runbook error:", str(e))
        return False


# ─────────────────────────────────────────────
# GET ONLY PARENT TICKETS
# ─────────────────────────────────────────────
async def get_parent_tickets():
    try:
        res = (
            supabase.table("tickets")
            .select("*")
            .is_("parent_ticket_key", None)
            .execute()
        )
        return res.data or []

    except Exception as e:
        print("❌ get_parent_tickets error:", str(e))
        return []


# ─────────────────────────────────────────────
# GET CHILDREN
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# UPDATE PARENT LINK
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# BULK CHILD KEY UPDATE
# ─────────────────────────────────────────────
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


async def detach_child_ticket(issue_key: str):
    try:
        # 1. fetch ticket first
        res = (
            supabase.table("tickets")
            .select("*")
            .eq("issue_key", issue_key)
            .single()
            .execute()
        )

        ticket = res.data

        if not ticket:
            return False

        description = ticket.get("description", "")
        summary = ticket.get("summary", "")

        # 2. check embedding
        embedding = ticket.get("embedding")

        if not embedding:
            print("⚡ embedding missing → generating now")

            text = f"{summary} {description}".strip()

            new_embedding = await get_embedding(text)

            if new_embedding:
                supabase.table("tickets").update({
                    "embedding": new_embedding
                }).eq("issue_key", issue_key).execute()

                print("✅ embedding stored for detached ticket")

        # 3. now detach ticket
        res = (
            supabase.table("tickets")
            .update({
                "child_key": None,
                "parent_ticket_key": None,
                "is_duplicate": False
            })
            .eq("issue_key", issue_key)
            .execute()
        )

        return bool(res.data)

    except Exception as e:
        print("❌ detach_child_ticket error:", str(e))
        return False
        

# ─────────────────────────────────────────────
# DELETE ONLY SINGLE TICKET
# ─────────────────────────────────────────────
async def delete_single_ticket(issue_key: str):
    try:
        res = (
            supabase.table("tickets")
            .delete()
            .eq("issue_key", issue_key)
            .execute()
        )
        return bool(res.data)

    except Exception as e:
        print("❌ delete_single_ticket error:", str(e))
        return False


# ─────────────────────────────────────────────
# PROMOTE FIRST CHILD AS NEW PARENT
# ─────────────────────────────────────────────
async def promote_first_child_as_parent(old_parent_key: str):
    try:
        children = (
            supabase.table("tickets")
            .select("*")
            .eq("parent_ticket_key", old_parent_key)
            .order("issue_key", desc=False)
            .execute()
        )
        children = children.data or []

        if not children:
            return None

        new_parent     = children[0]
        new_parent_key = new_parent["issue_key"]

        supabase.table("tickets") \
            .update({
                "parent_ticket_key": None,
                "child_key":         None,
                "is_duplicate":      False
            }) \
            .eq("issue_key", new_parent_key) \
            .execute()

        remaining = sorted(children[1:], key=lambda x: x["issue_key"])
        counter   = 1

        for child in remaining:
            supabase.table("tickets") \
                .update({
                    "parent_ticket_key": new_parent_key,
                    "child_key":         f"{new_parent_key}.{counter}"
                }) \
                .eq("issue_key", child["issue_key"]) \
                .execute()
            counter += 1

        return new_parent_key

    except Exception as e:
        print("❌ promote_first_child_as_parent error:", str(e))
        return None




async def search_completed_tickets(
    query_embedding,
    top_k=5,
    app_name="",
    component_name=""
):
    try:
        if not query_embedding:
            print("❌ Empty embedding received")
            return []

        query_embedding = [float(x) for x in query_embedding]

        # -----------------------------
        # 🔥 CLEAN INPUT FILTERS
        # -----------------------------
        def clean(value):
            if not value:
                return None
            value = value.strip()
            return value or None

        app_name = clean(app_name)
        component_name = clean(component_name)

        # -----------------------------
        # 📤 DEBUG: INPUT TO RPC
        # -----------------------------
        print("\n📤 RPC INPUT DEBUG")
        print("app_name:", repr(app_name))
        print("component_name:", repr(component_name))
        print("embedding_size:", len(query_embedding))

        # safety check
        if len(query_embedding) != 384:
            print("❌ Invalid embedding size:", len(query_embedding))
            return []

        # -----------------------------
        # 🚀 SUPABASE CALL
        # -----------------------------
        res = supabase.rpc(
            "search_completed_tickets",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "app_filter": app_name,
                "component_filter": component_name
            }
        ).execute()

        data = res.data or []

        # -----------------------------
        # 🧠 DEBUG: RAW DB OUTPUT
        # -----------------------------
        print("\n========= COMPLETED SEARCH (RAW DB OUTPUT) =========")
        for d in data:
            print({
                "issue_key": d.get("issue_key"),
                "app_name": d.get("app_name"),
                "component_name": d.get("component_name"),
                "similarity": d.get("similarity")
            })
        print("====================================================\n")

        return data

    except Exception as e:
        print("❌ completed ticket search error:", str(e))
        return []



# ─────────────────────────────────────────────
# UPDATE TICKET ESCALATION
# ─────────────────────────────────────────────
async def update_ticket_escalation(
    issue_key: str,
    escalated_to: str,
    escalation_channel: str,
    escalated_at: str,
) -> bool:
    try:
        res = (
            supabase.table("tickets")
            .update({
                "escalated_to":       escalated_to,
                "escalation_channel": escalation_channel,
                "escalated_at":       escalated_at,
            })
            .eq("issue_key", issue_key)
            .execute()
        )
        print("🔥 SUPABASE RESPONSE:", res.data)
        return bool(res.data)
    except Exception as e:
        print("❌ update_ticket_escalation error:", str(e))
        return False




# ─────────────────────────────────────────────
# UPDATE ONLY CHILDREN STATUS
# Parent remains unchanged
# ─────────────────────────────────────────────
async def update_children_status(
    parent_key: str,
    status: str
):
    try:

        res = (
            supabase.table("tickets")
            .update({
                "status": status
            })
            .eq(
                "parent_ticket_key",
                parent_key.strip()
            )
            .execute()
        )

        return bool(res.data)

    except Exception as e:

        print(
            "❌ update_children_status error:",
            str(e)
        )

        return False