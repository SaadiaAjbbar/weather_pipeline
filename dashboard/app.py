import psycopg2
import pandas as pd
import streamlit as st

st.title("🌤️ Weather Dashboard")

# Connexion à PostgreSQL
conn = psycopg2.connect(
    host="postgres",
    port=5432,
    database="weather_db",
    user="postgres",
    password="votre_mot_de_passe"
)

# Récupérer les données
query = """
SELECT
    c.city_name,
    f.forecast_date,
    f.temp_max,
    f.temp_min,
    f.precipitation_sum,
    f.risk_score,
    f.risk_level
FROM fact_weather_forecasts f
JOIN dim_cities c
    ON f.city_id = c.city_id
ORDER BY f.forecast_date, c.city_name;
"""

df = pd.read_sql(query, conn)

conn.close()

st.subheader("Prévisions météo")

st.dataframe(df)