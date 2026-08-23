import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
OPENALEX_API_URL = "https://api.openalex.org/works"

# Expanded broad forensic topics to build a massive library
FORENSIC_TOPICS = [
    {"query": "DNA profiling forensic", "discipline": "DNA & Serology"},
    {"query": "Digital forensics file carving", "discipline": "Digital & Cyber Forensics"},
    {"query": "Bloodstain pattern analysis", "discipline": "Crime Scene Reconstruction"},
    {"query": "Forensic toxicology hair analysis", "discipline": "Toxicology & Chemistry"},
    {"query": "Ballistics toolmark identification", "discipline": "Firearms & Ballistics"},
    {"query": "Fingerprint ridge characteristics", "discipline": "Pattern Evidence"},
    {"query": "Forensic pathology autopsy standards", "discipline": "Pathology & Medicine"},
    {"query": "Cybersecurity incident response forensics", "discipline": "Digital & Cyber Forensics"}
]

def ingest_papers():
    print("Starting EquiForensics Massive Paper Ingestion Pipeline...")
    total_inserted = 0

    for topic in FORENSIC_TOPICS:
        search_query = topic["query"]
        discipline = topic["discipline"]
        print(f"\n[+] Fetching open-access papers for: {search_query}")
        
        params = {
            "search": search_query,
            "filter": "is_oa:true,publication_year:>2015",
            "per-page": 50, # Pull top 50 per category
            "sort": "cited_by_count:desc"
        }
        
        try:
            response = requests.get(OPENALEX_API_URL, params=params, timeout=20)
            if response.status_code != 200:
                print(f"[X] API Error for {search_query}: Status {response.status_code}")
                continue
                
            data = response.json()
            works = data.get("results", [])
            
            for work in works:
                title = work.get("title")
                if not title:
                    continue
                
                # Extract publication year
                pub_year = work.get("publication_year", 2020)
                
                # Extract citation count
                citations = work.get("cited_by_count", 0)
                
                # Extract authors
                authors = []
                for authorship in work.get("authorships", []):
                    author_name = authorship.get("author", {}).get("display_name")
                    if author_name:
                        authors.append(author_name)
                        
                # Extract PDF URL if available
                pdf_url = None
                oa_location = work.get("open_access", {})
                if oa_location.get("is_oa") and oa_location.get("oa_url"):
                    pdf_url = oa_location.get("oa_url")
                
                paper_payload = {
                    "title": title,
                    "publication_year": pub_year,
                    "discipline": discipline,
                    "authors": authors[:5], # Store top 5 authors
                    "citation_count": citations,
                    "pdf_url": pdf_url
                }
                
                # Upsert into Supabase (avoids duplicates based on title if unique constraint exists, else inserts)
                try:
                    supabase.table("papers").upsert(paper_payload, on_conflict="title").execute()
                    total_inserted += 1
                except Exception as db_err:

                    # Fallback standard insert if upsert conflict constraint isn't set
                    try:
                        supabase.table("papers").insert(paper_payload).execute()
                        total_inserted += 1
                    except Exception:
                        pass
                        
            print(f"[✓] Processed category: {discipline}")

        except Exception as e:
            print(f"[X] Error fetching {search_query}: {e}")

    print(f"\nPipeline complete! Successfully processed and synced papers to database.")

if __name__ == "__main__":
    ingest_papers()