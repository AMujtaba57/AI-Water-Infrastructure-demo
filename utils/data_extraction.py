import re
from supabase import create_client

# --- Supabase Config (replace with your project credentials) ---
SUPABASE_URL = "https://dukggntwutqovhwuttua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR1a2dnbnR3dXRxb3Zod3V0dHVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwNTc1MzIsImV4cCI6MjA3MTYzMzUzMn0.U6wUS_WWS2O79f7pU2SyEosi5u8W0ULfWRrE_4kG3xY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Load Markdown Dataset ---
with open("data/nt-water-verified.md", "r", encoding="utf-8") as f:
    md_data = f.read()

county_pattern = re.compile(r"## \*\*County: (.*?)\*\*")
district_pattern = re.compile(r"\*\*Water District: (.*?)\*\*")
city_pattern = re.compile(r"\s*-\s*City: (.*?) \((.*?)\)")

current_county = None
current_district = None

for line in md_data.splitlines():
    county_match = county_pattern.match(line)
    district_match = district_pattern.match(line)
    city_match = city_pattern.match(line)

    if county_match:
        current_county = county_match.group(1).strip()
        # insert or fetch county
        county_resp = supabase.table("counties").insert({"name": current_county}).execute()
        if "data" in county_resp and county_resp.data:
            county_id = county_resp.data[0]["id"]
        else:
            # fetch if already exists
            county_id = supabase.table("counties").select("id").eq("name", current_county).execute().data[0]["id"]

    elif district_match and current_county:
        current_district = district_match.group(1).strip()
        district_resp = supabase.table("districts").insert({"name": current_district, "county_id": county_id}).execute()
        if "data" in district_resp and district_resp.data:
            district_id = district_resp.data[0]["id"]
        else:
            district_id = supabase.table("districts").select("id").eq("name", current_district).execute().data[0]["id"]

    elif city_match and current_district:
        city_name, service_type = city_match.groups()
        city_resp = supabase.table("cities").insert({
            "name": city_name.strip(),
            "service_type": service_type.strip(),
            "district_id": district_id
        }).execute()
        # ignore duplicates safely

print("Counties, Districts, and Cities loaded into Supabase")
