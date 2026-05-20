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


def _clean(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$",          "", raw).strip()
    return raw


def is_same_issue(current: dict, past: dict) -> tuple[bool, str]:
    prompt = SAME_ISSUE_PROMPT.format(
        summary          = current.get("summary", ""),
        description      = current.get("description", ""),
        past_summary     = past.get("summary", ""),
        past_description = past.get("description", ""),
        past_root_cause  = past.get("rca_root_cause", ""),
        past_affected    = past.get("rca_affected", ""),
    )
    try:
        result = json.loads(_clean(llm.invoke(prompt).content))
        same   = bool(result.get("is_same_issue", False))
        conf   = str(result.get("confidence", "LOW")).upper()
        print(f"[RCAAgent] Same issue: {same} | {conf} | {result.get('reason','')}")
        return same, conf
    except Exception as e:
        print(f"[RCAAgent] is_same_issue failed: {e}")
        return False, "LOW"


def is_kb_applicable(current: dict, kb_entry: dict) -> tuple[bool, str]:
    prompt = KB_MATCH_PROMPT.format(
        summary       = current.get("summary", ""),
        description   = current.get("description", ""),
        kb_title      = kb_entry.get("title", ""),
        kb_symptoms   = kb_entry.get("symptoms", ""),
        kb_root_cause = kb_entry.get("root_cause", ""),
        kb_affected   = kb_entry.get("affected_component", ""),
    )
    try:
        result     = json.loads(_clean(llm.invoke(prompt).content))
        applicable = bool(result.get("is_applicable", False))
        conf       = str(result.get("confidence", "LOW")).upper()
        print(f"[RCAAgent] KB applicable: {applicable} | {conf} | {result.get('reason','')}")
        return applicable, conf
    except Exception as e:
        print(f"[RCAAgent] is_kb_applicable failed: {e}")
        return False, "LOW"


def generate_clarification_questions(current: dict) -> dict:
    prompt = HITL_CLARIFICATION_PROMPT.format(
        summary     = current.get("summary", ""),
        description = current.get("description", ""),
    )
    try:
        result = json.loads(_clean(llm.invoke(prompt).content))
        print(f"[RCAAgent] Generated {len(result.get('questions', []))} HITL questions")
        return {"questions": result.get("questions", []), "hint": result.get("hint", "")}
    except Exception as e:
        print(f"[RCAAgent] generate_clarification_questions failed: {e}")
        return {
            "questions": [
                "What exact error message or error code are you seeing?",
                "When did this issue first occur and did anything change before it started?",
                "Which specific systems or services are affected?",
                "Have you tried any troubleshooting steps? If so, what were the results?",
            ],
            "hint": "Error messages and timeline are most critical for diagnosis.",
        }


def generate_fresh_rca(current: dict) -> dict:
    """
    Two-layer RCA: technical_cause + systemic_cause.
    Combines into root_cause string with section headers for
    storage in Supabase and display in Jira / frontend.
    No resolution_steps — handled by SOP module.
    """
    prompt = GENERATE_PROMPT.format(
        summary     = current.get("summary", ""),
        description = current.get("description", ""),
    )
    try:
        result = json.loads(_clean(llm.invoke(prompt).content))

        required = ("technical_cause", "systemic_cause", "affected_component", "confidence")
        if not all(k in result for k in required):
            raise ValueError(f"Missing required keys. Got: {list(result.keys())}")

        confidence = str(result["confidence"]).upper().strip()
        if confidence not in ("HIGH", "MEDIUM", "LOW"):
            confidence = "LOW"

        technical = str(result["technical_cause"]).strip()
        systemic  = str(result["systemic_cause"]).strip()

        root_cause = (
            f"TECHNICAL CAUSE:\n{technical}\n\n"
            f"SYSTEMIC CAUSE:\n{systemic}"
        )

        needs_human_review = result.get("needs_human_review", confidence == "LOW")
        clarification      = generate_clarification_questions(current) if needs_human_review else None

        return {
            "status":             "success",
            "root_cause":         root_cause,
            "technical_cause":    technical,
            "systemic_cause":     systemic,
            "affected_component": str(result["affected_component"]).strip(),
            "confidence":         confidence,
            "needs_human_review": needs_human_review,
            "clarification":      clarification,
        }

    except Exception as e:
        print(f"[RCAAgent] generate_fresh_rca failed: {e}")
        clarification = None
        try:
            clarification = generate_clarification_questions(current)
        except Exception:
            pass
        return {
            "status":             "error",
            "root_cause":         f"RCA generation failed: {str(e)[:80]}. Manual review required.",
            "technical_cause":    "",
            "systemic_cause":     "",
            "affected_component": "Unknown — please provide more details",
            "confidence":         "LOW",
            "needs_human_review": True,
            "clarification":      clarification,
        }