from fastapi import APIRouter, HTTPException

from repositories.ticket_repository import (
    get_all_tickets,
    update_ticket_runbook,
)
from repositories.runbook_repository import insert_runbook
from modules.runbook_execution.handler import handle_runbook_flow
from services.embedding_service import get_embedding
from repositories.ticket_event_repository import log_event

router = APIRouter()


# ───────────── GET RUNBOOK FOR TICKET ─────────────
@router.get("/tickets/{issueKey}/runbook")
async def get_runbook(issueKey: str):
    try:
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")

        # ── child ticket → redirect to parent ──
        if ticket.get("is_duplicate") and ticket.get("parent_ticket_key"):
            parent_key = ticket["parent_ticket_key"]
            print(f"↩️  [{issueKey}] Duplicate — redirecting to parent {parent_key}")
            return {
                "type":              "duplicate",
                "message":           f"This is a duplicate ticket. See runbook for parent: {parent_key}",
                "parent_ticket_key": parent_key,
            }

        # ─────────────────────────────
        # CACHE HIT
        # ─────────────────────────────
        if ticket.get("paired_steps"):
            print(f"📦 [{issueKey}] CACHE HIT")
            return {
                "paired_steps":     ticket["paired_steps"],
                "runbook_title":    ticket.get("runbook_title"),
                "runbook_category": ticket.get("runbook_category"),
                "match_type":       ticket.get("match_type"),
                "ticket_status":    ticket.get("status"),
                "message":          "Loaded from cache",
            }

        # ─────────────────────────────
        # CACHE MISS → RUN AGENT
        # ─────────────────────────────
        print(f"🤖 [{issueKey}] CACHE MISS — calling LLM...")

        state = {
            "id":          issueKey,
            "summary":     ticket.get("summary", ""),
            "description": ticket.get("description", ""),
            "data":        ticket,
            "type":        None,
            "message":     "",
        }

        result = await handle_runbook_flow(state)

        if result.get("type") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        paired_steps   = result.get("paired_steps", [])
        final_category = result.get("runbook_category")

        # ── Cache in DB ──
        await update_ticket_runbook(
            issueKey,
            paired_steps     = paired_steps,
            runbook_title    = result.get("runbook_title"),
            runbook_category = final_category,
            match_type       = result.get("match_type"),
        )
        await log_event(
            ticket_id=issueKey,
            event="RUNBOOK_GENERATED",
            actor="system",
            details="Runbook generated and cached",
            metadata={
                "runbook_title": result.get("runbook_title"),
                "category": final_category,
                "match_type": result.get("match_type")
            }
        )
        print(f"💾 [{issueKey}] Runbook cached in Supabase")

        return {
            "paired_steps":     paired_steps,
            "runbook_title":    result.get("runbook_title"),
            "runbook_category": final_category,
            "match_type":       result.get("match_type"),
            "ticket_status":    ticket.get("status"),
            "message":          result.get("message"),
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"❌ get_runbook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ───────────── CREATE RUNBOOK ─────────────
@router.post("/runbooks")
async def create_runbook(data: dict):
    try:
        title    = (data.get("title")            or "").strip()
        category = (data.get("category")         or "").strip()
        steps    = (data.get("resolution_steps") or "").strip()

        if not title or not category or not steps:
            return {
                "type":    "error",
                "message": "title, category, and resolution_steps are required",
            }

        embed_text = f"""
Title: {title}
Category: {category}
Symptoms: {data.get('symptoms', '')}
Keywords: {data.get('keywords', title)}
Resolution: {steps}
"""
        embedding = await get_embedding(embed_text)
        if embedding:
            embedding = [float(x) for x in embedding]

        payload = {
            "title":            title,
            "category":         category,
            "keywords":         data.get("keywords") or title,
            "symptoms":         data.get("symptoms") or "",
            "resolution_steps": steps,
            "ci_asset":         data.get("ci_asset") or None,
            "status":           "Active",
            "embedding":        embedding,
        }

        saved = await insert_runbook(payload)

        if not saved:
            return {"type": "error", "message": "Failed to save runbook to database"}

        print(f"✅ New runbook created: {title} (id={saved.get('id')})")

        return {
            "type":    "success",
            "message": "Runbook created successfully",
            "id":      saved.get("id"),
        }

    except Exception as e:
        print(f"❌ create_runbook error: {e}")
        return {"type": "error", "message": str(e)}



@router.get("/tickets/{issueKey}/can-complete")
async def can_complete_ticket(issueKey: str):
    try:
        tickets = await get_all_tickets()
        ticket = next((t for t in tickets if t["issue_key"] == issueKey), None)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # get children of this ticket
        children = [
            t for t in tickets
            if t.get("parent_ticket_key") == issueKey
        ]

        open_children = [
            c["issue_key"]
            for c in children
            if c.get("status") != "Completed"
        ]

        return {
            "allowed": len(open_children) == 0,
            "open_children": open_children
        }

    except Exception as e:
        print(f"❌ can_complete_ticket error: {e}")
        raise HTTPException(status_code=500, detail=str(e))