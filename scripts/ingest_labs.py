import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Expanded global directory of accredited institutions
GLOBAL_FORENSIC_LABS = [
    {
        "lab_name": "Bundeskriminalamt (BKA) Forensic Science Institute",
        "city": "Wiesbaden",
        "country": "Germany",
        "is_iso_17025": True,
        "forensic_disciplines": ["DNA Profiling", "Ballistics", "Digital Evidence"],
        "is_enfsi_member": True
    },
    {
        "lab_name": "Home Office Centre for Applied Science and Technology",
        "city": "London",
        "country": "UK",
        "is_iso_17025": True,
        "forensic_disciplines": ["Chemical Analysis", "Trace Evidence", "Explosives"],
        "is_enfsi_member": True
    },
    {
        "lab_name": "Institut National de Police Scientifique (INPS)",
        "city": "Ecully",
        "country": "France",
        "is_iso_17025": True,
        "forensic_disciplines": ["Ballistics", "DNA Profiling", "Fingerprints"],
        "is_enfsi_member": True
    },
    {
        "lab_name": "State Bureau of Forensic Expertise",
        "city": "Vienna",
        "country": "Austria",
        "is_iso_17025": True,
        "forensic_disciplines": ["Document Examination", "Cyber Forensics", "Toxicology"],
        "is_enfsi_member": True
    },
    {
        "lab_name": "Forensic Science Centre Ivan Vučetić",
        "city": "Zagreb",
        "country": "Croatia",
        "is_iso_17025": True,
        "forensic_disciplines": ["DNA Profiling", "Bloodstain Pattern Analysis"],
        "is_enfsi_member": True
    },
    {
        "lab_name": "Netherlands Forensic Institute (NFI)",
        "city": "The Hague",
        "country": "Netherlands",
        "is_iso_17025": True,
        "forensic_disciplines": ["DNA Profiling", "Digital Forensics", "Pathology"],
        "is_enfsi_member": True
    },
    {
        "lab_name": "Federal Bureau of Investigation (FBI) Laboratory",
        "city": "Quantico, VA",
        "country": "USA",
        "is_iso_17025": True,
        "forensic_disciplines": ["DNA Profiling", "Chemistry", "Trace Evidence", "Biometrics"],
        "is_enfsi_member": False
    },
    {
        "lab_name": "Victoria Police Forensic Services Department",
        "city": "Melbourne",
        "country": "Australia",
        "is_iso_17025": True,
        "forensic_disciplines": ["Chemical Analysis", "Ballistics", "Crime Scene Reconstruction"],
        "is_enfsi_member": False
    }
]

def ingest_labs():
    print("Starting EquiForensics Lab Ingestion Pipeline...")
    
    for lab in GLOBAL_FORENSIC_LABS:
        try:
            existing = supabase.table("labs").select("id").eq("lab_name", lab["lab_name"]).execute()
            
            if existing.data and len(existing.data) > 0:
                print(f"[i] Lab already exists, skipping: {lab['lab_name']}")
            else:
                supabase.table("labs").insert(lab).execute()
                print(f"[+] Successfully ingested lab: {lab['lab_name']} ({lab['country']})")
                
        except Exception as e:
            print(f"[X] Error inserting {lab['lab_name']}: {e}")

    print("Lab Ingestion Pipeline Complete.")

if __name__ == "__main__":
    ingest_labs()