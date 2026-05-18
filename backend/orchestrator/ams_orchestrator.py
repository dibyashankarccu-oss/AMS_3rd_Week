from modules.duplicate_detection.handler import handle_duplicate_flow
from modules.copilot_rca.handler import handle_rca_flow
from modules.runbook_execution.handler import handle_runbook_flow
from repositories.ticket_event_repository import log_event


async def handle_ticket(data):

    state = {
        "data": data,
        "timeline_started": True,
        "summary": getattr(data, "summary", "") if data else "",
        "issue_key": getattr(data, "issue_key", None),
        
        "type": None,
        "id": None,
        "message": None,
        "is_duplicate": False,

        "rca_root_cause": None,
        "rca_affected": None,
        "rca_steps": [],
        "rca_confidence": None,
        "rca_confidence_label": None,
        "rca_summary": None,
    }

    try:
        # -------------------------------------------------
        # STEP 0: DUPLICATE CHECK
        # -------------------------------------------------
        state = await safe_run_module(handle_duplicate_flow, state)

        ticket_id = state.get("id") or state.get("issue_key")

        # -------------------------------------------------
        # INIT LOGS
        # -------------------------------------------------
        if ticket_id:
            await log_event(
                ticket_id=ticket_id,
                event="TICKET_SUBMITTED",
                actor="user",
                details=state.get("summary", "")
            )

            await log_event(
                ticket_id=ticket_id,
                event="DUPLICATE_DETECTION_COMPLETED"
            )

        if not state.get("summary") and state.get("data"):
            data_obj = state["data"]
            state["summary"] = getattr(data_obj, "summary", "")

        # -------------------------------------------------
        # EXIT IF DUPLICATE
        # -------------------------------------------------
        if state.get("is_duplicate"):
            if ticket_id:
                await log_event(
                    ticket_id=ticket_id,
                    event="DUPLICATE_DETECTED"
                )

            return normalize_response(state)

        
        # -------------------------------------------------
        # RCA GENERATION
        # -------------------------------------------------
        state = await safe_run_module(handle_rca_flow, state)

        ticket_id = state.get("id") or state.get("issue_key")

        # =================================================
        # SINGLE RCA LOG (ONLY ONCE PER TICKET)
        # =================================================
        if ticket_id:
            try:
                await log_event(
                    ticket_id=ticket_id,
                    event="RCA_GENERATED",
                    actor="system",
                    details=f"confidence={state.get('rca_confidence')}"
                )
            except Exception as e:
                print(f"⚠️ RCA log_event failed: {e}")
        
         # -------------------------------------------------
        # SOP EXECUTION
        # -------------------------------------------------
        state = await safe_run_module(handle_runbook_flow, state)

        ticket_id = state.get("id") or state.get("issue_key")

        # =================================================
        # SINGLE SOP LOG (ONLY ONCE PER TICKET)
        # =================================================
        if ticket_id:
            try:
                await log_event(
                    ticket_id=ticket_id,
                    event="SOP_EXECUTED",
                    actor="system",
                    details=f"resolution steps generated"
                )
            except Exception as e:
                print(f"⚠️ SOP log_event failed: {e}")

        # -------------------------------------------------
        # RETURN FINAL RESPONSE
        # -------------------------------------------------
        return normalize_response(state)

    except Exception as e:
        return {
            "type": "error",
            "message": f"Orchestrator failed: {str(e)}"
        }


async def safe_run_module(module_fn, state: dict):
    try:
        result = await module_fn(state)

        if not isinstance(result, dict):
            return {
                **state,
                "type": "error",
                "message": "Module returned invalid state"
            }

        state.update(result)
        return state

    except Exception as e:
        return {
            **state,
            "type": "error",
            "message": f"Module failed: {str(e)}"
        }


def normalize_response(state: dict):
    return {
        "type": state.get("type", "success"),
        "id": state.get("id"),
        "message": state.get("message"),

        "rca": {
            "root_cause": state.get("rca_root_cause"),
            "affected": state.get("rca_affected"),
            "steps": state.get("rca_steps", []),
            "confidence": state.get("rca_confidence"),
            "confidence_label": state.get("rca_confidence_label"),
            "summary": state.get("rca_summary"),
        } if state.get("rca_root_cause") else None,
    }