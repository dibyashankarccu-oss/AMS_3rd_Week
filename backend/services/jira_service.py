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

    summary        = getattr(data, "summary",        None) or data.get("summary",        "")
    description    = getattr(data, "description",    None) or data.get("description",    "")
    urgency        = getattr(data, "urgency",         None) or data.get("urgency",         "")
    impact         = getattr(data, "impact",          None) or data.get("impact",          "")
    app_name       = getattr(data, "app_name",        None) or data.get("app_name",        "") or "General"
    component_name = getattr(data, "component_name",  None) or data.get("component_name",  "") or "General"

    urgency_map = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
    impact_map  = {
        "extensive":   "Extensive / Widespread",
        "significant": "Significant / Large",
        "moderate":    "Moderate / Limited",
        "minor":       "Minor / Localized"
    }

    if urgency:
        urgency = urgency_map.get(urgency.lower().strip(), urgency)
    if impact:
        impact  = impact_map.get(impact.lower().strip(), impact)

    related_text = "\n".join(related) if isinstance(related, list) else related

    request_fields = {
        "summary": summary,
        "description": (
            f"{description}\n\n"
            f"Application: {app_name or 'General'}\n"
            f"Component: {component_name or 'General'}\n"
            f"Related:\n{related_text}"
        )
    }

    if urgency:
        request_fields[Config.JIRA_URGENCY_FIELD] = {"value": urgency}
    if impact:
        request_fields[Config.JIRA_IMPACT_FIELD]  = {"value": impact}

    payload = {
        "serviceDeskId":     Config.SERVICE_DESK_ID,
        "requestTypeId":     Config.REQUEST_TYPE_ID,
        "requestFieldValues": request_fields
    }

    try:
        print("🔥 JIRA PAYLOAD:", payload)
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(url, json=payload, headers=headers, auth=auth)

        if res.status_code not in [200, 201]:
            print("❌ Jira create error:", res.text)
            return None

        print("✅ Jira Ticket Created")
        return res.json()

    except Exception as e:
        print("❌ Exception in create_ticket:", str(e))
        return None


# ─────────────────────────────────────────────
# ADD RCA AS JIRA COMMENT
# ITIL Problem Management format:
#   🔧 Technical Cause  (engineering team)
#   📊 Systemic Cause   (problem management team)
# Resolution steps removed — covered by SOP module.
# ─────────────────────────────────────────────
async def add_rca_comment(
    issue_key:  str,
    root_cause: str,
    affected:   str,
    confidence: str,
    source:     str = "generated",
) -> bool:

    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/comment"

    conf_emoji = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴", "HUMAN": "🔵"}.get(confidence, "⚪")

    source_label = {
        "generated":                    "AI Generated — Fresh Analysis",
        "matched":                      "Matched from Past Resolved Ticket",
        "knowledge_base":               "Confluence Knowledge Base",
        "generated_with_clarification": "AI Generated — With Engineer Clarification",
        "human_override":               "Human Verified — Manually Reviewed",
        "hitl_escalated":               "Escalated — Insufficient Data for Automated RCA",
    }.get(source, source)

    # Parse TECHNICAL / SYSTEMIC sections
    import re as _re
    tech_m = _re.search(r"TECHNICAL CAUSE:\s*([\s\S]*?)(?=\n\nSYSTEMIC CAUSE:|$)",
                        root_cause or "", _re.IGNORECASE)
    sys_m  = _re.search(r"SYSTEMIC CAUSE:\s*([\s\S]*?)$",
                        root_cause or "", _re.IGNORECASE)
    technical_text = tech_m.group(1).strip() if tech_m else (root_cause or "–")
    systemic_text  = sys_m.group(1).strip()  if sys_m  else None

    content = [
        {
            "type": "heading", "attrs": {"level": 2},
            "content": [{"type": "text", "text": "🔍 Copilot Root Cause Analysis Report"}]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": f"{conf_emoji}  Confidence: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": confidence},
                {"type": "hardBreak"},
                {"type": "text", "text": "Source: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": source_label},
                {"type": "hardBreak"},
                {"type": "text", "text": "Affected Component: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": affected or "–", "marks": [{"type": "strong"}, {"type": "em"}]},
            ]
        },
        {
            "type": "heading", "attrs": {"level": 3},
            "content": [{"type": "text", "text": "🔧 Technical Cause"}]
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": technical_text}]
        },
    ]

    if systemic_text:
        content += [
            {
                "type": "heading", "attrs": {"level": 3},
                "content": [{"type": "text", "text": "📊 Systemic Cause  [Problem Management]"}]
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": systemic_text}]
            },
            {
                "type": "blockquote",
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": ("ℹ️  The systemic cause identifies the underlying process or "
                                 "organisational gap that allowed this incident to occur. "
                                 "A problem management task should be created to prevent recurrence."),
                        "marks": [{"type": "em"}]
                    }]
                }]
            }
        ]

    content.append({
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "— AMS Copilot RCA Engine  |  ", "marks": [{"type": "em"}]},
            {"type": "text", "text": "Resolution steps available in the SOP/Runbook tab.",
             "marks": [{"type": "em"}]},
        ]
    })

    adf_body = {"type": "doc", "version": 1, "content": content}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                url, json={"body": adf_body}, headers=headers, auth=auth
            )
        if res.status_code not in [200, 201]:
            print(f"❌ add_rca_comment failed [{issue_key}]: {res.status_code} — {res.text[:300]}")
            return False
        print(f"💬 [{issue_key}] RCA comment posted to Jira")
        return True
    except Exception as e:
        print(f"❌ add_rca_comment exception [{issue_key}]: {e}")
        return False


