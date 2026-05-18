# services/merge_service.py

from repositories.ticket_repository import (
    get_all_tickets,
    get_children,
    supabase
)

from services.jira_service import (
    complete_parent_and_children,
    unlink_duplicate_comments,
    link_duplicate_comments
)


# ─────────────────────────────────────────────
# MARK DUPLICATE
# ─────────────────────────────────────────────
async def mark_duplicate(issue_key: str):

    try:

        supabase.table("tickets").update({
            "is_duplicate": True
        }).eq("issue_key", issue_key).execute()

        return True

    except Exception as e:

        print(
            "❌ mark_duplicate error:",
            str(e)
        )

        return False


# ─────────────────────────────────────────────
# GET NEXT CHILD NUMBER
# Example:
# TP-650.1
# TP-650.2
# → returns 3
# ─────────────────────────────────────────────
async def get_next_child_number(parent_key: str):

    try:

        res = (
            supabase.table("tickets")
            .select("child_key")
            .eq("parent_ticket_key", parent_key)
            .not_.is_("child_key", "null")
            .execute()
        )

        rows = res.data or []

        max_num = 0

        for row in rows:

            child_key = row.get("child_key")

            if not child_key:
                continue

            try:

                num = int(
                    child_key.split(".")[-1]
                )

                if num > max_num:
                    max_num = num

            except:
                pass

        return max_num + 1

    except Exception as e:

        print(
            "❌ get_next_child_number error:",
            str(e)
        )

        return 1


# ─────────────────────────────────────────────
# MERGE TICKETS
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# MERGE TICKETS
# ─────────────────────────────────────────────
async def merge_tickets(
    target_parent: str,
    source_parents: list
):

    try:

        tickets = await get_all_tickets()

        if not tickets:

            return {
                "success": False,
                "message": "No tickets found"
            }

        # remove duplicates
        source_parents = list(
            set(source_parents)
        )

        # remove self merge
        source_parents = [
            s for s in source_parents
            if s != target_parent
        ]

        # find target ticket
        target_ticket = next(
            (
                t for t in tickets
                if t["issue_key"] == target_parent
            ),
            None
        )

        if not target_ticket:

            return {
                "success": False,
                "message": "Target not found"
            }

        # preserve completed state
        force_completed = (
            target_ticket.get("status")
            == "Completed"
        )

        moved = 0

        # ─────────────────────────────
        # MERGE SOURCE PARENTS
        # ─────────────────────────────
        for source in source_parents:

            source_ticket = next(
                (
                    t for t in tickets
                    if t["issue_key"] == source
                ),
                None
            )

            if not source_ticket:
                continue


            # source parent itself
            # + all its children
            source_children = [
                t for t in tickets
                if (
                    t["issue_key"] == source
                    or t.get("parent_ticket_key") == source
                )
            ]


            # ─────────────────────────
            # MOVE EACH TICKET
            # ─────────────────────────
            for t in source_children:

                issue_key = t["issue_key"]

                if issue_key == target_parent:
                    continue


                # remove old Jira links
                # skip source itself because
                # it was parent before
                if issue_key != source:

                    await unlink_duplicate_comments(
                        source,
                        issue_key
                    )


                next_num = await get_next_child_number(
                    target_parent
                )

                update_payload = {

                    "parent_ticket_key":
                        target_parent,

                    "child_key":
                        f"{target_parent}.{next_num}",

                    "is_duplicate": True
                }


                if force_completed:

                    update_payload[
                        "status"
                    ] = "Completed"


                # DB UPDATE
                supabase.table(
                    "tickets"
                ).update(
                    update_payload
                ).eq(
                    "issue_key",
                    issue_key
                ).execute()


                # create new Jira links
                await link_duplicate_comments(
                    target_parent,
                    issue_key
                )

                moved += 1

                print(
                    f"✅ Merged {issue_key}"
                    f" → "
                    f"{target_parent}.{next_num}"
                )


        # ─────────────────────────────
        # JIRA STATUS SYNC
        # ─────────────────────────────
        if force_completed:

            jira_result = (
                await complete_parent_and_children(
                    target_parent
                )
            )

            print(
                "🔥 Jira sync result:",
                jira_result
            )


        # ─────────────────────────────
        # FINAL RESPONSE
        # ─────────────────────────────
        return {

            "success": True,

            "target": target_parent,

            "sources": source_parents,

            "moved": moved,

            "status_sync":
                force_completed,

            "jira_synced":
                force_completed
        }

    except Exception as e:

        print(
            "❌ merge_tickets error:",
            str(e)
        )

        return {

            "success": False,

            "message": str(e)
        }   


