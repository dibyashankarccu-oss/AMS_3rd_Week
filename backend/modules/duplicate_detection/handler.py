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

from repositories.app_component_resolver import resolve_app_component


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

    # Safe extraction (works for both dict + object)
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

    urgency = getattr(data, "urgency", None) or data.get("urgency", "")
    impact = getattr(data, "impact", None) or data.get("impact", "")

    # ─────────────────────────────────────────────
    # FIX: DEFAULT APP / COMPONENT
    # ─────────────────────────────────────────────
    if not app_name or app_name.lower() == "general":
        app_name = "General"
        app_code = None
    else:
        app_code, _ = await resolve_app_component(app_name, component_name)

    if not component_name or component_name.lower() == "general":
        component_name = "General"
        component_code = None
    else:
        _, component_code = await resolve_app_component(app_name, component_name)

    # ─────────────────────────────────────────────
    # STEP 1 — VECTOR SEARCH
    # ─────────────────────────────────────────────
    candidate_tickets = []

    query_embedding = await get_embedding(summary)

    if query_embedding:
        query_embedding = [float(x) for x in query_embedding]

        candidate_tickets = await search_similar_tickets(
            query_embedding=query_embedding,
            top_k=5,
            app_name=app_name,
            component_name=component_name
        )

    # ─────────────────────────────────────────────
    # FALLBACK SEARCH
    # ─────────────────────────────────────────────
    if not candidate_tickets:
        tickets = await get_all_tickets() or []

        candidate_tickets = [
            t for t in tickets
            if (
                t.get("status") == "Open"
                and not t.get("is_duplicate")
                and not t.get("child_key")
                and (t.get("app_name") or "General") == app_name
                and (t.get("component_name") or "General") == component_name
            )
        ]

    # ─────────────────────────────────────────────
    # STEP 2 — SIMILARITY CHECK
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

        child_key = await generate_child_id(parent_key)

        new_ticket = await create_ticket(data, summary)

        issue_key = new_ticket.get("issueKey") if new_ticket else None

        if not issue_key:
            return {
                **state,
                "type": "error",
                "message": "Failed to create Jira duplicate ticket"
            }

        await link_duplicate_comments(parent_key, issue_key)

        await insert_ticket({
            "issue_key": issue_key,
            "child_key": child_key,

            "name": name,
            "email": email,

            "summary": summary,
            "description": description,

            "app_name": app_name,
            "app_code": app_code,

            "component_name": component_name,
            "component_code": component_code,

            "urgency": urgency,
            "impact": impact,

            "status": "Open",
            "is_duplicate": True,
            "parent_ticket_key": parent_key,
            "embedding": None,
        })

        return {
            **state,
            "id": issue_key,
            "issue_key": issue_key,
            "type": "success",
            "message": "Duplicate ticket linked successfully",
            "child_key": child_key,
            "parent_ticket": parent_key,
            "is_duplicate": True
        }

    # ─────────────────────────────────────────────
    # NEW TICKET FLOW
    # ─────────────────────────────────────────────
    related = await generate_related(summary)

    new_ticket = await create_ticket(data, related)

    issue_key = new_ticket.get("issueKey") if new_ticket else None

    if not issue_key:
        return {
            **state,
            "type": "error",
            "message": "Failed to create Jira ticket"
        }

    embedding = await get_embedding(f"{summary}\n{related}")

    if embedding:
        embedding = [float(x) for x in embedding]

    await insert_ticket({
        "issue_key": issue_key,
        "child_key": None,

        "name": name,
        "email": email,

        "summary": summary,
        "description": description,

        "app_name": app_name,
        "app_code": app_code,

        "component_name": component_name,
        "component_code": component_code,

        "urgency": urgency,
        "impact": impact,

        "status": "Open",
        "is_duplicate": False,
        "parent_ticket_key": None,
        "embedding": embedding
    })

    return {
        **state,
        "id": issue_key,
        "issue_key": issue_key,
        "type": "success",
        "message": "Ticket registered successfully",
        "child_key": None,
        "is_duplicate": False
    }