# ─────────────────────────────────────────────
# GENERIC JIRA COMMENT
# ─────────────────────────────────────────────
async def add_comment(issue_key: str, text: str):
    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
        }
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(url, json=payload, headers=headers, auth=auth)
        if res.status_code not in [200, 201]:
            print("❌ add_comment:", res.text)
            return False
        return True
    except Exception as e:
        print("❌ add_comment exception:", e)
        return False


# ─────────────────────────────────────────────
# LINK DUPLICATE COMMENTS
# ─────────────────────────────────────────────
async def link_duplicate_comments(parent_jira_id: str, child_jira_id: str):
    try:
        comments_url = f"{BASE_URL}/rest/api/3/issue/{parent_jira_id}/comment"
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(comments_url, headers=headers, auth=auth)
        comments = res.json().get("comments", []) if res.status_code == 200 else []

        parent_comment_id = None
        child_ids = []

        for c in comments:
            body    = c.get("body", {})
            content = body.get("content", [])
            text    = ""
            for item in content:
                for x in item.get("content", []):
                    text += x.get("text", "")
            if text.startswith("Children:"):
                parent_comment_id = c["id"]
                existing = text.replace("Children:", "").strip()
                if existing:
                    child_ids = [x.strip() for x in existing.split(",")]
                break

        if child_jira_id not in child_ids:
            child_ids.append(child_jira_id)

        updated_text = "Children: " + ", ".join(child_ids)
        payload = {
            "body": {"type": "doc", "version": 1,
                     "content": [{"type": "paragraph",
                                  "content": [{"type": "text", "text": updated_text}]}]}
        }

        async with httpx.AsyncClient(timeout=15) as client:
            if parent_comment_id:
                await client.put(
                    f"{BASE_URL}/rest/api/3/issue/{parent_jira_id}/comment/{parent_comment_id}",
                    json=payload, headers=headers, auth=auth
                )
            else:
                await client.post(comments_url, json=payload, headers=headers, auth=auth)

        await add_comment(child_jira_id, f"Parent: {parent_jira_id}")
        return True

    except Exception as e:
        print("❌ link_duplicate_comments:", e)
        return False


