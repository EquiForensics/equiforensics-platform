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

FALLBACK_LABS = [
    {"lab_name": "Bundeskriminalamt (BKA) Forensic Science Institute", "city": "Wiesbaden", "country": "Germany", "is_iso_17025": True, "forensic_disciplines": ["DNA Profiling", "Ballistics"], "is_enfsi_member": True},
    {"lab_name": "Netherlands Forensic Institute (NFI)", "city": "The Hague", "country": "Netherlands", "is_iso_17025": True, "forensic_disciplines": ["Digital Forensics", "Pathology"], "is_enfsi_member": True},
    {"lab_name": "Federal Bureau of Investigation (FBI) Laboratory", "city": "Quantico, VA", "country": "USA", "is_iso_17025": True, "forensic_disciplines": ["DNA Profiling", "Trace Evidence"], "is_enfsi_member": False}
]

# Helper function to check for duplicates before inserting
def safe_insert(lab_data):
    try:
        # Check if lab name already exists
        existing = supabase.table("labs").select("id").eq("lab_name", lab_data["lab_name"]).execute()
        if existing.data and len(existing.data) > 0:
            return False # It exists, skip it
            
        # If it doesn't exist, insert it
        supabase.table("labs").insert(lab_data).execute()
        return True
    except Exception as e:
        print(f"  [X] DB Error inserting {lab_data['lab_name']}: {e}")
        return False

def scrape_and_ingest_labs():
    print("Starting Live HTML Lab Scraper...")
    target_url = "https://enfsi.eu/about-enfsi/members/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    count = 0
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.find_all(['li', 'td', 'div', 'p'])
            
            for el in elements:
                text = el.get_text(strip=True)
                
                if len(text) > 10 and ("Laboratory" in text or "Institute" in text or "Forensic" in text or "Police" in text):
                    lab_name = text[:100].split(',')[0].strip()
                    lab_payload = {
                        "lab_name": lab_name,
                        "city": "Global Registry",
                        "country": "International",
                        "is_iso_17025": True,
                        "forensic_disciplines": ["General Forensics"],
                        "is_enfsi_member": True
                    }
                    
                    if safe_insert(lab_payload):
                        count += 1
                        
    except Exception as e:
        print(f"[!] Network or parsing error occurred: {e}")

    # THE FALLBACK TRIGGER
    if count == 0:
        print("[!] Live scraping yielded 0 new results. Checking Fallback Seed Data...")
        fallback_count = 0
        for lab in FALLBACK_LABS:
            if safe_insert(lab):
                fallback_count += 1
                
        print(f"[✓] Successfully injected {fallback_count} new fallback labs.")
    else:
        print(f"[✓] Scraping complete! Successfully harvested {count} labs from the live web page.")

if __name__ == "__main__":
    scrape_and_ingest_labs()