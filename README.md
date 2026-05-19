# 🛰️ Space-AI: Operational 2D Remote Sensing Vegetation Water Stress Monitor

An operational, cloud-native geospatial dashboard designed for environmental monitoring and biosphere anomaly detection. This system processes multi-spectral **Sentinel-2** satellite imagery data to identify, calculate, and visualize vegetation water stress and drought risk index anomalies. 

To handle large-scale datasets efficiently, the application aggregates hundreds of thousands of individual data pixels into high-resolution **2D Hexagonal Bins (Hexagonal Grid)** using an interactive mapping engine.

---

## 🚀 Key Features

- **Interactive 2D Hexagonal Binning:** Uses `PyDeck` to aggregate dense point layers into clean, customizable hex grids, eliminating overplotting and showcasing average stress probabilities natively.
- **Dynamic Filtering:** Real-time UI control via Streamlit sliders to adjust anomaly probability cutoffs.
- **Production-Ready Geospatial Architecture:** Dual-environment design configured to read from local PostGIS containers or serverless cloud databases securely.
- **Operational KPI Metrics:** Instantly displays scanned pixel counts, active anomaly volumes, and area degradation rates.

---

## 🛠️ Technology Stack

- **Frontend & UI:** `Streamlit` (Python)
- **Geospatial Mapping Engine:** `PyDeck` (deck.gl wrapper)
- **Database:** `PostgreSQL` + `PostGIS` (Geospatial Extension)
- **Cloud Database Hosting:** `Neon.tech` (Serverless Postgres with Connection Pooling)
- **Object-Relational Mapping:** `SQLAlchemy`

---

## 📦 Project Structure

```text
├── app.py               # Main Streamlit dashboard source code
├── requirements.txt     # Python dependency specifications
├── .gitignore           # Specifies intentionally untracked files to ignore
└── README.md            # Project documentation and guide
