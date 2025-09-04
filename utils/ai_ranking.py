"""
AI Matrix Infrastructure Intelligence Application
Main Streamlit Application with OpenAI Integration
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import openai
from openai import OpenAI
from typing import Dict, List, Tuple
import os
from dotenv import load_dotenv
import supabase
from utils.relationship_map import create_relationship_graph_v2
# Load environment variables
load_dotenv()

# Configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_API_MODEL")


# Page configuration
st.set_page_config(
    page_title="AI Matrix Infrastructure Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3d59;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .tier-1 { background-color: #48bb78; color: white; }
    .tier-2 { background-color: #4299e1; color: white; }
    .tier-3 { background-color: #ed8936; color: white; }
    .tier-4 { background-color: #f56565; color: white; }
</style>
""", unsafe_allow_html=True)

class InfrastructureRanker:
    """OpenAI-powered infrastructure ranking engine"""
    
    def __init__(self):
        self.client = OpenAI(api_key=openai.api_key)
    
    def calculate_district_score(self, district_data: Dict) -> Tuple[int, str, Dict]:
        """Calculate AI-powered score for a city"""
        
        prompt = f"""
        Analyze and score this North Texas city for infrastructure opportunities:

        District Name:  {district_data.get('name')}
        Infrastructure budget: {district_data.get('budget',0)}
        Cities Served: {district_data.get('cities_served',0)}
        Water District: {district_data.get('water_districts')}
        APL Status: {district_data.get('apl_alignement','')}
        Active Projects: {district_data.get('project_activity', 0)}
        Internal Support: {district_data.get('internal_support', "N/A")}
        
        Scoring Criteria (out of 100):
        1. Infrastructure Budget (max. 30 pts): Higher budgets = more opportunities
        2. Cities Served (max. 25 pts): More cities served = broader reach
        3. APL/Spec Alignment (max. 20 pts): STRONG=20, MODERATE=15, UNKNOWN=5
        4. Known Project Activity (max. 15 pts): More projects = higher score
        5. Internal Support (max. 10 pts): Documented support programs = higher score
        
        Return a JSON with:
        - score: numerical score 0-100
        - tier: 1-4 based on score (1=85-100, 2=70-84, 3=50-69, 4=<50)
        - breakdown: dict with each criteria score
        """
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an infrastructure sales intelligence analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            # return result.get('score', 0), result.get('tier', 4), result
            return result
            
        except Exception as e:
            print('#############',e)


