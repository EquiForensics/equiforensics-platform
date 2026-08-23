import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

FALLBACK_LABS = [
    {"lab_name": "Bundeskriminalamt (BKA) Forensic Science Institute", "city": "Wiesbaden", "country": "Germany", "is_iso_17025": True, "forensic_disciplines": ["DNA Profiling", "Ballistics"]},
    {"lab_name": "Netherlands Forensic Institute (NFI)", "city": "The Hague", "country": "Netherlands", "is_iso_17025": True, "forensic_disciplines": ["Digital Forensics", "Pathology"]},
    {"lab_name": "Federal Bureau of Investigation (FBI) Laboratory", "city": "Quantico", "country": "USA", "is_iso_17025": True, "forensic_disciplines": ["DNA Profiling", "Trace Evidence"]},
    {"lab_name": "Scottish Police Authority Forensic Services", "city": "Glasgow", "country": "UK", "is_iso_17025": True, "forensic_disciplines": ["Biology", "Chemistry"]}
]

def safe_insert(lab_data):
    try:
        existing = supabase.table("labs").select("id").eq("lab_name", lab_data["lab_name"]).execute()
        if existing.data and len(existing.data) > 0:
            return False 
        supabase.table("labs").insert(lab_data).execute()
        return True
    except Exception as e:
        print(f"  [X] DB Error inserting {lab_data['lab_name']}: {e}")
        return False

def scrape_and_ingest_labs():
    print("Starting Smarter HTML Lab Scraper...")
    target_url = "https://enfsi.eu/about-enfsi/members/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    count = 0
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.find_all(['li', 'td', 'div', 'p'])
            
            for el in elements:
                text = el.get_text(strip=True)
                
                # Check if it looks like a lab entry
                if len(text) > 10 and ("Laboratory" in text or "Institute" in text or "Forensic" in text or "Police" in text):
                    # Smart Parsing: Split by commas to get real locations
                    parts = [p.strip() for p in text.split(',')]
                    
                    lab_name = parts[0][:100]
                    # If they provided a city/country, use it. Otherwise, set as unknown.
                    city = parts[1] if len(parts) > 1 else "Unknown City"
                    country = parts[2] if len(parts) > 2 else "Unknown Country"
                    
                    lab_payload = {
                        "lab_name": lab_name,
                        "city": city,
                        "country": country,
                        "is_iso_17025": True,
                        "forensic_disciplines": ["General Forensics"],
                        "is_enfsi_member": True
                    }
                    
                    if safe_insert(lab_payload):
                        print(f"  [+] Scraped: {lab_name} | {city}, {country}")
                        count += 1
                        
    except Exception as e:
        print(f"[!] Network or parsing error occurred: {e}")

    if count == 0:
        print("[!] No new dynamic labs found. Checking Fallbacks...")
        fallback_count = 0
        for lab in FALLBACK_LABS:
            if safe_insert(lab):
                fallback_count += 1
        print(f"[✓] Injected {fallback_count} new fallback labs.")
    else:
        print(f"[✓] Scraping complete! Harvested {count} labs.")

if __name__ == "__main__":
    scrape_and_ingest_labs()