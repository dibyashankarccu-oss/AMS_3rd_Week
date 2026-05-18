import os
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer

# ── Load env ──
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ── Init clients ──
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model    = SentenceTransformer("all-MiniLM-L6-v2")


# ── Build embedding text ──
def build_text(r):
    return f"""
    Title:     {r['title']}
    Category:  {r['category']}
    Symptoms:  {r['symptoms']}
    Keywords:  {r['keywords']}
    RootCause: {r['root_cause']}
    """


# ── Fetch all RCA KB entries ──
res = supabase.table("rca_knowledge_base").select("*").execute()

if not res.data:
    print("❌ No entries found in rca_knowledge_base — run the SQL seed first")
    exit()

print(f"🔍 Found {len(res.data)} RCA knowledge base entries")

# ── Generate + store embeddings ──
for r in res.data:
    try:
        text      = build_text(r)
        embedding = model.encode(text).tolist()

        supabase.table("rca_knowledge_base").update({
            "embedding": embedding
        }).eq("id", r["id"]).execute()

        print(f"✅ Embedded: {r['title']}")

    except Exception as e:
        print(f"❌ Failed for {r['title']}: {e}")

print("🎉 All RCA KB embeddings stored successfully!")