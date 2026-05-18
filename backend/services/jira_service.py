# services/jira_service.py

import httpx
import re

from core.config import Config
from repositories.ticket_repository import get_all_tickets

auth = (Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)

headers = {
    "Accept":       "application/json",
    "Content-Type": "application/json"
}

BASE_URL = f"https://{Config.JIRA_DOMAIN}"


# ─────────────────────────────────────────────
# CREATE JIRA TICKET
# ─────────────────────────────────────────────

async def create_ticket(data, related=""):

    url = f"{BASE_URL}/rest/servicedeskapi/request"

    summary = getattr(data, "summary", None) or data.get("summary", "")
    description = getattr(data, "description", None) or data.get("description", "")

    urgency = getattr(data, "urgency", None) or data.get("urgency", "")
    impact = getattr(data, "impact", None) or data.get("impact", "")

    app_name = getattr(data, "app_name", None) or data.get("app_name", "")
    component_name = getattr(data, "component_name", None) or data.get("component_name", "")

    # Normalize urgency
    urgency_map = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low"
    }

    # Normalize impact to exact Jira labels
    impact_map = {
        "extensive": "Extensive / Widespread",
        "significant": "Significant / Large",
        "moderate": "Moderate / Limited",
        "minor": "Minor / Localized"
    }

    if urgency:
        urgency = urgency_map.get(
            urgency.lower().strip(),
            urgency
        )

    if impact:
        impact = impact_map.get(
            impact.lower().strip(),
            impact
        )

    # Format related issues properly
    related_text = (
        "\n".join(related)
        if isinstance(related, list)
        else related
    )

    request_fields = {

        "summary": summary,

        "description":
            f"{description}\n\n"
            f"Application: {app_name or 'General'}\n"
            f"Component: {component_name or 'General'}\n"
            f"Related:\n{related_text}"

    }

    # Add only when value exists
    if urgency:
        request_fields[Config.JIRA_URGENCY_FIELD] = {
            "value": urgency
        }

    if impact:
        request_fields[Config.JIRA_IMPACT_FIELD] = {
            "value": impact
        }

    payload = {
        "serviceDeskId": Config.SERVICE_DESK_ID,
        "requestTypeId": Config.REQUEST_TYPE_ID,
        "requestFieldValues": request_fields
    }

    try:

        print("🔥 JIRA PAYLOAD:")
        print(payload)

        async with httpx.AsyncClient(timeout=15) as client:

            res = await client.post(
                url,
                json=payload,
                headers=headers,
                auth=auth
            )

        if res.status_code not in [200, 201]:

            print("❌ Jira create error:")
            print(res.text)

            return None

        print("✅ Jira Ticket Created")

        return res.json()

    except Exception as e:

        print(
            "❌ Exception in create_ticket:",
            str(e)
        )

        return None
        
              
