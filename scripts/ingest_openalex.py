import os
import time
import requests
from urllib.parse import quote
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Load secure credentials
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Use the SERVICE_KEY for admin write privileges!
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing credentials in .env file.")

# Initialize Supabase with the Admin Key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
OPENALEX_API_URL = "https://api.openalex.org/works"

def fetch_and_upload_papers(disciplines: list):
    headers = {"User-Agent": "EquiForensics/1.1 (mailto:contact@equiforensics.com)"}
    
    for discipline in disciplines:
        print(f"\n[+] Fetching open-access papers for: {discipline}")
        encoded_query = quote(discipline)
        url = f"{OPENALEX_API_URL}?search={encoded_query}&filter=is_oa:true&per-page=25"
        
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            
            papers_to_insert = []
            for raw_paper in results:
                if raw_paper.get("is_retracted", False):
                    continue # Skip retracted papers for legal integrity
                
                doi = raw_paper.get("doi")
                doc_id = doi.replace("https://doi.org/", "") if doi else raw_paper.get("id", "").split("/")[-1]
                authors = [a.get("author", {}).get("display_name") for a in raw_paper.get("authorships", []) if a.get("author", {}).get("display_name")]
                
                papers_to_insert.append({
                    "id": doc_id,
                    "title": raw_paper.get("title") or "Untitled Paper",
                    "doi": doi or "",
                    "publication_year": raw_paper.get("publication_year") or 0,
                    "discipline": discipline,
                    "is_open_access": raw_paper.get("open_access", {}).get("is_oa", False),
                    "pdf_url": raw_paper.get("open_access", {}).get("oa_url") or "",
                    "authors": authors,
                    "citation_count": raw_paper.get("cited_by_count", 0),
                    "is_retracted": False
                })

            if papers_to_insert:
                supabase.table("papers").upsert(papers_to_insert).execute()
                print(f"[✓] Ingested {len(papers_to_insert)} validated papers for '{discipline}'.")
                
        except Exception as e:
            print(f"[X] Error fetching {discipline}: {e}")
            
        time.sleep(1.0) # Be polite to the API limits

if __name__ == "__main__":
    disciplines = ["DNA profiling forensic", "Digital forensics file carving", "Bloodstain pattern analysis"]
    print("Starting EquiForensics Data Ingestion...")
    fetch_and_upload_papers(disciplines)
    print("Pipeline complete.")