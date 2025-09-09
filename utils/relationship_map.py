import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

st.set_page_config(page_title="North Texas Mindmap", layout="wide")

st.title("North Texas Regional Relationships - Hierarchical Mind Map")
st.markdown("This interactive visualization shows counties, cities, water districts, and internal support structures.")

def create_hierarchical_mindmap(display_df, districts_df, counties_df):
    DATA = {"root": "North Texas Regional Relationships"}

    # Counties
    DATA["counties"] = counties_df["name"].unique().tolist()

    # APL Alignment
    DATA["apl_alignment"] = display_df["Apl Alignment"].dropna().unique().tolist()

    # Water Districts
    DATA["water_districts"] = districts_df["name"].unique().tolist()

    # Cities grouped by County
    DATA["cities"] = display_df.groupby("County")["City Name"].apply(list).to_dict()

    # Internal Support (group cities by support type)
    DATA["internal_support"] = (
        display_df.groupby("Internal Support")["Service Type"].unique().apply(list).to_dict()
    )

    # Relationships
    DATA["relationships"] = {}

    # city_to_water mapping
    DATA["relationships"]["city_to_water"] = [
        {"city": row["City Name"], "district": row["Name District"], "type": row["Service Type"]}
        for _, row in display_df.iterrows()
    ]

    G = nx.DiGraph()
    positions = {}
    node_colors = {}
    node_sizes = {}
    node_labels = {}

    root = DATA["root"]
    G.add_node(root)
    positions[root] = (0, 0)
    node_colors[root] = "#3498db"
    node_sizes[root] = 3000
    node_labels[root] = root

    categories = [
        ("counties", "#e74c3c", -1, 0),
        ("apl_alignment", "#2ecc71", 0, -1),
        ("water_districts", "#9b59b6", 1, 0),
        ("internal_support", "#1abc9c", 0, 1)
    ]

    for i, (category, color, _, _) in enumerate(categories):
        if category == "internal_support":
            for j, (dept, teams) in enumerate(DATA[category].items()):
                dept_id = f"{dept}"
                G.add_node(dept_id)
                G.add_edge(root, dept_id)
                angle = np.pi/2 + j * np.pi/4
                radius = 5
                positions[dept_id] = (radius * np.cos(angle), radius * np.sin(angle))
                node_colors[dept_id] = color
                node_sizes[dept_id] = 1500
                node_labels[dept_id] = dept

                for k, team in enumerate(teams):
                    team_id = f"{dept}_{team}"
                    G.add_node(team_id)
                    G.add_edge(dept_id, team_id)
                    team_angle = angle + (k - len(teams)/2) * 0.2
                    team_radius = radius + 3
                    positions[team_id] = (team_radius * np.cos(team_angle), team_radius * np.sin(team_angle))
                    node_colors[team_id] = "#16a085"
                    node_sizes[team_id] = 1000
                    node_labels[team_id] = team
        else:
            items = DATA[category]
            for j, item in enumerate(items):
                item_id = f"{category}_{item}"
                G.add_node(item_id)
                G.add_edge(root, item_id)

                if category == "counties":
                    angle = np.pi + j * np.pi/3
                elif category == "apl_alignment":
                    angle = 3*np.pi/2 + j * np.pi/4
                elif category == "water_districts":
                    angle = j * np.pi/3

                radius = 5
                positions[item_id] = (radius * np.cos(angle), radius * np.sin(angle))
                node_colors[item_id] = color
                node_sizes[item_id] = 1500
                node_labels[item_id] = item

                if category == "counties":
                    try:
                        cities = DATA["cities"][item]
                        for k, city in enumerate(cities):
                            city_id = f"{item}_{city}"
                            G.add_node(city_id)
                            G.add_edge(item_id, city_id)
                            city_angle = angle + (k - len(cities)/2) * 0.2
                            city_radius = radius + 3
                            positions[city_id] = (city_radius * np.cos(city_angle), city_radius * np.sin(city_angle))
                            node_colors[city_id] = "#f39c12"
                            node_sizes[city_id] = 1000
                            node_labels[city_id] = city
                    except Exception as e:
                        print('Error: ', e)

    # Draw figure
    fig, ax = plt.subplots(figsize=(16, 12))
    nx.draw_networkx_nodes(G, positions, node_size=[node_sizes[node] for node in G.nodes()],
                          node_color=[node_colors[node] for node in G.nodes()],
                          alpha=0.9, edgecolors='white', linewidths=2, ax=ax)

    nx.draw_networkx_edges(G, positions, edgelist=list(G.edges()), alpha=0.5, edge_color='gray', ax=ax)

    for node, (x, y) in positions.items():
        ax.annotate(node_labels[node], xy=(x, y), xytext=(0, 0), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", fc=node_colors[node], ec="white", alpha=0.9),
                    fontsize=9, color='white', weight='bold', ha='center', va='center')

    ax.axis('off')
    st.pyplot(fig)
