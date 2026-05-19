# -*- coding: utf-8 -*-
"""
Space-AI: Operacyjny System Monitorowania Stresu Wodnego Roślinności
Wizualizacja anomalii wegetacyjnych za pomocą płaskiej agregacji heksagonalnej 2D.
"""

import os
import pandas as pd
import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# ==========================================
# 1. KONFIGURACJA ŚRODOWISKA I INTERFEJSU
# ==========================================
st.set_page_config(
    page_title="Teledetekcja: Monitor Stresu Wodnego", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dynamiczne wykrywanie środowiska (Streamlit Cloud Secrets vs Lokalny Docker)
if "postgres" in st.secrets:
    db_config = st.secrets["postgres"]
    DB_URL = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
else:
    # Lokalny fallback dla kontenera lokalnego
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
# 2. GŁÓWNY POTOK URUCHOMIENIOWY
# ==========================================
def main() -> None:
    st.markdown("<p style='color:#2E7D32; font-size:13px; font-weight:bold; letter-spacing:1px; margin-bottom:0;'>STACJA PRZETWARZANIA DANYCH GEOPRZESTRZENNYCH</p>", unsafe_allow_html=True)
    st.title("🛰️ System Monitorowania Stresu Wodnego Roślinności")
    st.markdown("Agregacja przestrzenna anomalii biosferycznych na podstawie zobrazowań spektralnych misji **Sentinel-2**.")
    st.markdown("---")
    
    try:
        df = load_geospatial_features()
        
        st.sidebar.header("⚙️ Parametry Filtrowania")
        threshold = st.sidebar.slider(
            "Pokaż punkty o prawdopodobieństwie stresu wyższym niż (%)", 
            0.0, 100.0, 50.0
        )
        
        # Filtrowanie wejściowe danych dla modelu wegetacji
        filtered_df = df[(df['stress_probability'] >= threshold) & (df['anomaly_class'] == 1)]
        anomaly_rate = (len(filtered_df) / (len(df) + 1e-5)) * 100
        
        # Statystyki globalne KPI
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="Całkowita liczba pikseli (Skan)", value=f"{len(df):,}".replace(",", " "))
        with c2:
            st.metric(label="Piksele w stanie aktywnego stresu", value=f"{len(filtered_df):,}".replace(",", " "))
        with c3:
            st.metric(label="Wskaźnik degradacji obszaru", value=f"{anomaly_rate:.2f} %")
        st.markdown("---")
        
        col_left, col_right = st.columns([2.5, 1.5])
        
        with col_left:
            st.subheader("🗺️ Siatka Heksagonalna Zagęszczenia Anomalii (Mapa 2D)")
            
            hexagon_layer = pdk.Layer(
                "HexagonLayer",
                data=filtered_df,
                get_position=["longitude", "latitude"],
                radius=150,
                elevation_scale=0,
                extruded=False,
                pickable=True,
                opacity=0.6,
                color_range=[
                    [255, 237, 160],
                    [254, 217, 118],
                    [254, 178, 76],
                    [253, 141, 60],
                    [240, 59, 32],
                    [189, 0, 38]
                ],
                # Wymuszenie jawnego, bezbłędnego liczenia średniej matematycznej z punktów (0-100%)
                get_color_value="[-] => points.reduce((sum, p) => sum + p.stress_probability, 0) / points.length",
            )
            
            view_state = pdk.ViewState(
                latitude=df['latitude'].mean() if not df.empty else 52.0,
                longitude=df['longitude'].mean() if not df.empty else 19.0,
                zoom=11.5,
                pitch=0
            )
            
            # Zmiana na oficjalny i stabilny serwer mapowy CartoDB (Jasny styl bez błędów w Pydeck)
            st.pydeck_chart(pdk.Deck(
                layers=[hexagon_layer],
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                tooltip={"text": "Średnie nasilenie stresu w komórce: {colorValue:.1f}%"}
            ))
            
        with col_right:
            st.subheader("📋 Surowy Rejestr Teledetekcyjny (Top 100)")
            
            table_df = filtered_df[['ndvi', 'stress_probability', 'anomaly_class']].copy()
            table_df.columns = ['Wskaźnik NDVI', 'Prawdopodobieństwo Stresu', 'Klasa Anomalii (0/1)']
            table_df['Wskaźnik NDVI'] = table_df['Wskaźnik NDVI'].round(4)
            table_df['Prawdopodobieństwo Stresu'] = table_df['Prawdopodobieństwo Stresu'].map('{:.2f}%'.format)
            
            st.dataframe(table_df.head(100), use_container_width=True, height=440)
            
    except Exception as err:
        st.error(f"🚨 Błąd krytyczny aplikacji: {err}")

if __name__ == "__main__":
    main()
