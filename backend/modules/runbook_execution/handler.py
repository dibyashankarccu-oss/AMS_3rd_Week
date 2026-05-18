# modules/runbook_execution/handler.py

from modules.runbook_execution.agent import RunbookAgent


async def handle_runbook_flow(state: dict) -> dict:
    try:
        summary     = state.get("summary", "")

        # Try top-level first (set explicitly by router),
        # fall back to nested data dict for safety
        description = state.get("description", "")
        if not description:
            raw_data = state.get("data")
            if isinstance(raw_data, dict):
                description = raw_data.get("description", "")
            elif hasattr(raw_data, "description"):
                description = raw_data.description or ""

        if not summary:
            return {
                **state,
                "type":    "error",
                "message": "Runbook module: ticket summary is empty",
            }

        if not description:
            return {
                **state,
                "type":    "error",
                "message": "Runbook module: ticket description is empty",
            }

        agent  = RunbookAgent()
        result = await agent.run(
            summary=summary,
            description=description,
            state=state,
        )

        return {
            **state,
            "runbook_title":           result.get("runbook_title"),
            "runbook_category":        result.get("runbook_category"),
            "paired_steps":            result.get("paired_steps", []),
            "match_type":              result.get("match_type", "ai_fallback"),
            "type":                    state.get("type") or "runbook_executed",
            "message":                 result.get("message", "Runbook execution complete"),
        }

    except Exception as e:
        print(f"❌ handle_runbook_flow error: {e}")
        return {
            **state,
            "type":    "error",
            "message": f"Runbook module failed: {str(e)}",
        }