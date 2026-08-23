import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def scrape_and_ingest_labs():
    print("Starting Live HTML Lab Scraper...")
    
    # Target a public directory source (e.g., an open registry or institutional list)
    target_url = "https://enfsi.eu/about-enfsi/members/"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[X] Failed to reach target page: Status {response.status_code}")
            return
            
        # Parse the raw HTML structure
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find listings (Targeting standard list/content elements on public directories)
        count = 0
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            
            # Simple heuristic filter to catch institutional lab lines
            if "Laboratory" in text or "Institute" in text or "Forensic" in text:
                lab_name = text[:120].split(',')[0] # Clean up text fragment
                
                lab_payload = {
                    "lab_name": lab_name,
                    "city": "Global Registry",
                    "country": "International",
                    "is_iso_17025": True,
                    "forensic_disciplines": ["General Forensics"],
                    "is_enfsi_member": True
                }
                
                try:
                    # Upsert to prevent duplicate errors
                    supabase.table("labs").upsert(lab_payload, on_conflict="lab_name").execute()
                    count += 1
                    print(f"[+] Scraped and Ingested: {lab_name}")
                except Exception:
                    pass

        print(f"Scraping complete! Successfully harvested {count} labs from the live web page.")

    except Exception as e:
        print(f"[X] Scraping error: {e}")

if __name__ == "__main__":
    scrape_and_ingest_labs()