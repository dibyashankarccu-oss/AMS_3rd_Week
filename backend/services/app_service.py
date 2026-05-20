from repositories.ticket_repository import supabase

async def get_apps_with_components():
    apps_res = supabase.table("ams_apps").select("*").execute()
    comps_res = supabase.table("ams_components").select("*").execute()

    apps = apps_res.data or []
    comps = comps_res.data or []

    comp_map = {}

    for c in comps:
        comp_map.setdefault(c["app_id"], []).append({
            "component_name": c["component_name"],
            "component_code": c["component_code"]
        })

    result = []
    for a in apps:
        result.append({
            "app_name": a["app_name"],
            "app_code": a["app_code"],
            "components": comp_map.get(a["id"], [])
        })

    return result