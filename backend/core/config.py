import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL missing in .env")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY missing in .env")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

class Config:
    JIRA_EMAIL     = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_DOMAIN    = os.getenv("JIRA_DOMAIN")
    SERVICE_DESK_ID = os.getenv("SERVICE_DESK_ID")
    REQUEST_TYPE_ID = os.getenv("REQUEST_TYPE_ID")

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    BETTERSTACK_SOURCE_TOKEN= os.getenv("BETTERSTACK_SOURCE_TOKEN")

    JIRA_URGENCY_FIELD = os.getenv("JIRA_URGENCY_FIELD")

    JIRA_IMPACT_FIELD = os.getenv("JIRA_IMPACT_FIELD")