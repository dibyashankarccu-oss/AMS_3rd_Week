# modules/copilot_rca/agent.py

import os
import json
import re

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from .prompt import (
    GENERATE_PROMPT,
    SAME_ISSUE_PROMPT,
    KB_MATCH_PROMPT,
    HITL_CLARIFICATION_PROMPT,
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME   = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in environment")

llm = ChatGroq(api_key=GROQ_API_KEY, model_name=MODEL_NAME)


# ─────────────────────────────────────────────
# CLEAN LLM OUTPUT
# ─────────────────────────────────────────────
def _clean_llm_output(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$",          "", raw).strip()
    return raw


# ─────────────────────────────────────────────
# IS SAME ISSUE (past ticket comparison)
# ─────────────────────────────────────────────
def is_same_issue(current: dict, past: dict) -> tuple[bool, str]:
    """
    LLM decides if current incident is the same type as a past resolved ticket.
    Returns (is_same: bool, confidence: str)
    """
    prompt = SAME_ISSUE_PROMPT.format(
        summary          = current.get("summary", ""),
        description      = current.get("description", ""),
        past_summary     = past.get("summary", ""),
        past_description = past.get("description", ""),
        past_root_cause  = past.get("rca_root_cause", ""),
        past_affected    = past.get("rca_affected", ""),
    )

    try:
        response = llm.invoke(prompt)
        raw      = _clean_llm_output(response.content)
        result   = json.loads(raw)

        same       = bool(result.get("is_same_issue", False))
        confidence = str(result.get("confidence", "LOW")).upper()
        reason     = result.get("reason", "")

        print(f"[RCAAgent] Same issue check: {same} | Confidence: {confidence} | Reason: {reason}")
        return same, confidence

    except Exception as e:
        print(f"[RCAAgent] is_same_issue failed: {e}")
        return False, "LOW"


# ─────────────────────────────────────────────
# IS KB APPLICABLE (knowledge base match)
# ─────────────────────────────────────────────
def is_kb_applicable(current: dict, kb_entry: dict) -> tuple[bool, str]:
    """
    LLM verifies if a KB entry is truly applicable to the current incident.
    Returns (is_applicable: bool, confidence: str)
    """
    prompt = KB_MATCH_PROMPT.format(
        summary      = current.get("summary", ""),
        description  = current.get("description", ""),
        kb_title     = kb_entry.get("title", ""),
        kb_symptoms  = kb_entry.get("symptoms", ""),
        kb_root_cause= kb_entry.get("root_cause", ""),
        kb_affected  = kb_entry.get("affected_component", ""),
    )

    try:
        response = llm.invoke(prompt)
        raw      = _clean_llm_output(response.content)
        result   = json.loads(raw)

        applicable = bool(result.get("is_applicable", False))
        confidence = str(result.get("confidence", "LOW")).upper()
        reason     = result.get("reason", "")

        print(f"[RCAAgent] KB match check: {applicable} | Confidence: {confidence} | Reason: {reason}")
        return applicable, confidence

    except Exception as e:
        print(f"[RCAAgent] is_kb_applicable failed: {e}")
        return False, "LOW"


# ─────────────────────────────────────────────
# GENERATE CLARIFICATION QUESTIONS (HITL)
# ─────────────────────────────────────────────
def generate_clarification_questions(current: dict) -> dict:
    """
    When confidence is LOW, generate diagnostic questions to ask the submitter.
    Returns {questions: [...], hint: str}
    """
    prompt = HITL_CLARIFICATION_PROMPT.format(
        summary     = current.get("summary", ""),
        description = current.get("description", ""),
    )

    try:
        response = llm.invoke(prompt)
        raw      = _clean_llm_output(response.content)
        result   = json.loads(raw)

        questions = result.get("questions", [])
        hint      = result.get("hint", "")

        print(f"[RCAAgent] Generated {len(questions)} HITL clarification questions")
        return {
            "questions": questions,
            "hint":      hint,
        }

    except Exception as e:
        print(f"[RCAAgent] generate_clarification_questions failed: {e}")
        return {
            "questions": [
                "What exact error message or error code are you seeing?",
                "When did this issue first occur and did anything change before it started?",
                "Which specific systems or services are affected?",
                "Have you tried any troubleshooting steps already? If so, what were the results?",
            ],
            "hint": "Error messages and timeline are the most critical details needed.",
        }


# ─────────────────────────────────────────────
# GENERATE FRESH RCA
# ─────────────────────────────────────────────
def generate_fresh_rca(current: dict) -> dict:
    """
    LLM generates a detailed, point-by-point RCA when no KB match or past
    ticket match exists. Includes HITL flag if confidence is LOW.
    """
    prompt = GENERATE_PROMPT.format(
        summary     = current.get("summary", ""),
        description = current.get("description", ""),
    )

    try:
        response = llm.invoke(prompt)
        raw      = _clean_llm_output(response.content)
        result   = json.loads(raw)

        required = ("root_cause", "affected_component", "resolution_steps", "confidence")
        if not all(k in result for k in required):
            raise ValueError("Missing required keys in LLM response")

        confidence = str(result["confidence"]).upper().strip()
        if confidence not in ("HIGH", "MEDIUM", "LOW"):
            confidence = "LOW"

        resolution_steps = result["resolution_steps"]
        if not isinstance(resolution_steps, list) or not resolution_steps:
            resolution_steps = ["Manual review required — LLM returned no resolution steps."]

        # ── HITL: if LOW confidence, generate clarification questions ──
        needs_human_review = result.get("needs_human_review", confidence == "LOW")
        clarification      = None

        if needs_human_review:
            print(f"[RCAAgent] LOW confidence — triggering HITL clarification questions")
            clarification = generate_clarification_questions(current)

        return {
            "status":              "success",
            "root_cause":          str(result["root_cause"]).strip(),
            "affected_component":  str(result["affected_component"]).strip(),
            "resolution_steps":    resolution_steps,
            "confidence":          confidence,
            "needs_human_review":  needs_human_review,
            "clarification":       clarification,
        }

    except Exception as e:
        print(f"[RCAAgent] generate_fresh_rca failed: {e}")

        # Even on failure, try to generate HITL questions
        clarification = None
        try:
            clarification = generate_clarification_questions(current)
        except Exception:
            pass

        return {
            "status":              "error",
            "root_cause":          f"RCA generation failed: {str(e)[:80]}. Manual review required.",
            "affected_component":  "Unknown — please provide more details",
            "resolution_steps":    ["Provide a detailed incident description and resubmit for RCA."],
            "confidence":          "LOW",
            "needs_human_review":  True,
            "clarification":       clarification,
        }