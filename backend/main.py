import os
import uuid
import io
from typing import Optional
from fastapi import FastAPI, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI(title="EquiForensics API", version="1.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/config")
def get_config():
    return {"supabase_url": SUPABASE_URL, "supabase_key": SUPABASE_KEY}

@app.get("/search-papers")
def search_papers(query: str = Query("*"), min_year: int = 2000):
    try:
        response = supabase.rpc("search_papers", {"search_query": query, "min_year": min_year}).execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# UPDATED: Labs search with location & discipline filters
@app.get("/search-labs")
def search_labs(query: Optional[str] = None, location: Optional[str] = None, discipline: Optional[str] = None):
    try:
        qb = supabase.table("labs").select("*")
        if query and query != "*":
            qb = qb.ilike("lab_name", f"%{query}%")
        if location and location != "":
            qb = qb.ilike("city", f"%{location}%")
        if discipline and discipline != "":
            qb = qb.contains("forensic_disciplines", [discipline])
        response = qb.execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# UPDATED: Experts search with location & specialty filters
@app.get("/search-experts")
def search_experts(location: Optional[str] = None, specialty: Optional[str] = None):
    try:
        qb = supabase.table("profiles")\
            .select("id, full_name, city, specialties, hourly_rate, bio")\
            .eq("user_type", "forensic_expert")\
            .eq("is_available", True)
        
        if location and location != "":
            qb = qb.ilike("city", f"%{location}%")
        if specialty and specialty != "":
            qb = qb.contains("specialties", [specialty])
            
        response = qb.execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/create-consultation")
def create_consultation():
    room_code = f"EquiForensics-Secure-{uuid.uuid4().hex[:10]}"
    return {"status": "success", "room_url": f"https://meet.jit.si/{room_code}"}

@app.post("/extract-pdf-text")
async def extract_pdf_text(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        return {"status": "success", "text": extracted_text.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}