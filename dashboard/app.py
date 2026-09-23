import psycopg2
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Weather Dashboard",
    layout="wide"
)

st.title("🌤️ Weather Dashboard")

conn = psycopg2.connect(
    host="postgres",
    port=5432,
    database="weather_db",
    user="postgres",
    password="votre_mot_de_passe"
)

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

df["forecast_date"] = pd.to_datetime(df["forecast_date"])

st.sidebar.header("Filtres")

cities = sorted(df["city_name"].unique())

selected_cities = st.sidebar.multiselect(
    "Ville",
    options=cities,
    default=cities
)

min_date = df["forecast_date"].min().date()
max_date = df["forecast_date"].max().date()

selected_dates = st.sidebar.date_input(
    "Période",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

risk_levels = [
    "faible",
    "modere",
    "eleve",
    "critique"
]

selected_risks = st.sidebar.multiselect(
    "Niveau de risque",
    options=risk_levels,
    default=risk_levels
)

filtered_df = df.copy()

if selected_cities:
    filtered_df = filtered_df[
        filtered_df["city_name"].isin(selected_cities)
    ]

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date = pd.Timestamp(selected_dates[0])
    end_date = pd.Timestamp(selected_dates[1])

    filtered_df = filtered_df[
        (filtered_df["forecast_date"] >= start_date) &
        (filtered_df["forecast_date"] <= end_date)
    ]

if selected_risks:
    filtered_df = filtered_df[
        filtered_df["risk_level"].isin(selected_risks)
    ]

st.subheader("Indicateurs clés")

if filtered_df.empty:
    st.warning("Aucune donnée ne correspond aux filtres.")
else:
    nombre_villes = filtered_df["city_name"].nunique()

    temperature_max = filtered_df["temp_max"].max()

    precipitation_max = filtered_df["precipitation_sum"].max()

    periodes_risque = (
        filtered_df["risk_level"] != "faible"
    ).sum()

    ligne_risque = filtered_df.loc[
        filtered_df["risk_score"].idxmax()
    ]

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Nombre de villes",
        nombre_villes
    )

    col2.metric(
        "Température maximale",
        f"{temperature_max:.1f} °C"
    )

    col3.metric(
        "Précipitations maximales",
        f"{precipitation_max:.1f} mm"
    )

    col4.metric(
        "Périodes à risque",
        periodes_risque
    )

    col5.metric(
        "Ville au risque le plus élevé",
        ligne_risque["city_name"]
    )

    st.subheader("Où et quand faut-il être vigilant ?")

    st.info(
        f"Ville : {ligne_risque['city_name']} | "
        f"Date : {ligne_risque['forecast_date'].date()} | "
        f"Score : {ligne_risque['risk_score']:.1f} | "
        f"Niveau : {ligne_risque['risk_level']}"
    )

    st.subheader("Prévisions météo")

    st.dataframe(
        filtered_df,
        use_container_width=True
    )