# ─────────────────────────────────────────────
# UNLINK DUPLICATE COMMENTS
# ─────────────────────────────────────────────
async def unlink_duplicate_comments(parent_jira_id: str, child_jira_id: str):
    try:
        comments_url = f"{BASE_URL}/rest/api/3/issue/{parent_jira_id}/comment"
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(comments_url, headers=headers, auth=auth)

        if res.status_code == 200:
            for c in res.json().get("comments", []):
                body = str(c.get("body", ""))
                if "Children:" not in body:
                    continue
                comment_id = c["id"]
                ids = [x for x in re.findall(r"[A-Z]+-\d+", body) if x != child_jira_id]
                if not ids:
                    async with httpx.AsyncClient(timeout=15) as client:
                        await client.delete(
                            f"{BASE_URL}/rest/api/3/issue/{parent_jira_id}/comment/{comment_id}",
                            headers=headers, auth=auth
                        )
                else:
                    updated = "Children: " + ", ".join(ids)
                    payload = {
                        "body": {"type": "doc", "version": 1,
                                 "content": [{"type": "paragraph",
                                              "content": [{"type": "text", "text": updated}]}]}
                    }
                    async with httpx.AsyncClient(timeout=15) as client:
                        await client.put(
                            f"{BASE_URL}/rest/api/3/issue/{parent_jira_id}/comment/{comment_id}",
                            json=payload, headers=headers, auth=auth
                        )
                break

        child_url = f"{BASE_URL}/rest/api/3/issue/{child_jira_id}/comment"
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(child_url, headers=headers, auth=auth)
        if res.status_code == 200:
            for c in res.json().get("comments", []):
                if f"Parent: {parent_jira_id}" in str(c.get("body", "")):
                    async with httpx.AsyncClient(timeout=15) as client:
                        await client.delete(
                            f"{BASE_URL}/rest/api/3/issue/{child_jira_id}/comment/{c['id']}",
                            headers=headers, auth=auth
                        )
                    break
        return True

    except Exception as e:
        print("❌ unlink_duplicate_comments:", e)
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
# MIGRATE MERGE COMMENTS
# ─────────────────────────────────────────────
async def migrate_merge_comments(old_parent: str, new_parent: str, moved_ids: list[str]):
    try:
        for ticket_id in moved_ids:
            await unlink_duplicate_comments(old_parent, ticket_id)
        for ticket_id in moved_ids:
            await link_duplicate_comments(new_parent, ticket_id)
        return True
    except Exception as e:
        print("❌ migrate_merge_comments:", e)
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
                url, json={"transition": {"id": transition_id}}, headers=headers, auth=auth
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
    return [t for t in tickets
            if t.get("issue_key") == parent_key
            or t.get("parent_ticket_key") == parent_key]


# ─────────────────────────────────────────────
# COMPLETE PARENT + ALL CHILDREN
# ─────────────────────────────────────────────
async def complete_parent_and_children(parent_key: str):
    try:
        related = await get_related_tickets(parent_key)
        if not related:
            return False
        success = True
        for t in related:
            if t.get("issue_key") and not await update_jira_status(t["issue_key"]):
                success = False
        return success
    except Exception as e:
        print("❌ complete_parent_and_children exception:", str(e))
        return False


# ─────────────────────────────────────────────
# DELETE PARENT + ALL CHILDREN
# ─────────────────────────────────────────────
async def delete_parent_and_children(parent_key: str):
    try:
        related  = await get_related_tickets(parent_key)
        if not related:
            return False
        children = [t for t in related if t.get("parent_ticket_key") == parent_key]
        parent   = [t for t in related if t.get("issue_key") == parent_key]
        success  = True
        for t in children + parent:
            if t.get("issue_key") and not await delete_jira_ticket(t["issue_key"]):
                success = False
        return success
    except Exception as e:
        print("❌ delete_parent_and_children exception:", str(e))
        return False