# app/v1/rca_routes.py

from fastapi import APIRouter, HTTPException

from core.constants import RCA_SIMILARITY_THRESHOLD
from core.constants import KB_SIMILARITY_THRESHOLD
from repositories.ticket_repository import (
    get_all_tickets,
    search_completed_tickets_with_rca,
    update_ticket_rca,
)
from repositories.rca_kb_repository import (
    search_rca_knowledge_base,
    insert_rca_knowledge,
)
from services.embedding_service import get_embedding
from modules.copilot_rca.agent import (
    is_same_issue,
    is_kb_applicable,
    generate_fresh_rca,
    generate_clarification_questions,
)
from modules.copilot_rca.handler import handle_rca_flow
from modules.copilot_rca.service import get_confidence_label, get_rca_summary

router = APIRouter()

# ── KB similarity threshold (slightly lower than ticket threshold) ──



# ─────────────────────────────────────────────────────────────
# GET RCA FOR TICKET
# ─────────────────────────────────────────────────────────────
@router.get("/tickets/{issueKey}/rca")
async def get_rca(issueKey: str):
    try:
        # ── 1. Find the ticket ──
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")

        # ── 2. Block RCA on child/duplicate tickets ──
        if ticket.get("parent_ticket_key"):
            raise HTTPException(
                status_code=400,
                detail="RCA is only available on parent tickets"
            )

        # ── 3. Return cached result if already computed ──
        if ticket.get("rca_root_cause"):
            confidence = ticket.get("rca_confidence", "LOW")
            affected   = ticket.get("rca_affected", "Unknown")
            print(f"📦 [{issueKey}] CACHE HIT — returning stored RCA")
            return {
                "root_cause":        ticket.get("rca_root_cause"),
                "affected":          affected,
                "steps":             ticket.get("rca_steps", []),
                "confidence":        confidence,
                "confidence_label":  get_confidence_label(confidence),
                "summary":           get_rca_summary(confidence, affected),
                "source":            ticket.get("rca_source"),
                "matched_from":      ticket.get("rca_matched_from"),
                "matched_summary":   ticket.get("rca_matched_summary"),
                "needs_human_review": confidence == "LOW",
                "clarification":     None,
                "cached":            True,
            }

        # ── 4. Validate description ──
        summary     = ticket.get("summary", "")
        description = ticket.get("description", "")

        if not description:
            raise HTTPException(
                status_code=400,
                detail="Ticket has no description — RCA requires description"
            )

        current = {"summary": summary, "description": description}

        # ── 5. Embed current ticket ──
        query_embedding = await get_embedding(f"{summary} {description}")
        if query_embedding:
            query_embedding = [float(x) for x in query_embedding]

        # ═══════════════════════════════════════════════════════
        # LAYER A — RCA KNOWLEDGE BASE SEARCH
        # ═══════════════════════════════════════════════════════
        kb_match = None

        if query_embedding:
            kb_results = await search_rca_knowledge_base(query_embedding, top_k=3)

            if kb_results:
                top_kb       = kb_results[0]
                kb_similarity = top_kb.get("similarity", 0)

                print(f"[RCA] KB top match: '{top_kb.get('title')}' similarity={kb_similarity:.3f}")

                if kb_similarity >= KB_SIMILARITY_THRESHOLD:
                    print(f"🔍 [{issueKey}] KB match above threshold — asking LLM to verify")
                    applicable, kb_conf = is_kb_applicable(current, top_kb)

                    if applicable:
                        kb_match = top_kb
                        kb_match["match_confidence"] = kb_conf
                        print(f"✅ [{issueKey}] KB MATCH CONFIRMED — using KB entry: '{top_kb.get('title')}'")
                    else:
                        print(f"⚠️  [{issueKey}] KB match REJECTED by LLM — falling through")
                else:
                    print(f"🚫 [{issueKey}] KB similarity {kb_similarity:.3f} below threshold {KB_SIMILARITY_THRESHOLD}")

        # ── 6A. KB Match → return KB RCA directly (fastest, no LLM generation) ──
        if kb_match:
            confidence = kb_match.get("confidence", "HIGH")
            affected   = kb_match.get("affected_component", "Unknown")
            steps_raw  = kb_match.get("resolution_steps", [])

            steps = steps_raw if isinstance(steps_raw, list) else []

            await update_ticket_rca(
                issue_key          = issueKey,
                root_cause         = kb_match.get("root_cause"),
                affected_component = affected,
                resolution_steps   = steps,
                confidence         = confidence,
                source             = "knowledge_base",
                matched_from       = f"KB:{kb_match.get('id')}",
                matched_summary    = kb_match.get("title"),
            )
            print(f"💾 [{issueKey}] KB RCA saved from '{kb_match.get('title')}'")

            return {
                "root_cause":        kb_match.get("root_cause"),
                "affected":          affected,
                "steps":             steps,
                "confidence":        confidence,
                "confidence_label":  get_confidence_label(confidence),
                "summary":           get_rca_summary(confidence, affected),
                "source":            "knowledge_base",
                "matched_from":      f"KB: {kb_match.get('title')}",
                "matched_summary":   kb_match.get("symptoms"),
                "needs_human_review": False,
                "clarification":     None,
                "cached":            False,
            }

        # ═══════════════════════════════════════════════════════
        # LAYER B — PAST TICKET SEARCH
        # ═══════════════════════════════════════════════════════
        best = None
        candidates = []

        if query_embedding:
            matches    = await search_completed_tickets_with_rca(query_embedding, top_k=5)
            candidates = [t for t in matches if t.get("issue_key") != issueKey]

            if candidates:
                top        = candidates[0]
                similarity = top.get("similarity", 0)

                print(f"[RCA] Past ticket top match: '{top.get('issue_key')}' similarity={similarity:.3f}")

                if similarity >= RCA_SIMILARITY_THRESHOLD:
                    print(f"🔍 [{issueKey}] Past ticket above threshold — asking LLM to verify")
                    same, confidence = is_same_issue(current, top)

                    if same:
                        best = top
                        best["match_confidence"] = confidence
                        print(f"✅ [{issueKey}] Past ticket CONFIRMED same issue — copying RCA from '{top.get('issue_key')}'")
                    else:
                        print(f"⚠️  [{issueKey}] Past ticket confirmed DIFFERENT — falling through to generation")
                else:
                    print(f"🚫 [{issueKey}] Past ticket similarity {similarity:.3f} below threshold")

        # ── 7A. Past ticket match → copy RCA ──
        if best:
            confidence = best.get("rca_confidence", "LOW")
            affected   = best.get("rca_affected", "Unknown")

            await update_ticket_rca(
                issue_key          = issueKey,
                root_cause         = best.get("rca_root_cause"),
                affected_component = affected,
                resolution_steps   = best.get("rca_steps", []),
                confidence         = confidence,
                source             = "matched",
                matched_from       = best.get("issue_key"),
                matched_summary    = best.get("summary"),
            )
            print(f"💾 [{issueKey}] Matched RCA saved from past ticket '{best.get('issue_key')}'")

            return {
                "root_cause":        best.get("rca_root_cause"),
                "affected":          affected,
                "steps":             best.get("rca_steps", []),
                "confidence":        confidence,
                "confidence_label":  get_confidence_label(confidence),
                "summary":           get_rca_summary(confidence, affected),
                "source":            "matched",
                "matched_from":      best.get("issue_key"),
                "matched_summary":   best.get("summary"),
                "needs_human_review": confidence == "LOW",
                "clarification":     None,
                "cached":            False,
            }

        # ═══════════════════════════════════════════════════════
        # LAYER C — FRESH LLM GENERATION
        # ═══════════════════════════════════════════════════════
        source_reason = "no KB or past ticket match found"
        print(f"🤖 [{issueKey}] Generating fresh RCA ({source_reason})")

        result = generate_fresh_rca(current)

        confidence         = result.get("confidence", "LOW")
        needs_human_review = result.get("needs_human_review", confidence == "LOW")
        clarification      = result.get("clarification")

        # ── HITL: if LOW confidence, do NOT save to DB — return questions instead ──
        if needs_human_review:
            print(f"🧑‍💻 [{issueKey}] HITL TRIGGERED — returning clarification questions (NOT saving to DB)")
            return {
                "root_cause":        result.get("root_cause"),
                "affected":          result.get("affected_component"),
                "steps":             result.get("resolution_steps", []),
                "confidence":        confidence,
                "confidence_label":  get_confidence_label(confidence),
                "summary":           f"⚠️ Insufficient detail for confident RCA — human review required",
                "source":            "generated_low_confidence",
                "matched_from":      None,
                "matched_summary":   None,
                "needs_human_review": True,
                "clarification":     clarification,
                "cached":            False,
            }

        # ── HIGH/MEDIUM confidence — save to DB ──
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("root_cause"))

        await update_ticket_rca(
            issue_key          = issueKey,
            root_cause         = result.get("root_cause"),
            affected_component = result.get("affected_component"),
            resolution_steps   = result.get("resolution_steps", []),
            confidence         = confidence,
            source             = "generated",
            matched_from       = None,
            matched_summary    = None,
        )
        print(f"💾 [{issueKey}] Fresh RCA saved (confidence: {confidence})")

        affected = result.get("affected_component", "Unknown")

        return {
            "root_cause":        result.get("root_cause"),
            "affected":          affected,
            "steps":             result.get("resolution_steps", []),
            "confidence":        confidence,
            "confidence_label":  get_confidence_label(confidence),
            "summary":           get_rca_summary(confidence, affected),
            "source":            "generated",
            "matched_from":      None,
            "matched_summary":   None,
            "needs_human_review": False,
            "clarification":     None,
            "cached":            False,
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"❌ get_rca error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# HITL — SUBMIT CLARIFICATION ANSWERS
# Frontend posts engineer's answers → retriggers RCA generation
# ─────────────────────────────────────────────────────────────
@router.post("/tickets/{issueKey}/rca/clarify")
async def submit_rca_clarification(issueKey: str, data: dict):
    """
    Called when an engineer provides answers to HITL clarification questions.
    Merges answers into the original description and re-runs RCA generation.
    """
    try:
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")

        answers      = data.get("answers", [])
        questions    = data.get("questions", [])
        original_desc = ticket.get("description", "")
        summary      = ticket.get("summary", "")

        # ── Enrich description with Q&A ──
        qa_block = "\n\nAdditional Information from Engineer:\n"
        for i, (q, a) in enumerate(zip(questions, answers)):
            if a and a.strip():
                qa_block += f"Q{i+1}: {q}\nA{i+1}: {a}\n\n"

        enriched_description = original_desc + qa_block

        print(f"🔄 [{issueKey}] HITL answers received — re-running RCA with enriched description")

        current = {
            "summary":     summary,
            "description": enriched_description,
        }

        result = generate_fresh_rca(current)

        confidence         = result.get("confidence", "LOW")
        needs_human_review = result.get("needs_human_review", confidence == "LOW")
        clarification      = result.get("clarification")
        affected           = result.get("affected_component", "Unknown")

        # ── Still LOW confidence after clarification — escalate to L3 ──
        if needs_human_review:
            print(f"🚨 [{issueKey}] Still LOW after clarification — flagging for L3 manual review")
            return {
                "root_cause":        "Insufficient information for automated RCA. Ticket has been flagged for L3 manual review.",
                "affected":          affected,
                "steps":             ["Escalate to L3 engineering team for manual root cause investigation."],
                "confidence":        "LOW",
                "confidence_label":  get_confidence_label("LOW"),
                "summary":           "🚨 Manual L3 review required — automated RCA could not determine root cause",
                "source":            "hitl_escalated",
                "needs_human_review": True,
                "clarification":     clarification,
                "cached":            False,
            }

        # ── Save the clarification-enriched RCA to DB ──
        await update_ticket_rca(
            issue_key          = issueKey,
            root_cause         = result.get("root_cause"),
            affected_component = affected,
            resolution_steps   = result.get("resolution_steps", []),
            confidence         = confidence,
            source             = "generated_with_clarification",
            matched_from       = None,
            matched_summary    = None,
        )
        print(f"💾 [{issueKey}] Clarification RCA saved (confidence: {confidence})")

        return {
            "root_cause":        result.get("root_cause"),
            "affected":          affected,
            "steps":             result.get("resolution_steps", []),
            "confidence":        confidence,
            "confidence_label":  get_confidence_label(confidence),
            "summary":           get_rca_summary(confidence, affected),
            "source":            "generated_with_clarification",
            "matched_from":      None,
            "matched_summary":   None,
            "needs_human_review": False,
            "clarification":     None,
            "cached":            False,
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"❌ submit_rca_clarification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ─────────────────────────────────────────────────────────────
# HUMAN RCA OVERRIDE — add this route to rca_routes.py
# Placed after the existing /rca/clarify route
# ─────────────────────────────────────────────────────────────

@router.post("/tickets/{issueKey}/rca/human")
async def submit_human_rca(issueKey: str, data: dict):
    """
    Called when a human intervener manually writes the root cause
    for a LOW-confidence ticket.

    Payload:
        {
            "root_cause":   "...",          # required — free-text entered by human
            "affected":     "...",          # optional — affected component
            "steps":        ["...", "..."]  # optional — resolution steps
        }

    Behaviour:
        1. Validates the ticket exists and is a parent ticket.
        2. Persists the human-written root cause to the tickets table
           with source = "human_override" and confidence = "HUMAN".
        3. Returns the saved RCA so the frontend can re-render immediately.
    """
    try:
        tickets = await get_all_tickets()
        ticket  = next((t for t in tickets if t["issue_key"] == issueKey), None)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {issueKey} not found")

        if ticket.get("parent_ticket_key"):
            raise HTTPException(
                status_code=400,
                detail="RCA override is only available on parent tickets"
            )

        root_cause = (data.get("root_cause") or "").strip()
        if not root_cause:
            raise HTTPException(status_code=422, detail="root_cause is required")

        affected = (data.get("affected") or ticket.get("rca_affected") or "Unknown").strip()
        steps    = data.get("steps") or ticket.get("rca_steps") or []

        await update_ticket_rca(
            issue_key          = issueKey,
            root_cause         = root_cause,
            affected_component = affected,
            resolution_steps   = steps,
            confidence         = "HUMAN",          # distinguishable from LOW/MEDIUM/HIGH
            source             = "human_override",
            matched_from       = None,
            matched_summary    = None,
        )

        print(f"✍️  [{issueKey}] Human RCA override saved")

        return {
            "root_cause":        root_cause,
            "affected":          affected,
            "steps":             steps,
            "confidence":        "HUMAN",
            "confidence_label":  "Human Verified — manually reviewed and confirmed",
            "summary":           f"✍️ Root cause written by human reviewer for: {affected}",
            "source":            "human_override",
            "matched_from":      None,
            "matched_summary":   None,
            "needs_human_review": False,
            "cached":            False,
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"❌ submit_human_rca error: {e}")
        raise HTTPException(status_code=500, detail=str(e))