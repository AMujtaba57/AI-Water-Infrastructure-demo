# data_extraction.py
import re
import pandas as pd
from supabase import create_client, Client
import PyPDF2  # For PDF parsing
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_water_district_data(text_content):
    """Extract water district data from text content"""
    districts = []
    
    # Split by water district sections
    district_sections = re.split(r'Water District:', text_content)
    
    for section in district_sections[1:]:  # Skip first empty section
        district_data = {}
        
        # Extract district name (first line)
        name_match = re.match(r'^\s*([A-Z]+)\s*', section)
        if name_match:
            district_data['name'] = name_match.group(1).strip()
        
        # Extract budget
        budget_match = re.search(r'\$([\d\.]+[BM]?)', section)
        if budget_match:
            budget_str = budget_match.group(1)
            # Convert to numeric value
            if 'B' in budget_str:
                budget = float(budget_str.replace('B', '')) * 1000000000
            elif 'M' in budget_str:
                budget = float(budget_str.replace('M', '')) * 1000000
            else:
                budget = float(budget_str) * 1000000
            district_data['budget'] = budget
        
        # Extract cities served count
        cities_match = re.search(r'Cities Served.*?(\d+)', section)
        if cities_match:
            district_data['cities_served'] = int(cities_match.group(1))
        else:
            # Estimate based on content
            cities_list = re.findall(r'- City:.*', section)
            district_data['cities_served'] = len(cities_list) if cities_list else 0
        
        # Extract APL alignment
        apl_match = re.search(r'APL/Spec Alignment.*?(STRONG|MODERATE|UNKNOWN)', section, re.IGNORECASE)
        if apl_match:
            district_data['apl_alignment'] = apl_match.group(1).upper()
        
        districts.append(district_data)
    
    return districts

def parse_markdown_file(md_path):
    """Parse the markdown file for city and county data"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    counties_data = []
    
    # Find all county sections
    county_pattern = r'## \*\*County: (.*?)\*\*(.*?)(?=## \*\*County: |\Z)'
    county_matches = re.findall(county_pattern, content, re.DOTALL)
    
    for county_name, county_content in county_matches:
        county_data = {
            'name': county_name.strip(),
            'water_districts': []
        }
        
        # Find water districts in this county
        district_pattern = r'\*\*Water District: (.*?)\*\*(.*?)(?=\*\*Water District: |\Z)'
        district_matches = re.findall(district_pattern, county_content, re.DOTALL)
        
        for district_name, district_content in district_matches:
            district_info = {
                'name': district_name.strip(),
                'cities': []
            }
            
            # Extract cities
            city_pattern = r'- City: (.*?)(?:\(.*?\))?(?:\n|$)'
            cities = re.findall(city_pattern, district_content)
            district_info['cities'] = [city.strip() for city in cities]
            
            county_data['water_districts'].append(district_info)
        
        counties_data.append(county_data)
    
    return counties_data

def get_color_code(county_name):
    # Assign color codes based on county
    color_map = {
        'Collin': '#FF6B6B',
        'Dallas': '#4ECDC4',
        'Denton': '#45B7D1',
        'Tarrant': '#96CEB4',
        'Ellis': '#FECA57',
        'Fannin': '#FF9FF3',
        'Grayson': '#54A0FF',
        'Kaufman': '#5F27CD',
        'Parker': '#00D2D3',
        'Rockwall': '#FF9F43',
        'Walker': '#A3CB38',
        'Wise': '#C44569'
    }
    return color_map.get(county_name, '#CCCCCC')

def load_data_to_supabase():
    districts_names = []
    print("Loading data to Supabase...")
    
    # Extract data from PDF
    pdf_text = extract_text_from_pdf('data/North Texas Water District Ranking Data.pdf')
    districts = extract_water_district_data(pdf_text)
    
    # Load water districts to Supabase
    for district in districts:
        try:
            result = supabase.table('water_districts').insert(district).execute()
            districts_names.append(district['name'])
            print(f"Added district: {district['name']}")
        except Exception as e:
            print(f"Error adding district {district['name']}: {e}")
    
    # Parse markdown file
    counties_data = parse_markdown_file('data/nt-water-verified.md')
    
    # Load counties, cities, and relationships
    for county_data in counties_data:
        # Insert county
        county_obj = {
            'name': county_data['name'],
            'color_code': get_color_code(county_data['name'])
        }
        try:
            county_result = supabase.table('counties').insert(county_obj).execute()
            county_id = county_result.data[0]['id']
            print(f"Added county: {county_data['name']}")
        except Exception as e:
            print(f"Error adding county {county_data['name']}: {e}")
            continue
        
        # Process water districts in this county
        for district_info in county_data['water_districts']:
            # Find or create water district
            try:
                flag = False
                for name in districts_names:
                    if name in district_info['name']:
                        flag = True
                        print(f"District {district_info['name']} found in PDF")
                        district_result = supabase.table('water_districts').select('*').eq('name', name).execute()
                        if district_result.data:
                            district_id = district_result.data[0]['id']
                if not flag:
                    # Create new district if not found
                    new_district = {'name': district_info['name']}
                    district_result = supabase.table('water_districts').insert(new_district).execute()
                    district_id = district_result.data[0]['id']
                    print(f"Created new district: {district_info['name']}")
            except Exception as e:
                print(f"Error finding/creating district {district_info['name']}: {e}")
                continue
            
            # Insert cities
            for city_name in district_info['cities']:
                city_data = {
                    'name': city_name,
                    'county_id': county_id,
                    'water_district_id': district_id,
                    'apl_status': 'Not Submitted',  # Default value
                    'score': 0  # Default value
                }
                try:
                    supabase.table('cities').insert(city_data).execute()
                    print(f"Added city: {city_name}")
                except Exception as e:
                    print(f"Error adding city {city_name}: {e}")

if __name__ == "__main__":
    load_data_to_supabase()
    print("Data loading completed!")
