-- Create counties table
CREATE TABLE counties (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color_code TEXT
);

-- Create water_districts table
CREATE TABLE water_districts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    budget NUMERIC,
    cities_served INTEGER,
    apl_alignment TEXT,
    project_activity TEXT,
    internal_support TEXT,
    score NUMERIC
);

-- Create engineering_firms table
CREATE TABLE engineering_firms (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    influence_level TEXT
);

-- Create cities table
CREATE TABLE cities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    county_id UUID REFERENCES counties(id),
    water_district_id UUID REFERENCES water_districts(id),
    engineering_firm_id UUID REFERENCES engineering_firms(id),
    apl_status TEXT DEFAULT 'Not Submitted',
    cip_budget NUMERIC,
    sewer_budget NUMERIC,
    score NUMERIC DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_cities_county_id ON cities(county_id);
CREATE INDEX idx_cities_water_district_id ON cities(water_district_id);
CREATE INDEX idx_cities_engineering_firm_id ON cities(engineering_firm_id);
CREATE INDEX idx_cities_score ON cities(score);