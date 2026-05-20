# app/v1/ticket_routes.py

from fastapi import APIRouter, HTTPException

# schemas + orchestrator
from schemas.ticket_schema import TicketRequest
from orchestrator.ams_orchestrator import handle_ticket
from repositories.ticket_repository import search_similar_tickets
from services.embedding_service import get_embedding

# repository layer
# repository layer
from repositories.ticket_repository import (
    get_all_tickets,
    update_status_cascade,
    get_ticket,
    get_children,
    update_parent,
    update_child_keys,
    promote_first_child_as_parent
)

# Jira integration
from services.jira_service import (
    complete_parent_and_children,
    unlink_duplicate_comments
)

from services.merge_service import merge_tickets

from modules.pre_submission_search.handler import (
    search_similar_completed_tickets
)
from repositories.ticket_event_repository import log_event
from services.app_service import get_apps_with_components

router = APIRouter()


# ─────────────────────────────────────────────
# SUBMIT TICKET
# ─────────────────────────────────────────────
@router.post("/submit")
async def submit(data: TicketRequest):
    result = await handle_ticket(data)

    if not isinstance(result, dict):
        return {
            "type": "error",
            "message": "Invalid orchestrator response"
        }

    return result


# ─────────────────────────────────────────────
# GET ALL TICKETS
# ─────────────────────────────────────────────
@router.get("/tickets")
async def get_tickets():
    tickets = await get_all_tickets()

    if not isinstance(tickets, list):
        return []

    return tickets


@router.get("/tickets/{issueKey}/complete-check")
async def check_before_complete(issueKey: str):
    tickets = await get_all_tickets()

    current = next(
        (t for t in tickets if t["issue_key"] == issueKey),
        None
    )

    if not current:
        return {"type": "error", "message": "Ticket not found"}

    parent_key = current.get("parent_ticket_key") or current["issue_key"]

    children = [
        t for t in tickets
        if t.get("parent_ticket_key") == parent_key
    ]

    open_children = [
        c["issue_key"]
        for c in children
        if c.get("status") != "Completed"
    ]

    if open_children:
        return {
            "type": "warning",
            "requires_confirmation": True,
            "parent_key": parent_key,
            "open_children": open_children,
            "message": "Some children are still open"
        }

    return {
        "type": "safe",
        "parent_key": parent_key,
        "message": "Safe to complete"
    }


# ─────────────────────────────────────────────
# COMPLETE TICKET CASCADE (UPDATED)
# PARENT + ALL CHILDREN
# WITH OPEN CHILD CHECK + FORCE OPTION
# ─────────────────────────────────────────────
@router.put("/tickets/{issueKey}/complete")
async def complete_ticket(issueKey: str, force: bool = False):
    try:

        tickets = await get_all_tickets()

        if not tickets:
            return {
                "type": "error",
                "message": "No tickets found"
            }

        current = next(
            (
                t for t in tickets
                if t["issue_key"] == issueKey
            ),
            None
        )

        if not current:
            return {
                "type": "error",
                "message": "Ticket not found"
            }

        # If child clicked → use parent
        parent_key = (
                current.get("parent_ticket_key")
                or current.get("issue_key")
        )

        # ─────────────────────────────────────────────
        # CHECK CHILDREN STATUS
        # ─────────────────────────────────────────────
        children = [
            t for t in tickets
            if t.get("parent_ticket_key") == parent_key
        ]

        open_children = [
            c for c in children
            if c.get("status") != "Completed"
        ]

        # ─────────────────────────────────────────────
        # BLOCK IF OPEN CHILDREN EXIST (unless forced)
        # ─────────────────────────────────────────────
        if open_children and not force:
            return {
                "type": "warning",
                "message": "Some child tickets are still open",
                "requires_confirmation": True,
                "parent_key": parent_key,
                "open_children": [
                    c["issue_key"] for c in open_children
                ]
            }

        print(
            f"🔍 Completing parent + children: {parent_key}"
        )

        # ─────────────────────────────────────────────
        # UPDATE ALL JIRA ISSUES
        # ─────────────────────────────────────────────
        jira_ok = await complete_parent_and_children(parent_key)

        if not jira_ok:
            print(
                f"⚠️ Jira cascade update partially failed "
                f"for {parent_key}"
            )

        # ─────────────────────────────────────────────
        # UPDATE DB
        # ─────────────────────────────────────────────
        db_ok = await update_status_cascade(
            parent_key,
            "Completed"
        )
        await log_event(
            ticket_id=parent_key,
            event="PARENT_COMPLETED",
            actor="system",
            details="Parent and all children marked completed"
        )

        if not db_ok:
            return {
                "type": "error",
                "message": "Database update failed"
            }

        print(
            f"✅ Completed parent + all child tickets "
            f"for {parent_key}"
        )

        return {
            "type": "success",
            "message": "Parent and all child tickets marked completed",
            "id": parent_key
        }

    except Exception as e:

        print(f"❌ complete_ticket error: {e}")

        return {
            "type": "error",
            "message": str(e)
        }