def load_data():
    """Load data from Supabase with proper table relationships"""
    try:
        supabase = create_client(supabase_url,supabase_key)
        # Load water districts
        districts_response = supabase.table('water_districts').select('*').execute()
        districts_df = pd.DataFrame(districts_response.data)
        
        # Load counties
        counties_response = supabase.table('counties').select('*').execute()
        counties_df = pd.DataFrame(counties_response.data)

        # ---- Cities Data ----
        cities_data = supabase.table("cities").select("""
            id,
            name,
            apl_status,
            counties ( name ),
            water_districts ( name, budget, cities_served, apl_alignment, project_activity, internal_support ),
            cip_budget,
            sewer_budget,
            service_type
        """).execute()

        cities_df = pd.DataFrame(cities_data.data)
        cities_df['budget'] = ''
        cities_df['cities_served'] = ''
        cities_df['apl_alignment'] = ''
        cities_df['project_activity'] = ''
        cities_df['internal_support'] = ''
        for index, row in cities_df.iterrows(): 
            cities_df.loc[index, 'counties'] = row['counties']['name']
            cities_df.loc[index, 'water_districts'] = row['water_districts']['name']
            cities_df.loc[index, 'budget'] = row['water_districts']['budget']
            cities_df.loc[index, 'cities_served'] = row['water_districts']['cities_served']
            cities_df.loc[index, 'apl_alignment'] = row['water_districts']['apl_alignment']
            cities_df.loc[index, 'project_activity'] = row['water_districts']['project_activity']
            cities_df.loc[index, 'internal_support'] = row['water_districts']['internal_support']
        return cities_df, districts_df, counties_df

        
    except Exception as e:
        print(f"Error loading data from Supabase: {e}")
        # Return empty DataFrames as fallback
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_relationship_graph(cities_df, districts_df, counties_df):
    """Create interactive relationship visualization"""
    
    # Create network graph
    fig = go.Figure()
    
    # Color mapping for counties
    county_colors = {row['name']: row['color_code'] for _, row in counties_df.iterrows()}

    
    # Add district nodes
    for idx, district in districts_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[idx * 2],
            y=[5],
            mode='markers+text',
            marker=dict(size=30, color='purple'),
            text=district['name'],
            textposition='top center',
            name=district['name'],
            showlegend=False
        ))
    
    # Add city nodes and connections
    for idx, city in cities_df.iterrows():
        district_idx = districts_df[districts_df['name'] == city['water_districts']].index
        if len(district_idx) > 0:
            district_idx = district_idx[0]
            
            # Add connection line
            fig.add_trace(go.Scatter(
                x=[district_idx * 2, idx * 0.5],
                y=[5, 1],
                mode='lines',
                line=dict(color='gray', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add city node
        fig.add_trace(go.Scatter(
            x=[idx * 0.5],
            y=[1],
            mode='markers+text',
            marker=dict(
                size=20,
                color=county_colors.get(city['counties'], 'gray')
            ),
            text=city['name'],
            textposition='bottom center',
            name=city['name'],
            showlegend=False,
            hovertemplate=f"<b>{city['name']}</b><br>" +
                         f"County: {city['counties']}<br>" +
                         f"District: {city['water_districts']}<br>" +
                         f"APL: {city['apl_status']}<extra></extra>"
        ))
    
    fig.update_layout(
        title="North Texas Water Infrastructure Relationships",
        height=500,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode='closest'
    )
    
    return fig

def dashboard_main():
    """Main application logic"""
    
    # Header
    st.markdown('<h1 class="main-header">🏗️ AI Matrix Infrastructure Intelligence</h1>', unsafe_allow_html=True)
    st.markdown("### North Texas Water Infrastructure Ranking System (Demo)")
    
    # Sidebar
    with st.sidebar:
        # st.markdown("### 🔐 User Access")
        # user_email = st.text_input("Email", value="admin@armorock.com")
        # if st.button("Login"):
        #     st.success(f"Welcome, {user_email}")
        
        # st.markdown("---")
        st.markdown("### 🎯 Quick Filters")
        
        # Load data
        cities_df, districts_df, counties_df = load_data()
        selected_county = st.multiselect(
            "County",
            options=['All'] + list(cities_df['counties'].unique()),
            default=['All']
        )
        
        selected_district = st.multiselect(
            "Water District",
            options=['All'] + list(cities_df['water_districts'].unique()),
            default=['All']
        )
        
        selected_apl = st.multiselect(
            "APL Status",
            options=['All'] + list(cities_df['apl_alignment'].unique()),
            default=['All']
        )
        
        min_budget = st.slider(
            "Min Annual Budget ($M)",
            min_value=0,
            max_value=5000,
            value=0,
            step=10
        )
    
    # Apply filters
    filtered_cities = cities_df.copy()
    if 'All' not in selected_county:
        filtered_cities = filtered_cities[filtered_cities['counties'].isin(selected_county)]
    if 'All' not in selected_district:
        filtered_cities = filtered_cities[filtered_cities['water_districts'].isin(selected_district)]
    if 'All' not in selected_apl:
        filtered_cities = filtered_cities[filtered_cities['apl_status'].isin(selected_apl)]
    filtered_cities = filtered_cities[filtered_cities['budget'] >= min_budget * 1_000_000]
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🗺️ Relationships", "🏆 Rankings", "📈 Analytics"])
    
    with tab1:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cities", len(filtered_cities))
        with col2:
            st.metric("Avg Annual Budget", f"${districts_df['budget'].mean()/1_000_000:.1f}M")
        with col3:
            approved_count = len(filtered_cities[filtered_cities['apl_status'] == 'Approved'])
            st.metric("APL Approved", approved_count)
        with col4:
            st.metric("Active Projects", districts_df['project_activity'].sum())
        
        st.markdown("---")
        
        # Ranking table with AI scores
        st.subheader("🤖 AI-Powered District Rankings")
        
        ranker = InfrastructureRanker()
        
        # Calculate scores for filtered cities
        districts_df['tier'] = 4
        districts_df['criteria'] = {}
        with st.spinner("Calculating AI scores..."):
            for idx, dist in districts_df.iterrows():
                dist_dict = dist.to_dict()
                result = ranker.calculate_district_score(dist_dict)
                districts_df.loc[idx, 'score'] = result["score"]
                districts_df.loc[idx, 'tier'] = result["tier"]
                districts_df.loc[idx, 'criteria'] = json.dumps(result["breakdown"])
                

        filtered_cities = filtered_cities.merge(
            districts_df[['name', 'score', 'tier', 'criteria']],
            left_on="water_districts",
            right_on="name",
            how="left",
            suffixes=("", "_district")  # prevent score conflict
        )

        filtered_cities= filtered_cities.rename(columns={'name': 'city_name', 'counties':'County','budget':'annual_budget'})
        
        # Sort by score
        filtered_cities = filtered_cities.sort_values('score', ascending=False)
        
        # Display styled dataframe
        display_df = filtered_cities.drop(["id", "water_districts"], axis=1)
        new_cols = [" ".join(word.capitalize() for word in item.split("_")) for item in display_df.columns]
        display_df.columns = new_cols
        
        # Format currency columns
        display_df['Cip Budget'] = display_df['Cip Budget'].apply(lambda x: f"${x/1_000_000:.1f}M")
        display_df['Sewer Budget'] = display_df['Sewer Budget'].apply(lambda x: f"${x/1_000_000:.1f}M")
        display_df['Annual Budget'] = display_df['Annual Budget'].apply(lambda x: f"${x/1_000_000:.1f}M")
        
        # Apply tier coloring
        def highlight_tier(row):
            tier = row['Tier']
            if tier == 1:
                return ['background-color: #48bb78; color: white'] * len(row)
            elif tier == 2:
                return ['background-color: #4299e1; color: white'] * len(row)
            elif tier == 3:
                return ['background-color: #ed8936; color: white'] * len(row)
            else:
                return ['background-color: #f56565; color: white'] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_tier, axis=1),
            use_container_width=True,
            height=400,
            column_order = ["Name District", "City Name", "County","Annual Budget", 'Apl Alignment', 'Project Activity' 
                'Internal Support','Score','Tier']
        )
    
    with tab2:
        st.subheader("🗺️ Infrastructure Relationship Map")
        
        relationship_fig = create_relationship_graph_v2(display_df, districts_df, counties_df)
        st.plotly_chart(relationship_fig, use_container_width=True)
        
        
    with tab3:
        st.subheader("🏆 District Rankings")
        # District ranking table
        display_df['Tier'] = pd.cut(
            display_df['Score'],
            bins=[0, 70, 85, 95, 100],
            labels=[4, 3, 2, 1]
        )
        
        st.dataframe(
            districts_df[['name', 'budget', 'cities_served', 'apl_alignment','project_activity', 'internal_support', 'score']].style.format({
                'annual_budget': '${:,.0f}'
            }),
            use_container_width=True
        )
        
        # Bar chart of district budgets
        fig_budget = px.bar(
            districts_df,
            x='name',
            y='budget',
            title='Water District Annual Budgets',
            labels={'budget': 'Annual Budget ($)', 'name': 'District'},
            color='apl_alignment'
        )
        st.plotly_chart(fig_budget, use_container_width=True)
    
    with tab4:
        st.subheader("📈 Analytics & Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # APL Status distribution
            apl_fig = px.pie(
                filtered_cities,
                names='apl_status',
                title='APL Status Distribution',
                color_discrete_map={
                    'Approved': '#48bb78',
                    'Verified': '#4299e1',
                    'Pending': '#ed8936',
                    'Needs Submission': '#f56565',
                    'Not Submitted': '#718096'
                }
            )
            st.plotly_chart(apl_fig, use_container_width=True)
        
        with col2:
            # Budget vs Score scatter
            scatter_fig = px.scatter(
                display_df,
                x='Annual Budget',
                y='Score',
                # size='Cities Served',
                color='Tier',
                title='Annual Budget vs AI Score',
                labels={'Annual Budget': 'Annual Budget ($)', 'Score': 'AI Score'},
                hover_data=['Name District', 'Apl Alignment']
            )
            st.plotly_chart(scatter_fig, use_container_width=True)
        

# if __name__ == "__main__":
#     main()
