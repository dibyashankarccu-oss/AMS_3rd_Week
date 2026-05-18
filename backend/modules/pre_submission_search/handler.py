from services.embedding_service import get_embedding

from repositories.ticket_repository import search_completed_tickets

from .agent import rerank_tickets

from .service import filter_candidates, is_valid_match


def normalize(text):
    return text.strip().lower() if text else None


async def search_similar_completed_tickets(
    summary,
    description="",
    app_name="",
    component_name=""
):

    def normalize(text):
        return text.strip().lower() if text else None

    text = f"""
    {summary}
    {description}
    """

    embedding = await get_embedding(text)

    if not embedding:
        return {"ticket": None}

    embedding = [float(x) for x in embedding]

    # PASS FILTERS HERE (SQL-level filtering)
    candidates = await search_completed_tickets(
        embedding,
        top_k=5,
        app_name=app_name,
        component_name=component_name
    )

    print("\nFOUND:")
    for c in candidates:
        print(c["issue_key"], c["similarity"])

    # VECTOR THRESHOLD FILTER
    candidates = filter_candidates(candidates)

    print("\nAFTER VECTOR FILTER:")
    for c in candidates:
        print(c["issue_key"], c["similarity"])

    if not candidates:
        return {"ticket": None}

    # 🔥 HARD METADATA FILTER (CRITICAL FIX)
    candidates = [
        c for c in candidates
        if (not app_name or normalize(c.get("app_name")) == normalize(app_name))
        and (not component_name or normalize(c.get("component_name")) == normalize(component_name))
    ]

    print("\nAFTER APP/COMPONENT FILTER:")
    for c in candidates:
        print(c["issue_key"], c["app_name"], c["component_name"])

    if not candidates:
        return {"ticket": None}

    # LLM RERANKING
    best = await rerank_tickets(
        summary,
        description,
        candidates
    )

    print("\nBEST:", best)

    # STEP 1: LLM SCORE VALIDATION
    if not is_valid_match(best):
        print("REJECTED (LLM threshold)")
        return {"ticket": None}

    # STEP 2: FINAL STRICT GUARD (SAFETY NET)
    if app_name:
        if normalize(best.get("app_name")) != normalize(app_name):
            print("REJECTED (APP MISMATCH)")
            return {"ticket": None}

    if component_name:
        if normalize(best.get("component_name")) != normalize(component_name):
            print("REJECTED (COMPONENT MISMATCH)")
            return {"ticket": None}

    return {"ticket": best}