# ─────────────────────────────────────────────
# GET TICKET BY ISSUE KEY (PARENT ONLY)
# USED FOR SEARCH BAR
# ─────────────────────────────────────────────
import re


@router.get("/tickets/search/{issueKey}")
async def search_by_id(issueKey: str):
    try:

        tickets = await get_all_tickets()

        if not tickets:
            return {
                "type": "error",
                "message": "No tickets found"
            }

        key = issueKey.strip().upper()

        # ─────────────────────────────
        # STEP 1: FIND EXACT TICKET
        # ─────────────────────────────
        current = next(
            (
                t for t in tickets
                if t["issue_key"].upper() == key
            ),
            None
        )

        if not current:
            return {
                "type": "error",
                "message": "Ticket not found"
            }

        # ─────────────────────────────
        # STEP 2: CHILD TICKET FLOW
        # ─────────────────────────────
        if current.get("child_key"):

            parent_key = current["parent_ticket_key"]

            parent = next(
                (
                    t for t in tickets
                    if t["issue_key"] == parent_key
                ),
                None
            )

            if not parent:
                return {
                    "type": "error",
                    "message": "Parent ticket not found"
                }

            children = [
                t for t in tickets
                if t.get("parent_ticket_key") == parent_key
            ]

            return {
                "type": "success",

                # IMPORTANT ORDER FOR UI
                "child": current,  # show first
                "parent_key": parent_key,  # display label
                "parent": parent,  # full card
                "children": children,

                "mode": "child-view"
            }

        # ─────────────────────────────
        # STEP 3: PARENT FLOW
        # ─────────────────────────────
        children = [
            t for t in tickets
            if t.get("parent_ticket_key") == current["issue_key"]
        ]

        return {
            "type": "success",
            "parent": current,
            "children": children,
            "mode": "parent-view"
        }

    except Exception as e:

        print(f"❌ search_by_id error: {e}")

        return {
            "type": "error",
            "message": str(e)
        }


# ─────────────────────────────────────────────
# MERGE TICKETS (DB ONLY)
# ─────────────────────────────────────────────
@router.post("/tickets/merge")
async def merge_tickets_api(payload: dict):
    """
    payload:
    {
        "target_parent_key": "TP-594",
        "source_parent_keys": ["TP-595", "TP-596"]
    }
    """

    try:

        target = payload.get("target_parent_key")
        sources = payload.get("source_parent_keys", [])

        # ─────────────────────────────
        # VALIDATION
        # ─────────────────────────────
        if not target or not isinstance(sources, list):
            return {
                "type": "error",
                "message": "Invalid merge request"
            }

        # remove duplicates
        sources = list(set(sources))

        # ensure target is included (optional safety)
        if target not in sources:
            sources.append(target)

        # remove target from "source-only logic safety"
        source_only = [
            s for s in sources
            if s != target
        ]

        if not source_only:
            return {
                "type": "error",
                "message": "No source tickets to merge"
            }

        # ─────────────────────────────
        # CALL SERVICE
        # ─────────────────────────────
        result = await merge_tickets(
            target_parent=target,
            source_parents=source_only
        )
        await log_event(
            ticket_id=target,
            event="MERGE_RECEIVED",
            actor="system",
            details=f"Merge completed with sources: {', '.join(source_only)}"
        )
        for s in source_only:
            await log_event(
                ticket_id=s,
                event="MERGED_INTO_TARGET",
                actor="system",
                details=f"Merged into target {target}"
            )

        return {
            "type": "success",
            "message": "Tickets merged successfully",
            "data": result
        }

    except Exception as e:

        return {
            "type": "error",
            "message": str(e)
        }


