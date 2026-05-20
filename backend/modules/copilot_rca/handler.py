# modules/copilot_rca/handler.py

from modules.copilot_rca.agent import is_same_issue, generate_fresh_rca, is_kb_applicable
from modules.copilot_rca.service import get_confidence_label, get_rca_summary
from repositories.ticket_repository import update_ticket_rca, search_completed_tickets_with_rca
from repositories.rca_kb_repository import search_rca_knowledge_base
from services.embedding_service import get_embedding
from services.jira_service import add_rca_comment
from core.constants import RCA_SIMILARITY_THRESHOLD, KB_SIMILARITY_THRESHOLD


async def handle_rca_flow(state: dict) -> dict:
    try:
        issue_key   = state.get("issue_key") or state.get("id")
        summary     = state.get("summary", "")
        description = ""
        app_code    = None
        comp_code   = None

        raw_data = state.get("data")
        if raw_data:
            if hasattr(raw_data, "description"):
                description = raw_data.description or ""
            elif isinstance(raw_data, dict):
                description = raw_data.get("description", "")

            app_code  = (getattr(raw_data, "app_code",       None)
                         if hasattr(raw_data, "app_code")
                         else raw_data.get("app_code")  if isinstance(raw_data, dict) else None)
            comp_code = (getattr(raw_data, "component_code", None)
                         if hasattr(raw_data, "component_code")
                         else raw_data.get("component_code") if isinstance(raw_data, dict) else None)

        if not summary or not description:
            return {**state, "type": "error",
                    "message": "RCA module: summary or description is empty"}

        current         = {"summary": summary, "description": description}
        query_embedding = await get_embedding(f"{summary} {description}")
        if query_embedding:
            query_embedding = [float(x) for x in query_embedding]

        root_cause = None
        affected   = None
        confidence = "LOW"
        source     = "generated"

        # ── LAYER A: KB MATCH ──
        if query_embedding:
            try:
                # Try with app/component filter first
                kb_results = await search_rca_knowledge_base(
                    query_embedding, top_k=3,
                    app_code=app_code, component_code=comp_code
                )
                # Fallback to unfiltered if no results
                if not kb_results and (app_code or comp_code):
                    print(f"[RCA-A] No filtered KB match — trying unfiltered")
                    kb_results = await search_rca_knowledge_base(query_embedding, top_k=3)

                if kb_results:
                    top_kb = kb_results[0]
                    kb_sim = top_kb.get("similarity", 0)
                    print(f"[RCA-A] KB top: '{top_kb.get('title')}' similarity={kb_sim:.3f}")

                    if kb_sim >= KB_SIMILARITY_THRESHOLD:
                        applicable, _ = is_kb_applicable(current, top_kb)
                        if applicable:
                            root_cause = top_kb.get("root_cause")
                            affected   = top_kb.get("affected_component", "Unknown")
                            confidence = top_kb.get("confidence", "HIGH")
                            source     = "knowledge_base"
                            print(f"✅ [{issue_key}] KB match: '{top_kb.get('title')}'")
                        else:
                            print(f"⚠️  [{issue_key}] KB match rejected by LLM")
                    else:
                        print(f"🚫 [{issue_key}] KB similarity {kb_sim:.3f} below threshold {KB_SIMILARITY_THRESHOLD}")
            except Exception as e:
                print(f"⚠️  [{issue_key}] KB search error: {e}")

        # ── LAYER B: PAST TICKET MATCH ──
        if root_cause is None and query_embedding:
            try:
                matches    = await search_completed_tickets_with_rca(query_embedding, top_k=5)
                candidates = [t for t in matches if t.get("issue_key") != issue_key]
                print(f"[RCA-B] Past ticket candidates: {len(candidates)}")

                if candidates:
                    top = candidates[0]
                    sim = top.get("similarity", 0)
                    print(f"[RCA-B] Top: '{top.get('issue_key')}' similarity={sim:.3f}")

                    if sim >= RCA_SIMILARITY_THRESHOLD:
                        same, _ = is_same_issue(current, top)
                        if same:
                            root_cause = top.get("rca_root_cause")
                            affected   = top.get("rca_affected", "Unknown")
                            confidence = top.get("rca_confidence", "MEDIUM")
                            source     = "matched"
                            print(f"✅ [{issue_key}] Past ticket match: '{top.get('issue_key')}'")
                        else:
                            print(f"⚠️  [{issue_key}] Past ticket confirmed DIFFERENT")
                    else:
                        print(f"🚫 [{issue_key}] Similarity {sim:.3f} below threshold {RCA_SIMILARITY_THRESHOLD}")
                else:
                    print(f"ℹ️  [{issue_key}] No completed tickets with RCA available")
            except Exception as e:
                print(f"⚠️  [{issue_key}] Past ticket search error: {e}")

        # ── LAYER C: FRESH LLM GENERATION ──
        if root_cause is None:
            print(f"🤖 [{issue_key}] Generating fresh RCA")
            result     = generate_fresh_rca(current)
            root_cause = result.get("root_cause", "")
            affected   = result.get("affected_component", "Unknown")
            confidence = result.get("confidence", "LOW")
            source     = "generated"

        # ── SAVE TO SUPABASE ──
        if issue_key:
            saved = await update_ticket_rca(
                issue_key          = issue_key,
                root_cause         = root_cause,
                affected_component = affected,
                confidence         = confidence,
                source             = source,
            )
            if saved:
                print(f"💾 [{issue_key}] RCA saved (confidence={confidence}, source={source})")
            else:
                print(f"⚠️  [{issue_key}] DB save failed — still posting Jira comment")

            # ── POST JIRA COMMENT — always fires ──
            await add_rca_comment(
                issue_key  = issue_key,
                root_cause = root_cause,
                affected   = affected,
                confidence = confidence,
                source     = source,
            )
        else:
            print("⚠️  handle_rca_flow: no issue_key in state — skipping save and comment")

        return {
            **state,
            "type":                 "rca_complete",
            "message":              root_cause or "",
            "rca_root_cause":       root_cause,
            "rca_affected":         affected,
            "rca_confidence":       confidence,
            "rca_confidence_label": get_confidence_label(confidence),
            "rca_summary":          get_rca_summary(confidence, affected),
        }

    except Exception as e:
        print(f"❌ handle_rca_flow error: {e}")
        return {**state, "type": "error", "message": f"RCA module failed: {str(e)}"}