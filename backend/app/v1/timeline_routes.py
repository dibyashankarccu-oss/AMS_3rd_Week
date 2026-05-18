from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, timedelta

from repositories.ticket_event_repository import get_ticket_events

router = APIRouter()

IST = timezone(timedelta(hours=5, minutes=30))


def utc_to_ist(utc_str: str):
    """
    Convert UTC timestamp (ISO format) to IST.
    """
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        return dt.astimezone(IST).isoformat()
    except Exception:
        return utc_str  # fallback if parsing fails


@router.get("/tickets/{ticket_id}/timeline")
async def get_ticket_timeline(ticket_id: str):

    try:
        events = await get_ticket_events(ticket_id)

        if not events:
            return {
                "ticket_id": ticket_id,
                "events": []
            }

        # Convert timestamps to IST for UI
        for event in events:
            if event.get("created_at"):
                event["created_at_ist"] = utc_to_ist(event["created_at"])

        return {
            "ticket_id": ticket_id,
            "events": events
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch timeline: {str(e)}"
        )