@router.put("/tickets/{issueKey}/detach")
async def detach_ticket(issueKey: str):
    try:

        tickets = await get_all_tickets()

        current = next(
            (
                t for t in tickets
                if t["issue_key"] == issueKey
            ),
            None
        )

        if not current:
            return {
                "type": "error",
                "message": "Ticket not found"
            }

        # only child tickets can be detached
        if not current.get("parent_ticket_key"):
            return {
                "type": "error",
                "message": "Only child tickets can be detached"
            }

        from repositories.ticket_repository import (
            detach_child_ticket
        )

        parent_key = current[
            "parent_ticket_key"
        ]

        # remove Jira comment links
        await unlink_duplicate_comments(
            parent_key,
            issueKey
        )

        # detach DB relationship
        ok = await detach_child_ticket(
            issueKey
        )
        # Child perspective
        await log_event(
            ticket_id=issueKey,
            event="DETACHED_FROM_PARENT",
            actor="system",
            details=f"Detached from parent {parent_key}"
        )

        # Parent perspective (important for traceability)
        await log_event(
            ticket_id=parent_key,
            event="CHILD_DETACHED",
            actor="system",
            details=f"Child {issueKey} detached"
        )

        if not ok:
            return {
                "type": "error",
                "message": "Detach failed"
            }

        return {
            "type": "success",
            "message":
                "Ticket detached successfully",
            "id": issueKey
        }

    except Exception as e:

        print(
            f"❌ detach_ticket error: {e}"
        )

        return {
            "type": "error",
            "message": str(e)
        }

    # ─────────────────────────────────────────────


# COMPLETE ONLY ONE TICKET
# ─────────────────────────────────────────────
@router.put("/tickets/{issueKey}/complete-single")
async def complete_single_ticket(issueKey: str):
    try:

        from repositories.ticket_repository import (
            get_ticket
        )

        ticket = await get_ticket(issueKey)

        if not ticket:
            return {
                "type": "error",
                "message": "Ticket not found"
            }

        from services.jira_service import (
            update_jira_status
        )

        jira_ok = await update_jira_status(
            issueKey
        )

        if not jira_ok:
            return {
                "type": "error",
                "message": "Jira update failed"
            }

        from repositories.ticket_repository import (
            supabase
        )

        supabase.table(
            "tickets"
        ).update({
            "status": "Completed"
        }).eq(
            "issue_key",
            issueKey
        ).execute()

        await log_event(
            ticket_id=issueKey,
            event="SINGLE_COMPLETED",
            actor="system",
            details="Single ticket marked completed"
        )

        return {
            "type": "success",
            "message": "Single ticket completed"
        }

    except Exception as e:

        return {
            "type": "error",
            "message": str(e)
        }


@router.post("/tickets/pre-search")
async def pre_submission_search(payload: dict):
    summary = payload.get("summary", "")
    description = payload.get("description", "")

    app_name = payload.get("app_name", "")
    component_name = payload.get("component_name", "")

    if not summary:
        return {"ticket": None}

    result = await search_similar_completed_tickets(
        summary,
        description,
        app_name,
        component_name
    )

    print("\nPRE SEARCH API RESPONSE:", result, "\n")

    return result


# ─────────────────────────────────────────────
# COMPLETE ONLY CHILDREN OF A PARENT
# Parent remains unchanged
# ─────────────────────────────────────────────
@router.put("/tickets/{issueKey}/complete-children")
async def complete_children_only(issueKey: str):
    try:

        ticket = await get_ticket(issueKey)

        if not ticket:
            return {
                "type": "error",
                "message": "Ticket not found"
            }

        parent_key = (
                ticket.get("parent_ticket_key")
                or ticket["issue_key"]
        )

        children = await get_children(
            parent_key
        )

        if not children:
            return {
                "type": "error",
                "message": "No child tickets found"
            }

        from services.jira_service import (
            update_jira_status
        )

        from repositories.ticket_repository import (
            update_children_status
        )

        # Jira only for children
        for child in children:
            await update_jira_status(
                child["issue_key"]
            )

        db_ok = await update_children_status(
            parent_key,
            "Completed"
        )
        await log_event(
            ticket_id=parent_key,
            event="CHILDREN_COMPLETED",
            actor="system",
            details="All child tickets completed"
        )

        if not db_ok:
            return {
                "type": "error",
                "message": "DB update failed"
            }

        return {
            "type": "success",
            "message": "All child tickets completed"
        }

    except Exception as e:

        print(
            "❌ complete_children_only:",
            e
        )

        return {
            "type": "error",
            "message": str(e)
        }


@router.get("/apps-with-components")
async def apps_with_components():
    try:
        data = await get_apps_with_components()

        return {
            "type": "success",
            "data": data
        }

    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }