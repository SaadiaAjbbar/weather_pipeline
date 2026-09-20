import os

import pandas as pd
import psycopg2
import streamlit as st


st.set_page_config(
    page_title="Morocco Weather Pipeline",
    layout="wide"
)

st.title("🌤️ Weather Data Dashboard")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        database=os.getenv("POSTGRES_DB", "weather_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "votre_mot_de_passe"),
    )


try:
    conn = get_connection()

    query = """
        SELECT
            f.forecast_date,
            c.city_name,
            f.temp_max,
            f.temp_min,
            f.precipitation_sum,
            f.wind_speed_max,
            f.wind_gusts_max,
            f.risk_score,
            f.risk_level
        FROM fact_weather_forecasts f
        JOIN dim_cities c
            ON f.city_id = c.city_id
        ORDER BY f.forecast_date, c.city_name;
    """

    df = pd.read_sql(query, conn)
    conn.close()

    st.success("Connexion PostgreSQL réussie ✅")

    col1, col2, col3 = st.columns(3)

    col1.metric("Villes", df["city_name"].nunique())
    col2.metric("Prévisions", len(df))
    col3.metric("Risque moyen", round(df["risk_score"].mean(), 2))

    st.subheader("Prévisions météo")

    st.dataframe(
        df,
        use_container_width=True
    )

except Exception as e:
    st.error(f"Erreur de connexion à PostgreSQL : {e}")