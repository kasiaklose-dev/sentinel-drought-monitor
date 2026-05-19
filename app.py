# -*- coding: utf-8 -*-
"""
Space-AI: Operacyjny System Monitorowania Stresu Wodnego Roślinności
"""

import os
import pandas as pd
import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# ==========================================
# 1. KONFIGURACJA ŚRODOWISKA
# ==========================================
st.set_page_config(
    page_title="Teledetekcja: Monitor Stresu Wodnego", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ładowanie danych z sekretów (Cloud) lub środowiska (Lokalnie)
if "postgres" in st.secrets:
    db_config = st.secrets["postgres"]
    # Kluczowa zmiana: dodanie ?sslmode=require dla bezpieczeństwa Neon.tech
    DB_URL = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?sslmode=require"
else:
    DB_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://geospatial_user:geospatial_password@127.0.0.1:5434/geospatial_db"
    )

@st.cache_resource
def get_connection_engine() -> Engine:
    return create_engine(DB_URL, connect_args={'client_encoding': 'utf8'})

@st.cache_data
def load_geospatial_features() -> pd.DataFrame:
    engine = get_connection_engine()
    query = """
        SELECT 
            predicted_drought_risk AS anomaly_class, 
            drought_probability_pct AS stress_probability, 
            ndvi_value AS ndvi,
            ST_Y(ST_Transform(geometry, 4326)) AS latitude,
            ST_X(ST_Transform(geometry, 4326)) AS longitude
        FROM predictions_drought;
    """
    return pd.read_sql(query, con=engine)

# ==========================================
# 2. GŁÓWNY INTERFEJS
# ==========================================
def main() -> None:
    st.markdown("<p style='color:#2E7D32; font-size:13px; font-weight:bold; letter-spacing:1px; margin-bottom:0;'>STACJA PRZETWARZANIA DANYCH GEOPRZESTRZENNYCH</p>", unsafe_allow_html=True)
    st.title("🛰️ System Monitorowania Stresu Wodnego Roślinności")
    st.markdown("Agregacja przestrzenna anomalii biosferycznych na podstawie zobrazowań spektralnych misji **Sentinel-2**.")
    st.markdown("---")
    
    try:
        df = load_geospatial_features()
        
        st.sidebar.header("⚙️ Parametry Filtrowania")
        threshold = st.sidebar.slider("Pokaż punkty o prawdopodobieństwie stresu wyższym niż (%)", 0.0, 100.0, 50.0)
        
        filtered_df = df[(df['stress_probability'] >= threshold) & (df['anomaly_class'] == 1)]
        anomaly_rate = (len(filtered_df) / (len(df) + 1e-5)) * 100
        
        # KPI
        c1, c2, c3 = st.columns(3)
        c1.metric("Całkowita liczba pikseli", f"{len(df):,}".replace(",", " "))
        c2.metric("Piksele w stanie stresu", f"{len(filtered_df):,}".replace(",", " "))
        c3.metric("Wskaźnik degradacji", f"{anomaly_rate:.2f} %")
        st.markdown("---")
        
        col_left, col_right = st.columns([2.5, 1.5])
        
        with col_left:
            st.subheader("🗺️ Mapa Stresu Wodnego (Hex Grid)")
            
            hexagon_layer = pdk.Layer(
                "HexagonLayer",
                data=filtered_df,
                get_position=["longitude", "latitude"],
                radius=150,
                elevation_scale=0,
                extruded=False,
                pickable=True,
                opacity=0.6,
                color_range=[[255, 237, 160], [254, 217, 118], [254, 178, 76], [253, 141, 60], [240, 59, 32], [189, 0, 38]],
                get_color_value="[-] => points.reduce((sum, p) => sum + p.stress_probability, 0) / points.length",
            )
            
            view_state = pdk.ViewState(
                latitude=df['latitude'].mean() if not df.empty else 52.0,
                longitude=df['longitude'].mean() if not df.empty else 19.0,
                zoom=11.5,
                pitch=0
            )
            
            st.pydeck_chart(pdk.Deck(
                layers=[hexagon_layer],
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                tooltip={"text": "Średnie nasilenie stresu w komórce: {colorValue:.1f}%"}
            ))
            
        with col_right:
            st.subheader("📋 Rejestr (Top 100)")
            table_df = filtered_df[['ndvi', 'stress_probability']].copy()
            table_df.columns = ['NDVI', 'Prawdopodobieństwo Stresu']
            table_df['Prawdopodobieństwo Stresu'] = table_df['Prawdopodobieństwo Stresu'].map('{:.2f}%'.format)
            st.dataframe(table_df.head(100), use_container_width=True, height=440)
            
    except Exception as err:
        st.error(f"🚨 Błąd aplikacji: {err}")

if __name__ == "__main__":
    main()
