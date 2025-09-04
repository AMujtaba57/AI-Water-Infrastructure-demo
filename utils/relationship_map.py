import plotly.graph_objects as go


def create_relationship_graph_v2(cities_df, districts_df, counties_df):
    """Create interactive relationship visualization similar to the attached image"""
    
    # Create a mapping of entities to coordinates
    # We'll organize in a hierarchical structure: Counties -> Water Districts -> Cities
    
    # Define layout parameters
    county_y = 10
    district_y = 7
    city_y = 4
    
    # Create figure
    fig = go.Figure()
    
    # Color mapping for counties
    county_colors = {row['name']: row['color_code'] for _, row in counties_df.iterrows()}
    
    # Add counties
    county_x_positions = {}
    for idx, county in enumerate(counties_df['name']):
        x_pos = idx * 5
        county_x_positions[county] = x_pos
        
        fig.add_trace(go.Scatter(
            x=[x_pos],
            y=[county_y],
            mode='markers+text',
            marker=dict(size=25, color=county_colors.get(county, 'gray')),
            text=county,
            textposition='top center',
            name=county,
            hovertemplate=f"<b>{county}</b><extra></extra>"
        ))
    
    # Add water districts with connections to counties
    district_x_positions = {}
    district_county_map = {}
    
    # Create a mapping of districts to counties based on cities served
    for _, city in cities_df.iterrows():
        if city['Name District'] and city['County']:
            district_county_map[city['Name District']] = city['County']
    
    # Position districts under their respective counties
    district_count = {}
    for idx, district in districts_df.iterrows():
        district_name = district['name']
        county_name = district_county_map.get(district_name)
        
        if county_name and county_name in county_x_positions:
            county_x = county_x_positions[county_name]
            
            # Count how many districts are already under this county
            if county_name not in district_count:
                district_count[county_name] = 0
            else:
                district_count[county_name] += 1
                
            x_pos = county_x - 2 + (district_count[county_name] * 1.5)
            district_x_positions[district_name] = x_pos
            
            # Add connection line from county to district
            fig.add_trace(go.Scatter(
                x=[county_x, x_pos],
                y=[county_y - 0.5, district_y + 0.5],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Add district node
            fig.add_trace(go.Scatter(
                x=[x_pos],
                y=[district_y],
                mode='markers+text',
                marker=dict(size=20, color='purple', symbol='square'),
                text=district_name,
                textposition='top center',
                name=district_name,
                hovertemplate=f"<b>{district_name}</b><br>" +
                             f"Budget: ${district.get('budget', 0)/1_000_000:.1f}M<br>" +
                             f"Cities Served: {district.get('cities_served', 0)}<extra></extra>"
            ))
    
    # Add cities with connections to districts
    city_count = {}
    for idx, city in cities_df.iterrows():
        city_name = city['City Name']
        district_name = city['Name District']
        county_name = city['County']
        
        if district_name and district_name in district_x_positions:
            district_x = district_x_positions[district_name]
            
            # Count how many cities are already under this district
            if district_name not in city_count:
                city_count[district_name] = 0
            else:
                city_count[district_name] += 1
                
            x_pos = district_x - 1 + (city_count[district_name] * 0.7)
            
            # Add connection line from district to city
            fig.add_trace(go.Scatter(
                x=[district_x, x_pos],
                y=[district_y - 0.5, city_y + 0.5],
                mode='lines',
                line=dict(color='lightgray', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Determine city color based on APL status
            city_color = 'gray'
            if city['Apl Alignment'] == 'STRONG':
                city_color = 'green'
            elif city['Apl Alignment'] == 'MODERATE':
                city_color = 'orange'
            elif city['Apl Alignment'] == 'UNKNOWN':
                city_color = 'blue'
            
            # Add city node
            fig.add_trace(go.Scatter(
                x=[x_pos],
                y=[city_y],
                mode='markers+text',
                marker=dict(size=15, color=city_color),
                text=city_name,
                textposition='bottom center',
                name=city_name,
                hovertemplate=f"<b>{city_name}</b><br>" +
                             f"County: {county_name}<br>" +
                             f"District: {district_name}<br>" +
                             f"APL: {city['Apl Alignment']}<extra></extra>"
            ))
    
    # Add legend for APL status
    fig.add_trace(go.Scatter(
        x=[-5], y=[-2],
        mode='markers',
        marker=dict(size=10, color='green'),
        name='APL Strong',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[-5], y=[-2],
        mode='markers',
        marker=dict(size=10, color='blue'),
        name='APL Moderate',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[-5], y=[-2],
        mode='markers',
        marker=dict(size=10, color='orange'),
        name='APL Unknown',
        showlegend=True
    ))
    
    
    fig.update_layout(
        title="North Texas Water Infrastructure Relationships",
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-7, 25]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 12]),
        hovermode='closest'
    )
    
    return fig