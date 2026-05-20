# scripts/confluence_rca_sync.py
#
# Pulls RCA pages labelled "rca-kb" from Confluence and
# upserts them into rca_knowledge_base in Supabase.
#
# Confluence page hierarchy:
#   "AMS001 - Enterprise Incident Management System"   ← app page
#   └── "CMP001 - Ticket Intake API"                   ← component page
#       └── "RCA - Ticket Intake API"  [label: rca-kb] ← this is read
#
# The script strips the "AMS001 - " / "CMP001 - " prefixes to match
# app_name / component_name stored in ams_apps and ams_components tables.
#
# Run: python -m scripts.confluence_rca_sync

import os
import asyncio
import httpx

from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup

load_dotenv()

CONFLUENCE_BASE = os.getenv("CONFLUENCE_BASE_URL")
CONF_EMAIL      = os.getenv("CONFLUENCE_EMAIL")
CONF_TOKEN      = os.getenv("CONFLUENCE_API_TOKEN")
CONF_LABEL      = os.getenv("CONFLUENCE_RCA_LABEL", "rca-kb")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model    = SentenceTransformer("all-MiniLM-L6-v2")

auth    = (CONF_EMAIL, CONF_TOKEN)
cf_hdrs = {"Accept": "application/json"}

REQUIRED_SECTIONS = {
    "keywords", "symptoms", "root cause", "affected component", "confidence"
}


def strip_code_prefix(title: str) -> str:
    """
    "AMS001 - Enterprise Incident Management System" → "Enterprise Incident Management System"
    "CMP001 - Ticket Intake API"                    → "Ticket Intake API"
    "RCA - Ticket Intake API"                       → left as-is (not a code prefix)
    """
    import re
    # Match patterns like "AMS001 - " or "CMP001 - " at the start
    m = re.match(r'^[A-Z]+\d+\s*-\s*(.+)$', title.strip())
    return m.group(1).strip() if m else title.strip()


async def fetch_rca_pages() -> list:
    url   = f"{CONFLUENCE_BASE}/rest/api/content"
    pages = []
    start = 0
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            res = await client.get(url, auth=auth, headers=cf_hdrs, params={
                "type": "page", "label": CONF_LABEL,
                "expand": "body.storage,ancestors,version",
                "start": start, "limit": 25,
            })
            if res.status_code != 200:
                print(f"❌ Confluence fetch failed: {res.status_code}")
                break
            results = res.json().get("results", [])
            pages.extend(results)
            if len(results) < 25:
                break
            start += 25
    print(f"📄 Found {len(pages)} RCA pages with label '{CONF_LABEL}'")
    return pages


async def fetch_all_pages_map() -> dict:
    url   = f"{CONFLUENCE_BASE}/rest/api/content"
    pages = []
    start = 0
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            res = await client.get(url, auth=auth, headers=cf_hdrs, params={
                "type": "page", "expand": "ancestors",
                "start": start, "limit": 50,
            })
            if res.status_code != 200:
                break
            results = res.json().get("results", [])
            pages.extend(results)
            if len(results) < 50:
                break
            start += 50
    return {p["id"]: p for p in pages}


def resolve_app_component(page: dict, all_pages_map: dict):
    """
    Walk the ancestor chain to find the component page (direct parent)
    and app page (grandparent). Strip code prefixes to get clean names,
    then look up app_code and component_code from Supabase.
    """
    ancestors = page.get("ancestors", [])
    if len(ancestors) < 2:
        print(f"  ⚠️  '{page.get('title')}' has fewer than 2 ancestors — cannot resolve app/component")
        return None, None, None, None

    component_page = all_pages_map.get(ancestors[-1]["id"])
    app_page       = all_pages_map.get(ancestors[-2]["id"])

    if not component_page or not app_page:
        print(f"  ⚠️  Could not find ancestor pages in map for '{page.get('title')}'")
        return None, None, None, None

    raw_comp_title = component_page.get("title", "")
    raw_app_title  = app_page.get("title", "")

    # Strip "CMP001 - " / "AMS001 - " prefixes
    comp_name_clean = strip_code_prefix(raw_comp_title)
    app_name_clean  = strip_code_prefix(raw_app_title)

    print(f"  🔍 Resolving: app='{app_name_clean}' comp='{comp_name_clean}'")

    try:
        app_res = supabase.table("ams_apps") \
            .select("app_code, app_name") \
            .eq("app_name", app_name_clean) \
            .execute()

        comp_res = supabase.table("ams_components") \
            .select("component_code, component_name") \
            .eq("component_name", comp_name_clean) \
            .execute()

        app_data  = app_res.data[0]  if app_res.data  else None
        comp_data = comp_res.data[0] if comp_res.data else None

        app_code  = app_data.get("app_code")        if app_data  else None
        app_name  = app_data.get("app_name")        if app_data  else app_name_clean
        comp_code = comp_data.get("component_code") if comp_data else None
        comp_name = comp_data.get("component_name") if comp_data else comp_name_clean

        if not app_code:
            print(f"  ⚠️  app '{app_name_clean}' not found in ams_apps")
        if not comp_code:
            print(f"  ⚠️  component '{comp_name_clean}' not found in ams_components")

        return app_code, app_name, comp_code, comp_name

    except Exception as e:
        print(f"  ❌ resolve_app_component error: {e}")
        return None, app_name_clean, None, comp_name_clean


