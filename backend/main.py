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
app = FastAPI(title="EquiForensics API", version="1.5.0")

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

# Papers Search with Pagination
@app.get("/search-papers")
def search_papers(query: str = Query("*"), min_year: int = 2000, page: int = 1, page_size: int = 12):
    try:
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        qb = supabase.table("papers").select("*", count="exact").gte("publication_year", min_year)
        if query and query != "*":
            qb = qb.ilike("title", f"%{query}%")
            
        response = qb.order("citation_count", desc=True).range(start, end).execute()
        return {"status": "success", "results": response.data, "page": page, "page_size": page_size}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Labs Search with Pagination
@app.get("/search-labs")
def search_labs(query: Optional[str] = None, location: Optional[str] = None, page: int = 1, page_size: int = 12):
    try:
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        qb = supabase.table("labs").select("*", count="exact")
        if query and query != "*":
            qb = qb.ilike("lab_name", f"%{query}%")
        if location and location != "":
            qb = qb.ilike("city", f"%{location}%")
            
        response = qb.range(start, end).execute()
        return {"status": "success", "results": response.data, "page": page, "page_size": page_size}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Experts Search with Pagination
@app.get("/search-experts")
def search_experts(location: Optional[str] = None, page: int = 1, page_size: int = 12):
    try:
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        qb = supabase.table("profiles")\
            .select("id, full_name, city, specialties, hourly_rate, bio", count="exact")\
            .eq("user_type", "forensic_expert")\
            .eq("is_available", True)
        
        if location and location != "":
            qb = qb.ilike("city", f"%{location}%")
            
        response = qb.range(start, end).execute()
        return {"status": "success", "results": response.data, "page": page, "page_size": page_size}
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