# ─────────────────────────────────────────────
# ADD RCA AS COMMENT ON JIRA TICKET
# Called after RCA is generated so the Jira
# ticket's comment thread contains the full
# root cause analysis for the support team.
# ─────────────────────────────────────────────
async def add_rca_comment(
    issue_key:         str,
    root_cause:        str,
    affected:          str,
    resolution_steps:  list,
    confidence:        str,
    source:            str        = "generated",
    matched_from:      str | None = None,
) -> bool:
    """
    Posts the RCA result as a rich-text comment on the Jira issue.
    Uses the Atlassian Document Format (ADF) so it renders nicely.
    """
    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/comment"

    # ── Build confidence badge text ──
    conf_emoji = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴", "HUMAN": "🔵"}.get(confidence, "⚪")
    source_label = {
        "generated":                  "AI Generated",
        "matched":                    f"Matched from past ticket: {matched_from or ''}",
        "knowledge_base":             f"Knowledge Base: {matched_from or ''}",
        "generated_with_clarification": "AI Generated (with clarification)",
        "human_override":             "Human Verified",
    }.get(source, source)

    # ── Build resolution steps as ADF list items ──
    step_items = [
        {
            "type": "listItem",
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": step}]
            }]
        }
        for step in (resolution_steps or [])
    ]

    # ── Full ADF comment body ──
    adf_body = {
        "type":    "doc",
        "version": 1,
        "content": [
            # Header
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "🔍 Copilot Root Cause Analysis"}]
            },
            # Confidence + source
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"{conf_emoji} Confidence: ", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": confidence},
                    {"type": "hardBreak"},
                    {"type": "text", "text": "Source: ",                   "marks": [{"type": "strong"}]},
                    {"type": "text", "text": source_label},
                ]
            },
            # Root cause
            {
                "type": "heading",
                "attrs": {"level": 4},
                "content": [{"type": "text", "text": "Root Cause"}]
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": root_cause or "–"}]
            },
            # Affected component
            {
                "type": "heading",
                "attrs": {"level": 4},
                "content": [{"type": "text", "text": "Affected Component"}]
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": affected or "–",
                              "marks": [{"type": "strong"}]}]
            },
            # Resolution steps
            {
                "type": "heading",
                "attrs": {"level": 4},
                "content": [{"type": "text", "text": "Resolution Steps"}]
            },
            *(
                [{
                    "type":    "orderedList",
                    "content": step_items
                }]
                if step_items
                else [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "No resolution steps generated."}]
                }]
            ),
            # Footer
            {
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": "— AMS Copilot RCA Engine",
                    "marks": [{"type": "em"}]
                }]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                url,
                json={"body": adf_body},
                headers=headers,
                auth=auth
            )

        if res.status_code not in [200, 201]:
            print(f"❌ add_rca_comment failed for {issue_key}: {res.text}")
            return False

        print(f"💬 [{issue_key}] RCA comment posted to Jira")
        return True

    except Exception as e:
        print(f"❌ add_rca_comment exception: {e}")
        return False



# ─────────────────────────────────────────────
# GENERIC JIRA COMMENT
# ─────────────────────────────────────────────
async def add_comment(
    issue_key: str,
    text: str
):

    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/comment"

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type":"paragraph",
                    "content":[
                        {
                            "type":"text",
                            "text": text
                        }
                    ]
                }
            ]
        }
    }

    try:

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                url,
                json=payload,
                headers=headers,
                auth=auth
            )

        if res.status_code not in [200,201]:
            print("❌ add_comment:",res.text)
            return False

        return True

    except Exception as e:
        print("❌ add_comment exception:",e)
        return False


# ─────────────────────────────────────────────
# LINK DUPLICATE COMMENTS
# Parent:
# Children: AMS-61, AMS-62, AMS-63
#
# Child:
# Parent: AMS-45
# ─────────────────────────────────────────────
async def link_duplicate_comments(
    parent_jira_id: str,
    child_jira_id: str
):

    try:

        comments_url = (
            f"{BASE_URL}/rest/api/3/issue/"
            f"{parent_jira_id}/comment"
        )

        async with httpx.AsyncClient(
            timeout=15
        ) as client:

            res = await client.get(
                comments_url,
                headers=headers,
                auth=auth
            )

        comments = []

        if res.status_code == 200:
            comments = res.json().get(
                "comments",
                []
            )

        parent_comment_id = None
        child_ids = []

        # find existing "Children:" comment
        for c in comments:

            body = c.get("body", {})
            content = body.get(
                "content",
                []
            )

            text = ""

            for item in content:

                for x in item.get(
                    "content",
                    []
                ):

                    text += x.get(
                        "text",
                        ""
                    )

            if text.startswith(
                "Children:"
            ):

                parent_comment_id = c["id"]

                existing = (
                    text.replace(
                        "Children:",
                        ""
                    )
                    .strip()
                )

                if existing:

                    child_ids = [
                        x.strip()
                        for x in existing.split(",")
                    ]

                break


        # avoid duplicate ids
        if child_jira_id not in child_ids:
            child_ids.append(
                child_jira_id
            )

        updated_text = (
            "Children: "
            + ", ".join(child_ids)
        )

        payload = {
            "body":{
                "type":"doc",
                "version":1,
                "content":[
                    {
                        "type":"paragraph",
                        "content":[
                            {
                                "type":"text",
                                "text":updated_text
                            }
                        ]
                    }
                ]
            }
        }

        # update existing comment
        if parent_comment_id:

            update_url = (
                f"{BASE_URL}/rest/api/3/issue/"
                f"{parent_jira_id}/comment/"
                f"{parent_comment_id}"
            )

            async with httpx.AsyncClient(
                timeout=15
            ) as client:

                await client.put(
                    update_url,
                    json=payload,
                    headers=headers,
                    auth=auth
                )

        else:

            async with httpx.AsyncClient(
                timeout=15
            ) as client:

                await client.post(
                    comments_url,
                    json=payload,
                    headers=headers,
                    auth=auth
                )

        # child comment
        await add_comment(
            child_jira_id,
            f"Parent: {parent_jira_id}"
        )

        return True

    except Exception as e:

        print(
            "❌ link_duplicate_comments:",
            e
        )

        return False

