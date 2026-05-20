# app/v1/rca_routes.py

from fastapi import APIRouter, HTTPException

from core.constants import RCA_SIMILARITY_THRESHOLD, KB_SIMILARITY_THRESHOLD
from repositories.ticket_repository import (
    get_all_tickets,
    search_completed_tickets_with_rca,
    update_ticket_rca,
)
from repositories.rca_kb_repository import search_rca_knowledge_base
from services.embedding_service import get_embedding
from modules.copilot_rca.agent import (
    is_same_issue,
    is_kb_applicable,
    generate_fresh_rca,
    generate_clarification_questions,
)
from modules.copilot_rca.service import get_confidence_label, get_rca_summary

router = APIRouter()


@router.get("/tickets/{issueKey}/rca")
async def get_rca(issueKey: str):
    try:
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")
        if ticket.get("parent_ticket_key"):
            raise HTTPException(status_code=400, detail="RCA only available on parent tickets")

        # ── CACHE HIT ──
        if ticket.get("rca_root_cause"):
            confidence = ticket.get("rca_confidence", "LOW")
            affected   = ticket.get("rca_affected",   "Unknown")
            print(f"📦 [{issueKey}] CACHE HIT")
            return {
                "root_cause":         ticket["rca_root_cause"],
                "affected":           affected,
                "confidence":         confidence,
                "confidence_label":   get_confidence_label(confidence),
                "summary":            get_rca_summary(confidence, affected),
                "source":             ticket.get("rca_source"),
                "needs_human_review": confidence == "LOW",
                "clarification":      None,
                "cached":             True,
            }

        summary     = ticket.get("summary", "")
        description = ticket.get("description", "")
        app_code    = ticket.get("app_code")
        comp_code   = ticket.get("component_code")

        if not description:
            raise HTTPException(status_code=400, detail="Ticket description required for RCA")

        current         = {"summary": summary, "description": description}
        query_embedding = await get_embedding(f"{summary} {description}")
        if query_embedding:
            query_embedding = [float(x) for x in query_embedding]

        # ── LAYER A: KB MATCH ──
        if query_embedding:
            kb_results = await search_rca_knowledge_base(
                query_embedding, top_k=3,
                app_code=app_code, component_code=comp_code
            )
            if not kb_results and (app_code or comp_code):
                kb_results = await search_rca_knowledge_base(query_embedding, top_k=3)

            if kb_results:
                top_kb = kb_results[0]
                kb_sim = top_kb.get("similarity", 0)
                print(f"[RCA-A] KB: '{top_kb.get('title')}' similarity={kb_sim:.3f}")

                if kb_sim >= KB_SIMILARITY_THRESHOLD:
                    applicable, _ = is_kb_applicable(current, top_kb)
                    if applicable:
                        confidence = top_kb.get("confidence", "HIGH")
                        affected   = top_kb.get("affected_component", "Unknown")
                        await update_ticket_rca(
                            issue_key=issueKey, root_cause=top_kb.get("root_cause"),
                            affected_component=affected, confidence=confidence,
                            source="knowledge_base",
                        )
                        return {
                            "root_cause":         top_kb.get("root_cause"),
                            "affected":           affected,
                            "confidence":         confidence,
                            "confidence_label":   get_confidence_label(confidence),
                            "summary":            get_rca_summary(confidence, affected),
                            "source":             "knowledge_base",
                            "needs_human_review": False,
                            "clarification":      None,
                            "cached":             False,
                        }

        # ── LAYER B: PAST TICKET MATCH ──
        if query_embedding:
            matches    = await search_completed_tickets_with_rca(query_embedding, top_k=5)
            candidates = [t for t in matches if t.get("issue_key") != issueKey]
            if candidates:
                top = candidates[0]
                sim = top.get("similarity", 0)
                print(f"[RCA-B] Past ticket '{top.get('issue_key')}' similarity={sim:.3f}")
                if sim >= RCA_SIMILARITY_THRESHOLD:
                    same, _ = is_same_issue(current, top)
                    if same:
                        confidence = top.get("rca_confidence", "MEDIUM")
                        affected   = top.get("rca_affected", "Unknown")
                        await update_ticket_rca(
                            issue_key=issueKey, root_cause=top.get("rca_root_cause"),
                            affected_component=affected, confidence=confidence,
                            source="matched",
                        )
                        return {
                            "root_cause":         top.get("rca_root_cause"),
                            "affected":           affected,
                            "confidence":         confidence,
                            "confidence_label":   get_confidence_label(confidence),
                            "summary":            get_rca_summary(confidence, affected),
                            "source":             "matched",
                            "needs_human_review": confidence == "LOW",
                            "clarification":      None,
                            "cached":             False,
                        }

        # ── LAYER C: FRESH GENERATION ──
        print(f"🤖 [{issueKey}] Generating fresh RCA")
        result             = generate_fresh_rca(current)
        confidence         = result.get("confidence", "LOW")
        needs_human_review = result.get("needs_human_review", confidence == "LOW")
        affected           = result.get("affected_component", "Unknown")
        clarification      = result.get("clarification")

        if needs_human_review:
            return {
                "root_cause":         result.get("root_cause"),
                "affected":           affected,
                "confidence":         confidence,
                "confidence_label":   get_confidence_label(confidence),
                "summary":            "⚠️ Insufficient detail — human review required",
                "source":             "generated_low_confidence",
                "needs_human_review": True,
                "clarification":      clarification,
                "cached":             False,
            }

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("root_cause"))

        await update_ticket_rca(
            issue_key=issueKey, root_cause=result.get("root_cause"),
            affected_component=affected, confidence=confidence, source="generated",
        )
        return {
            "root_cause":         result.get("root_cause"),
            "affected":           affected,
            "confidence":         confidence,
            "confidence_label":   get_confidence_label(confidence),
            "summary":            get_rca_summary(confidence, affected),
            "source":             "generated",
            "needs_human_review": False,
            "clarification":      None,
            "cached":             False,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ get_rca error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tickets/{issueKey}/rca/clarify")
async def submit_rca_clarification(issueKey: str, data: dict):
    try:
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")

        questions     = data.get("questions", [])
        answers       = data.get("answers",   [])
        original_desc = ticket.get("description", "")
        summary       = ticket.get("summary",     "")

        qa_block = "\n\nAdditional Information from Engineer:\n"
        for i, (q, a) in enumerate(zip(questions, answers)):
            if a and a.strip():
                qa_block += f"Q{i+1}: {q}\nA{i+1}: {a}\n\n"

        result             = generate_fresh_rca({"summary": summary,
                                                  "description": original_desc + qa_block})
        confidence         = result.get("confidence", "LOW")
        needs_human_review = result.get("needs_human_review", confidence == "LOW")
        affected           = result.get("affected_component", "Unknown")

        if needs_human_review:
            return {
                "root_cause":         "Insufficient information. Flagged for L3 manual review.",
                "affected":           affected,
                "confidence":         "LOW",
                "confidence_label":   get_confidence_label("LOW"),
                "summary":            "🚨 Manual L3 review required",
                "source":             "hitl_escalated",
                "needs_human_review": True,
                "clarification":      result.get("clarification"),
                "cached":             False,
            }

        await update_ticket_rca(
            issue_key=issueKey, root_cause=result.get("root_cause"),
            affected_component=affected, confidence=confidence,
            source="generated_with_clarification",
        )
        return {
            "root_cause":         result.get("root_cause"),
            "affected":           affected,
            "confidence":         confidence,
            "confidence_label":   get_confidence_label(confidence),
            "summary":            get_rca_summary(confidence, affected),
            "source":             "generated_with_clarification",
            "needs_human_review": False,
            "clarification":      None,
            "cached":             False,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ submit_rca_clarification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tickets/{issueKey}/rca/human")
async def submit_human_rca(issueKey: str, data: dict):
    try:
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")
        if ticket.get("parent_ticket_key"):
            raise HTTPException(status_code=400, detail="RCA override only on parent tickets")

        root_cause = (data.get("root_cause") or "").strip()
        if not root_cause:
            raise HTTPException(status_code=422, detail="root_cause is required")

        affected = (data.get("affected") or ticket.get("rca_affected") or "Unknown").strip()

        await update_ticket_rca(
            issue_key=issueKey, root_cause=root_cause,
            affected_component=affected, confidence="HUMAN", source="human_override",
        )
        print(f"✍️  [{issueKey}] Human RCA saved")
        return {
            "root_cause":         root_cause,
            "affected":           affected,
            "confidence":         "HUMAN",
            "confidence_label":   "Human Verified — manually reviewed and confirmed",
            "summary":            f"✍️ Root cause written by human reviewer for: {affected}",
            "source":             "human_override",
            "needs_human_review": False,
            "cached":             False,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ submit_human_rca error: {e}")
        raise HTTPException(status_code=500, detail=str(e))