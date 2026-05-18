# modules/copilot_rca/handler.py

from modules.copilot_rca.agent import generate_fresh_rca
from modules.copilot_rca.service import get_confidence_label, get_rca_summary
from repositories.ticket_repository import update_ticket_rca


async def handle_rca_flow(state: dict) -> dict:
    try:
        print("RCA STATE:", state)
        issue_key   = state.get("id")
        summary     = state.get("summary", "")
        description = ""

        raw_data = state.get("data")
        if raw_data:
            if hasattr(raw_data, "description"):
                description = raw_data.description or ""
            elif isinstance(raw_data, dict):
                description = raw_data.get("description", "")

        if not summary:
            return {**state, "type": "error", "message": "RCA module: ticket summary is empty"}

        if not description:
            return {**state, "type": "error", "message": "RCA module: ticket description is empty"}

        result = generate_fresh_rca({"summary": summary, "description": description})

        confidence = result.get("confidence", "LOW")
        affected   = result.get("affected_component", "Unknown")

        # ── Save RCA to Supabase tickets table ──
        if issue_key:
            saved = await update_ticket_rca(
                issue_key          = issue_key,
                root_cause         = result.get("root_cause", ""),
                affected_component = affected,
                resolution_steps   = result.get("resolution_steps", []),
                confidence         = confidence,
                source             = "generated",
                matched_from       = None,
                matched_summary    = None,
            )
            if saved:
                print(f"💾 [{issue_key}] RCA saved to Supabase (confidence: {confidence})")
            else:
                print(f"⚠️  [{issue_key}] RCA generated but DB save failed")
        else:
            print("⚠️  handle_rca_flow: no issue_key in state — RCA not saved")

        return {
            **state,
            "type":                 "rca_complete",
            "message":              result.get("root_cause", ""),
            "rca_root_cause":       result.get("root_cause", ""),
            "rca_affected":         affected,
            "rca_steps":            result.get("resolution_steps", []),
            "rca_confidence":       confidence,
            "rca_confidence_label": get_confidence_label(confidence),
            "rca_summary":          get_rca_summary(confidence, affected),
        }

    except Exception as e:
        print(f"❌ handle_rca_flow error: {e}")
        return {**state, "type": "error", "message": f"RCA module failed: {str(e)}"}