# ─────────────────────────────────────────────
# REMOVE PARENT ↔ CHILD COMMENT LINKS
# ─────────────────────────────────────────────
async def unlink_duplicate_comments(
    parent_jira_id: str,
    child_jira_id: str
):
    try:

        # -----------------------------
        # UPDATE PARENT COMMENT
        # -----------------------------
        comments_url = (
            f"{BASE_URL}/rest/api/3/issue/"
            f"{parent_jira_id}/comment"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(
                comments_url,
                headers=headers,
                auth=auth
            )

        if res.status_code == 200:

            comments = res.json().get(
                "comments",
                []
            )

            for c in comments:

                body = str(
                    c.get("body", "")
                )

                if "Children:" not in body:
                    continue

                comment_id = c["id"]

                import re

                ids = re.findall(
                    r"[A-Z]+-\d+",
                    body
                )

                ids = [
                    x for x in ids
                    if x != child_jira_id
                ]

                # no children left
                if not ids:

                    delete_url = (
                        f"{BASE_URL}/rest/api/3/issue/"
                        f"{parent_jira_id}/comment/"
                        f"{comment_id}"
                    )

                    async with httpx.AsyncClient(timeout=15) as client:
                        await client.delete(
                            delete_url,
                            headers=headers,
                            auth=auth
                        )

                else:

                    updated = (
                        "Children: "
                        + ", ".join(ids)
                    )

                    update_url = (
                        f"{BASE_URL}/rest/api/3/issue/"
                        f"{parent_jira_id}/comment/"
                        f"{comment_id}"
                    )

                    payload = {
                        "body":{
                            "type":"doc",
                            "version":1,
                            "content":[
                                {
                                    "type":"paragraph",
                                    "content":[
                                        {
                                            "type":"text",
                                            "text":updated
                                        }
                                    ]
                                }
                            ]
                        }
                    }

                    async with httpx.AsyncClient(timeout=15) as client:
                        await client.put(
                            update_url,
                            json=payload,
                            headers=headers,
                            auth=auth
                        )

                break


        # -----------------------------
        # REMOVE CHILD COMMENT
        # -----------------------------
        child_url = (
            f"{BASE_URL}/rest/api/3/issue/"
            f"{child_jira_id}/comment"
        )

        async with httpx.AsyncClient(timeout=15) as client:

            res = await client.get(
                child_url,
                headers=headers,
                auth=auth
            )

        if res.status_code == 200:

            comments = res.json().get(
                "comments",
                []
            )

            for c in comments:

                body = str(
                    c.get("body","")
                )

                if (
                    f"Parent: {parent_jira_id}"
                    in body
                ):

                    delete_url = (
                        f"{BASE_URL}/rest/api/3/issue/"
                        f"{child_jira_id}/comment/"
                        f"{c['id']}"
                    )

                    async with httpx.AsyncClient(timeout=15) as client:

                        await client.delete(
                            delete_url,
                            headers=headers,
                            auth=auth
                        )

                    break

        return True

    except Exception as e:

        print(
            "❌ unlink_duplicate_comments:",
            e
        )

        return False
    

# ─────────────────────────────────────────────
# GENERATE CHILD KEY
# ─────────────────────────────────────────────
async def generate_child_id(parent_key: str):

    tickets = await get_all_tickets()
    pattern = re.compile(rf"^{re.escape(parent_key)}\.(\d+)$")
    max_num = 0

    for t in tickets:
        child_key = t.get("child_key") or ""
        if child_key.count(".") > 1:
            continue
        match = pattern.match(child_key)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    return f"{parent_key}.{max_num + 1}"



# ─────────────────────────────────────────────
# MOVE ALL CHILD COMMENT LINKS TO NEW PARENT
# ─────────────────────────────────────────────
async def migrate_merge_comments(
    old_parent: str,
    new_parent: str,
    moved_ids: list[str]
):
    try:

        # remove old links
        for ticket_id in moved_ids:

            await unlink_duplicate_comments(
                old_parent,
                ticket_id
            )

        # add new links
        for ticket_id in moved_ids:

            await link_duplicate_comments(
                new_parent,
                ticket_id
            )

        return True

    except Exception as e:

        print(
            "❌ migrate_merge_comments:",
            e
        )

        return False
    

# ─────────────────────────────────────────────
# DELETE SINGLE JIRA TICKET
# ─────────────────────────────────────────────
async def delete_jira_ticket(issue_key: str):

    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.delete(url, headers=headers, auth=auth)

        if res.status_code not in [200, 204]:
            print(f"❌ Jira delete failed {issue_key}:", res.text)
            return False

        print(f"🗑 Jira ticket deleted: {issue_key}")
        return True

    except Exception as e:
        print("❌ delete_jira_ticket exception:", str(e))
        return False


# ─────────────────────────────────────────────
# UPDATE SINGLE JIRA ISSUE STATUS
# ─────────────────────────────────────────────
async def update_jira_status(issue_key: str):

    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/transitions"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(url, headers=headers, auth=auth)

        if res.status_code != 200:
            print(f"❌ Failed to fetch transitions for {issue_key}:", res.text)
            return False

        transitions   = res.json().get("transitions", [])
        transition_id = None

        for t in transitions:
            name = t.get("name", "").lower()
            if any(k in name for k in ["done", "complete", "resolve", "close"]):
                transition_id = t.get("id")
                break

        if not transition_id:
            print(f"❌ No suitable transition found for {issue_key}")
            return False

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                url,
                json={"transition": {"id": transition_id}},
                headers=headers,
                auth=auth
            )

        if res.status_code not in [200, 204]:
            print(f"❌ Jira status update failed for {issue_key}:", res.text)
            return False

        print(f"✅ Jira ticket completed: {issue_key}")
        return True

    except Exception as e:
        print("❌ update_jira_status exception:", str(e))
        return False


