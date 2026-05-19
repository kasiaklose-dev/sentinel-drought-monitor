# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine

# Ustawienia strony dla szybszego renderowania
st.set_page_config(page_title="Monitor Stresu", layout="wide")

# Konfiguracja bazy
if "postgres" in st.secrets:
    db = st.secrets["postgres"]
    DB_URL = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?sslmode=require"
else:
    DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5434/db")

@st.cache_resource
def get_engine():
    # Używamy puli połączeń dla wydajności
    return create_engine(DB_URL, pool_size=5, max_overflow=10)

# OPTYMALIZACJA: Agregacja w bazie i cache na 1 godzinę
@st.cache_data(ttl=3600)
def load_data(threshold):
    engine = get_engine()
    # POBIERAMY TYLKO KOLUMNY KTÓRE SĄ POTRZEBNE
    query = f"""
        SELECT 
            ST_Y(ST_Transform(geometry, 4326)) as lat, 
            ST_X(ST_Transform(geometry, 4326)) as lon,
            drought_probability_pct as stress
        FROM predictions_drought 
        WHERE drought_probability_pct >= {threshold} 
        AND predicted_drought_risk = 1
        LIMIT 30000;
    """
    return pd.read_sql(query, engine)

def main():
    st.title("🛰️ System Monitorowania Stresu Wodnego")
    
    # Suwak nie powinien triggerować przeładowania całej aplikacji jeśli to możliwe
    threshold = st.sidebar.slider("Prawdopodobieństwo stresu (%)", 0.0, 100.0, 50.0)
    
    # Ładowanie danych
    df = load_data(threshold)
    
    if df.empty:
        st.warning("Brak danych dla wybranego progu.")
        return

    # Szybka mapa - wyłączamy extruded i pickable dla maksymalnej płynności
    layer = pdk.Layer(
        "HexagonLayer",
        df,
        get_position=["lon", "lat"],
        radius=200,
        elevation_scale=0,
        pickable=False, 
        extruded=False,
        color_range=[[255, 237, 160], [254, 217, 118], [240, 59, 32], [189, 0, 38]],
        get_color_weight="stress",
    )

    # Używamy statycznego widoku by nie obliczać go za każdym razem
    center_lat = df.lat.mean()
    center_lon = df.lon.mean()

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=10),
        map_style="mapbox://styles/mapbox/light-v9"
    ), use_container_width=True)

    st.caption(f"Wyświetlono {len(df)} rekordów.")

if __name__ == "__main__":
    main()
