import os
import uuid
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI(title="EquiForensics API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/config")
def get_config():
    """Provides public Supabase keys to the frontend dynamically."""
    return {"supabase_url": SUPABASE_URL, "supabase_key": SUPABASE_KEY}

@app.get("/search-papers")
def search_papers(query: str = Query("*"), min_year: int = 2000):
    try:
        response = supabase.rpc("search_papers", {"search_query": query, "min_year": min_year}).execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/search-labs")
def search_labs(query: Optional[str] = None, iso_only: bool = False):
    try:
        qb = supabase.table("labs").select("*")
        if iso_only:
            qb = qb.eq("is_iso_17025", True)
        if query and query != "*":
            qb = qb.ilike("lab_name", f"%{query}%")
        response = qb.execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/search-experts")
def search_experts():
    """Searches the profiles table for available forensic experts."""
    try:
        # Returns users who are marked as experts and are available
        response = supabase.table("profiles")\
            .select("id, full_name, city, specialties, hourly_rate, bio")\
            .eq("user_type", "forensic_expert")\
            .eq("is_available", True)\
            .execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/create-consultation")
def create_consultation():
    room_code = f"EquiForensics-Secure-{uuid.uuid4().hex[:10]}"
    return {"status": "success", "room_url": f"https://meet.jit.si/{room_code}"}