# ─────────────────────────────────────────────
# GET ALL RELATED TICKETS
# ─────────────────────────────────────────────
async def get_related_tickets(parent_key: str):

    tickets = await get_all_tickets()

    return [
        t for t in tickets
        if t.get("issue_key") == parent_key
        or t.get("parent_ticket_key") == parent_key
    ]


# ─────────────────────────────────────────────
# COMPLETE PARENT + ALL CHILD JIRA TICKETS
# ─────────────────────────────────────────────
async def complete_parent_and_children(parent_key: str):

    try:
        related_tickets = await get_related_tickets(parent_key)

        if not related_tickets:
            print(f"⚠️ No related tickets found for {parent_key}")
            return False

        success = True
        for t in related_tickets:
            jira_issue_key = t.get("issue_key")
            if not jira_issue_key:
                continue
            if not await update_jira_status(jira_issue_key):
                success = False

        return success

    except Exception as e:
        print("❌ complete_parent_and_children exception:", str(e))
        return False


# ─────────────────────────────────────────────
# DELETE PARENT + ALL CHILD JIRA TICKETS
# ─────────────────────────────────────────────
async def delete_parent_and_children(parent_key: str):

    try:
        related_tickets = await get_related_tickets(parent_key)

        if not related_tickets:
            print(f"⚠️ No related tickets found for {parent_key}")
            return False

        children = [t for t in related_tickets if t.get("parent_ticket_key") == parent_key]
        parent   = [t for t in related_tickets if t.get("issue_key") == parent_key]
        ordered  = children + parent

        success = True
        for t in ordered:
            jira_issue_key = t.get("issue_key")
            if not jira_issue_key:
                continue
            if not await delete_jira_ticket(jira_issue_key):
                success = False

        return success

    except Exception as e:
        print("❌ delete_parent_and_children exception:", str(e))
        return False