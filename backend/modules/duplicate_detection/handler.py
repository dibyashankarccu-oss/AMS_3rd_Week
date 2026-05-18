# modules/duplicate_detection/handler.py

from core.constants import SIMILARITY_THRESHOLD

from modules.duplicate_detection.agent import find_best_match
from modules.duplicate_detection.service import generate_related

from services.jira_service import (
    create_ticket,
    generate_child_id,
    link_duplicate_comments
)

from services.embedding_service import get_embedding

from repositories.ticket_repository import (
    get_all_tickets,
    insert_ticket,
    search_similar_tickets
)


# ─────────────────────────────────────────────
# DUPLICATE DETECTION FLOW
# ─────────────────────────────────────────────
async def handle_duplicate_flow(state):

    data = state.get("data") or {}
    summary = state.get("summary", "")

    # ─────────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────────
    if not data or not summary:
        return {
            **state,
            "type": "error",
            "message": "Invalid request payload"
        }

    # Safe extraction
    name = getattr(data, "name", None) or data.get("name", "")
    email = getattr(data, "email", None) or data.get("email", "")

    description = (
        getattr(data, "description", None)
        or data.get("description", "")
    )

    app_name = (
        getattr(data, "app_name", None)
        or data.get("app_name", "")
    )

    component_name = (
        getattr(data, "component_name", None)
        or data.get("component_name", "")
    )

    # ─────────────────────────────────────────────
    # STEP 1 — VECTOR SEARCH
    # MATCH ONLY SAME APP + COMPONENT
    # ─────────────────────────────────────────────
    candidate_tickets = []

    query_embedding = await get_embedding(summary)

    if query_embedding:

        query_embedding = [
            float(x)
            for x in query_embedding
        ]

        candidate_tickets = await search_similar_tickets(
            query_embedding=query_embedding,
            top_k=5,
            app_name=app_name,
            component_name=component_name
        )

    # ─────────────────────────────────────────────
    # FALLBACK
    # ONLY SAME APP + COMPONENT
    # ─────────────────────────────────────────────
    if not candidate_tickets:

        tickets = await get_all_tickets() or []

        candidate_tickets = [
            t for t in tickets
            if (
                t.get("status") == "Open"
                and not t.get("is_duplicate")
                and not t.get("child_key")
                and t.get("app_name") == app_name
                and t.get("component_name") == component_name
            )
        ]

    # ─────────────────────────────────────────────
    # STEP 2 — LLM SIMILARITY
    # ─────────────────────────────────────────────
    score, parent = await find_best_match(
        summary,
        candidate_tickets
    )

    # ─────────────────────────────────────────────
    # DUPLICATE FLOW
    # ─────────────────────────────────────────────
    if parent and score >= SIMILARITY_THRESHOLD:

        parent_key = parent.get("issue_key")

        child_key = await generate_child_id(
            parent_key
        )

        new_ticket = await create_ticket(
            data,
            summary
        )

        issue_key = (
            new_ticket.get("issueKey")
            if new_ticket
            else None
        )

        if not issue_key:
            return {
                **state,
                "type": "error",
                "message":
                "Failed to create Jira duplicate ticket"
            }

        await link_duplicate_comments(
            parent_key,
            issue_key
        )

        await insert_ticket({

            "issue_key": issue_key,
            "child_key": child_key,

            "name": name,
            "email": email,

            "summary": summary,
            "description": description,

            "app_name": app_name,
            "component_name": component_name,
            "urgency": getattr(data, "urgency", ""),
            "impact": getattr(data, "impact", ""),

            "status": "Open",

            "is_duplicate": True,

            "parent_ticket_key": parent_key,

            "embedding": None,
        })

        return {
            **state,

            "id": issue_key,   # important for RCA

            "type": "success",

            "message":
            "Duplicate ticket linked successfully",

            "child_key": child_key,

            "parent_ticket": parent_key,

            "is_duplicate": True
        }

    # ─────────────────────────────────────────────
    # NEW PARENT FLOW
    # ─────────────────────────────────────────────
    related = await generate_related(summary)

    new_ticket = await create_ticket(
        data,
        related
    )

    issue_key = (
        new_ticket.get("issueKey")
        if new_ticket
        else None
    )

    if not issue_key:
        return {
            **state,
            "type": "error",
            "message":
            "Failed to create Jira ticket"
        }

    embedding = await get_embedding(
        f"{summary}\n{related}"
    )

    if embedding:
        embedding = [
            float(x)
            for x in embedding
        ]

    await insert_ticket({

        "issue_key": issue_key,

        "child_key": None,

        "name": name,
        "email": email,

        "summary": summary,
        "description": description,

        "app_name": app_name,
        "component_name": component_name,

        "urgency": getattr(data, "urgency", ""),
        "impact": getattr(data, "impact", ""),

        "status": "Open",

        "is_duplicate": False,

        "parent_ticket_key": None,

        "embedding": embedding
    })

    return {
        **state,

        "id": issue_key,   # important for RCA

        "type": "success",

        "message":
        "Ticket registered successfully",

        "child_key": None,

        "is_duplicate": False
    }