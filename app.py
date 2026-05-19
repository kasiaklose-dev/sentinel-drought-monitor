# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st
import pydeck as pdk
from sqlalchemy import create_engine

st.set_page_config(page_title="Teledetekcja: Monitor Stresu", layout="wide")

# Konfiguracja połączenia z obsługą SSL
if "postgres" in st.secrets:
    db = st.secrets["postgres"]
    DB_URL = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?sslmode=require"
else:
    DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5434/db")

@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_size=5, max_overflow=10)

# OPTYMALIZACJA: Agregacja w bazie danych (zamiast pobierać miliony punktów)
@st.cache_data(ttl=600) # Cache danych na 10 minut
def load_data(threshold):
    engine = get_engine()
    # Pobieramy tylko to, co potrzebne, filtrując już w SQL
    query = f"""
        SELECT 
            ST_Y(ST_Transform(geometry, 4326)) as lat, 
            ST_X(ST_Transform(geometry, 4326)) as lon,
            drought_probability_pct as stress
        FROM predictions_drought 
        WHERE drought_probability_pct >= {threshold} 
        AND predicted_drought_risk = 1
        LIMIT 50000; -- Bezpieczny limit dla płynności PyDeck
    """
    return pd.read_sql(query, engine)

def main():
    st.title("🛰️ System Monitorowania Stresu Wodnego")
    
    threshold = st.sidebar.slider("Minimalne prawdopodobieństwo stresu (%)", 0.0, 100.0, 50.0)
    
    # Dane ładują się tylko przy zmianie suwaka
    df = load_data(threshold)
    
    # Mapa z wyłączonym "pickable" dla wydajności przy dużej ilości punktów
    layer = pdk.Layer(
        "HexagonLayer",
        df,
        get_position=["lon", "lat"],
        radius=150,
        elevation_scale=0,
        pickable=False, # Wyłączenie interakcji wewnątrz mapy drastycznie przyspiesza renderowanie
        color_range=[[255, 237, 160], [240, 59, 32], [189, 0, 38]],
        get_color_weight="stress",
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=df.lat.mean() if not df.empty else 52.0, longitude=df.lon.mean() if not df.empty else 19.0, zoom=10),
        map_style="mapbox://styles/mapbox/light-v10" # Szybsze mapy niż CartoDB
    ))

if __name__ == "__main__":
    main()
