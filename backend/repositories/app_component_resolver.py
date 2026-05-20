from repositories.ticket_repository import supabase

def normalize(text: str):
    return (text or "").strip()

async def resolve_app_component(app_name: str, component_name: str):
    app_name = normalize(app_name)
    component_name = normalize(component_name)

    if not app_name or not component_name:
        return None, None

    app_res = supabase.table("ams_apps") \
        .select("app_code") \
        .eq("app_name", app_name) \
        .maybe_single() \
        .execute()

    comp_res = supabase.table("ams_components") \
        .select("component_code") \
        .eq("component_name", component_name) \
        .maybe_single() \
        .execute()

    app_code = app_res.data.get("app_code") if app_res.data else None
    component_code = comp_res.data.get("component_code") if comp_res.data else None

    print("DEBUG RESOLVER:", app_name, component_name, app_code, component_code)

    return app_code, component_code