from repositories.ticket_repository import supabase

async def log_event(
    ticket_id: str,
    event: str,
    actor: str = "system",
    details: str = "",
    metadata: dict = None
):
    try:

        payload = {
            "ticket_id": ticket_id,
            "event": event,
            "actor": actor,
            "details": details,
            "metadata": metadata or {}
        }

        supabase.table(
            "ticket_events"
        ).insert(payload).execute()

    except Exception as e:
        print("❌ log_event:", e)


async def get_ticket_events(ticket_id: str):

    try:

        result = (
            supabase.table("ticket_events")
            .select("*")
            .eq("ticket_id", ticket_id)
            .order(
                "created_at",
                desc=False
            )
            .execute()
        )

        return result.data or []

    except Exception as e:

        print(
            "❌ get_ticket_events:",
            e
        )

        return []