def parse_page(page: dict) -> dict | None:
    title   = page.get("title", "")
    page_id = page.get("id", "")
    body    = page.get("body", {}).get("storage", {}).get("value", "")

    text  = BeautifulSoup(body, "html.parser").get_text("\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    sections     = {}
    curr_heading = None
    curr_lines   = []

    for line in lines:
        low = line.lower()
        if low in REQUIRED_SECTIONS:
            if curr_heading and curr_lines:
                sections[curr_heading] = " ".join(curr_lines).strip()
            curr_heading = low
            curr_lines   = []
        else:
            if curr_heading:
                curr_lines.append(line)

    if curr_heading and curr_lines:
        sections[curr_heading] = " ".join(curr_lines).strip()

    missing = REQUIRED_SECTIONS - set(sections.keys())
    if missing:
        print(f"⚠️  Skipping '{title}' — missing sections: {missing}")
        return None

    confidence = sections.get("confidence", "").strip().upper()
    if confidence not in ("HIGH", "MEDIUM", "LOW"):
        print(f"⚠️  Skipping '{title}' — invalid confidence: '{confidence}'")
        return None

    return {
        "confluence_page_id": page_id,
        "title":              title,
        "category":           sections.get("category", "General"),
        "keywords":           sections.get("keywords", ""),
        "symptoms":           sections.get("symptoms", ""),
        "root_cause":         sections.get("root cause", ""),
        "affected_component": sections.get("affected component", ""),
        "confidence":         confidence,
        "status":             "Active",
    }


def upsert_entry(entry: dict) -> bool:
    embed_text = (
        f"{entry['title']} "
        f"{entry.get('keywords', '')} "
        f"{entry.get('symptoms', '')} "
        f"{entry.get('root_cause', '')}"
    )
    embedding = model.encode(embed_text).tolist()
    payload   = {**entry, "embedding": embedding}

    existing = supabase.table("rca_knowledge_base") \
        .select("id") \
        .eq("confluence_page_id", entry["confluence_page_id"]) \
        .execute()

    if existing.data:
        kb_id = existing.data[0]["id"]
        res   = supabase.table("rca_knowledge_base").update(payload).eq("id", kb_id).execute()
        print(f"  🔄 Updated:  '{entry['title']}' → {entry.get('app_code','GEN')}/{entry.get('component_code','GEN-CMP')}")
    else:
        payload["recurrence_count"] = 1
        res = supabase.table("rca_knowledge_base").insert(payload).execute()
        print(f"  ✅ Inserted: '{entry['title']}' → {entry.get('app_code','GEN')}/{entry.get('component_code','GEN-CMP')}")

    return bool(res.data)


async def sync():
    print("\n" + "="*60)
    print("CONFLUENCE RCA → SUPABASE SYNC")
    print("="*60)

    if not all([CONFLUENCE_BASE, CONF_EMAIL, CONF_TOKEN]):
        print("❌ Missing env vars: CONFLUENCE_BASE_URL / CONFLUENCE_EMAIL / CONFLUENCE_API_TOKEN")
        return

    rca_pages     = await fetch_rca_pages()
    all_pages_map = await fetch_all_pages_map()
    all_pages_map.update({p["id"]: p for p in rca_pages})

    inserted = updated = skipped = 0

    for page in rca_pages:
        print(f"\nProcessing: '{page.get('title')}'")

        entry = parse_page(page)
        if not entry:
            skipped += 1
            continue

        app_code, app_name, comp_code, comp_name = resolve_app_component(page, all_pages_map)
        entry["app_code"]       = app_code  or "GEN"
        entry["app_name"]       = app_name  or "General"
        entry["component_code"] = comp_code or "GEN-CMP"
        entry["component_name"] = comp_name or "General"

        was_existing = bool(
            supabase.table("rca_knowledge_base")
            .select("id")
            .eq("confluence_page_id", entry["confluence_page_id"])
            .execute().data
        )

        success = upsert_entry(entry)
        if success:
            if was_existing:
                updated += 1
            else:
                inserted += 1
        else:
            skipped += 1

    print(f"\n{'─'*60}")
    print(f"✅ Sync complete: {inserted} inserted, {updated} updated, {skipped} skipped")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    asyncio.run(sync())