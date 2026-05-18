# modules/runbook_execution/service.py

from services.embedding_service import get_embedding
from repositories.runbook_repository import search_runbooks_by_vector
from core.constants import RUNBOOK_SIMILARITY_THRESHOLD


# ─────────────────────────────────────────────────────────────
# RUNBOOK SEARCH (VECTOR)
# ─────────────────────────────────────────────────────────────
async def fetch_best_runbook(summary: str, description: str) -> dict | None:
    try:
        query = f"{summary} {description}".strip()
        if not query:
            return None

        query_embedding = await get_embedding(query)
        if not query_embedding:
            return None

        query_embedding = [float(x) for x in query_embedding]
        results = await search_runbooks_by_vector(query_embedding, top_k=1)

        if not results:
            return None

        best = results[0]
        similarity = best.get("similarity", 0)

        if similarity < RUNBOOK_SIMILARITY_THRESHOLD:
            print(
                f"⚠️  Runbook '{best.get('title')}' rejected — "
                f"similarity {similarity:.2f} below threshold {RUNBOOK_SIMILARITY_THRESHOLD}"
            )
            return None

        print(f"✅ Runbook matched: '{best.get('title')}' (similarity: {similarity:.2f})")
        return best

    except Exception as e:
        print(f"❌ fetch_best_runbook error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# OUTPUT PARSER  ← updated: pairs each STEP with its CMD
# Returns list of { "step": str, "cmd": str | None }
# ─────────────────────────────────────────────────────────────
def parse_llm_output(raw: str) -> list[dict]:
    """
    Parses LLM output into a list of paired step+command dicts.

    Input example:
        STEP: Check DB service status
        CMD: systemctl status postgresql
        STEP: Review recent logs
        STEP: Restart service if required
        CMD: systemctl restart postgresql

    Output:
        [
          {"step": "Check DB service status", "cmd": "systemctl status postgresql"},
          {"step": "Review recent logs",       "cmd": None},
          {"step": "Restart service if required", "cmd": "systemctl restart postgresql"},
        ]
    """
    paired = []
    lines  = [l.strip() for l in raw.splitlines() if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.upper().startswith("STEP:"):
            step_text = line[5:].strip()
            cmd_text  = None

            # Check if VERY NEXT line is a CMD
            if i + 1 < len(lines) and lines[i + 1].upper().startswith("CMD:"):
                raw_cmd  = lines[i + 1][4:].strip()
                cmd_text = raw_cmd if raw_cmd.upper() != "N/A" else None
                i += 1  # consume the CMD line

            if step_text:
                paired.append({"step": step_text, "cmd": cmd_text})

        i += 1

    # Graceful fallback if LLM returned plain text
    if not paired and raw.strip():
        paired = [{"step": raw.strip(), "cmd": None}]

    return paired


# ─────────────────────────────────────────────────────────────
# SAFETY FILTER  ← now works on paired list
# ─────────────────────────────────────────────────────────────
_DANGEROUS_PATTERNS = [
    "rm -rf", "drop table", "drop database", "delete from",
    "kill -9", "truncate", "chmod 777", ":(){:|:&};:", "mkfs", "dd if=",
]

def filter_safe_commands(paired: list[dict]) -> list[dict]:
    """
    Nullifies cmd on any step whose command matches a dangerous pattern.
    Step itself is always kept.
    """
    safe = []
    for item in paired:
        cmd = item.get("cmd")
        if cmd and any(pattern in cmd.lower() for pattern in _DANGEROUS_PATTERNS):
            print(f"⚠️  Unsafe command blocked: {cmd}")
            safe.append({"step": item["step"], "cmd": None})
        else:
            safe.append(item)
    return safe