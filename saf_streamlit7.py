import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
import statsmodels.api as sm

# --- Layout ---
st.set_page_config(layout="wide", page_title="Climate-Tech Hidden Champions Dashboard")
st.title("U.S. County Climate-Tech Dashboard (Version 1.0 — Arun Das)")

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("county_master_geoid.csv", dtype=str)
    
    # Force numeric where possible
    numeric_cols = [
        "gdp", "population", "airport_count",
        "enplanements", "passengers", "departures",
        "arrivals", "freight", "mail",
        "Sustainable_Aviation_Fuels_degree_centrality",
        "SAF_FIRM_COUNT"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Create county_state field
    df["county_state"] = df["COUNTY_NAME"] + ", " + df["STATE_NAME"]

    # Load shapefile
    gdf = gpd.read_file("cb_2022_us_county_5m.shp")
    gdf["GEOID"] = (gdf["STATEFP"] + gdf["COUNTYFP"]).astype(str).str.zfill(5)

    return df, gdf, numeric_cols

df, gdf, numeric_cols = load_data()

# --- Tabs ---
tabs = st.tabs(["Overview", "Scatterplots", "Choropleth Map"])

# =====================
# OVERVIEW TAB
# =====================
with tabs[0]:
    st.header("Study Overview")
    st.markdown("""
    This dashboard is designed as a **policy-relevant study tool** for exploring how 
    different U.S. counties contribute to the development of **climate technologies**.  

    While this prototype focuses on **Sustainable Aviation Fuels (SAF)**, the same framework 
    can be applied to **other climate technologies** such as **biomass, carbon capture and storage (CCS), and hydrogen**.  
    These appear in the dropdowns as **“Coming Soon”** to demonstrate the extensibility of the platform.  

    **Prepared by:** Arun Das  
    **Version:** 1.0  

    ---
    ### Goals
    - Identify **hidden champions**: counties that play outsized roles in SAF ecosystems.  
    - Analyze correlations between **economic, demographic, and transport factors** (GDP, population, airports, traffic) and SAF development.  
    - Provide insights for **climate policy targeting** at the county level.  
    - Build a **generalizable tool** that can later compare SAF to hydrogen, CCS, biomass, and more.  

    ---
    ### Next Steps
    - Integrate **policy databases** to test what interventions drive success.  
    - Run **cross-technology comparisons** (SAF vs hydrogen vs CCS).  
    - Provide **recommendations to policymakers** about where investment delivers the greatest returns.  
    """)

    # Hidden champions table
    st.subheader("Hidden Champions (SAF Prototype)")
    hidden_champions = df.sort_values(
        "Sustainable_Aviation_Fuels_degree_centrality", ascending=False
    ).head(25)[[
        "county_state", "gdp", "population", "airport_count",
        "Sustainable_Aviation_Fuels_degree_centrality", "SAF_FIRM_COUNT"
    ]]
    st.dataframe(hidden_champions, use_container_width=True, height=400)
    st.markdown("""
    **Explanation:**  
    These are the counties with the **highest SAF centrality scores**.  
    They represent *hidden champions* because they may not be the richest or most populous counties, 
    but they play a critical role in SAF innovation networks.  

    In future iterations, similar lists will highlight **hidden champions in hydrogen, CCS, biomass, and other climate technologies**.  
    """)

# =====================
# SCATTERPLOT TAB
# =====================
with tabs[1]:
    st.header("Scatterplot Analysis")

    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Select X-axis", numeric_cols, index=numeric_cols.index("gdp"))
    with col2:
        y_col = st.selectbox("Select Y-axis", numeric_cols, index=numeric_cols.index("Sustainable_Aviation_Fuels_degree_centrality"))

    plot_df = df[[x_col, y_col, "county_state"]].dropna()

    # Fit regression line
    X = sm.add_constant(plot_df[x_col])
    model = sm.OLS(plot_df[y_col], X).fit()
    slope = model.params[x_col] if x_col in model.params else None

    fig = px.scatter(
        plot_df,
        x=x_col,
        y=y_col,
        hover_name="county_state",
        trendline="ols",
        labels={x_col: x_col.upper(), y_col: y_col.upper()},
        title=f"{y_col.upper()} vs. {x_col.upper()}"
    )
    st.plotly_chart(fig, use_container_width=True)

    if slope is not None and not pd.isnull(slope):
        st.markdown(f"**Regression slope:** {slope:.4f}")
    st.markdown("""
    **Interpretation:**  
    - The scatterplot highlights relationships between county-level metrics.  
    - The **OLS regression line** provides insight into correlations.  
    - Counties that sit **far above the regression line** often represent **hidden champions**.  
    """)

# =====================
# CHOROPLETH MAP TAB
# =====================
with tabs[2]:
    st.header("Choropleth Map")

    # Add "coming soon" placeholders
    metric_options = {
        "Sustainable_Aviation_Fuels_degree_centrality": "SAF Centrality",
        "gdp": "GDP",
        "population": "Population",
        "airport_count": "Airport Count",
        "enplanements": "Enplanements",
        "passengers": "Passengers",
        "departures": "Departures",
        "arrivals": "Arrivals",
        "freight": "Freight",
        "mail": "Mail",
        "biomass": "Biomass (Coming Soon)",
        "ccs": "CCS (Coming Soon)",
        "hydrogen": "Hydrogen (Coming Soon)"
    }

    selected_key = st.selectbox("Select map metric", list(metric_options.keys()),
                                format_func=lambda x: metric_options[x])

    if "Coming Soon" in metric_options[selected_key]:
        st.info(f"{metric_options[selected_key]} not available yet. This demo shows SAF, but the tool is generalizable to all climate techs.")
    else:
        merged = gdf.merge(df, on="GEOID", how="left").dropna(subset=[selected_key])

        hover_data = {
            "county_state": True,
            "gdp": True,
            "population": True,
            "airport_count": True,
            "Sustainable_Aviation_Fuels_degree_centrality": True,
            "departures": True,
            "arrivals": True,
            "passengers": True,
            "enplanements": True,
            "freight": True,
            "mail": True
        }

        fig = px.choropleth_mapbox(
            merged,
            geojson=json.loads(merged.to_json()),
            locations=merged.index,
            color=selected_key,
            hover_name="county_state",
            hover_data=hover_data,
            mapbox_style="carto-positron",
            zoom=3,
            center={"lat": 37.8, "lon": -96},
            opacity=0.85,
            color_continuous_scale="Viridis",
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Interpretation:**  
        - Darker colors represent higher intensity of the selected metric.  
        - Hovering reveals **county-level context** (GDP, population, airports, SAF centrality, and traffic).  
        - In the future, maps for **hydrogen, CCS, and biomass** will help policymakers compare across technologies.  
        """)
