import pandas as pd
from sqlalchemy import create_engine, text

# Configuration PostgreSQL
user = "postgres"
password = "votre_mot_de_passe"
host = "127.0.0.1"
port = "5433"
db = "weather_db"

DB_URL = f"postgresql+pg8000://{user}:{password}@{host}:{port}/{db}"

def get_engine():
    return create_engine(DB_URL)

def save_gold_to_db(df: pd.DataFrame):
    engine = get_engine()

    with engine.begin() as conn:
        # 1. Insertion des villes
        cities_df = df[["city", "lat", "lng"]].drop_duplicates()

        query_cities = text("""
            INSERT INTO dim_cities (city_name, lat, lng)
            VALUES (:city, :lat, :lng)
            ON CONFLICT (city_name) DO UPDATE
            SET lat = EXCLUDED.lat,
                lng = EXCLUDED.lng;
        """)

        cities_records = [
            {
                "city": str(row["city"]),
                "lat": float(row["lat"]),
                "lng": float(row["lng"])
            }
            for _, row in cities_df.iterrows()
        ]

        conn.execute(query_cities, cities_records)

        # 2. Récupération des IDs
        cities_map = pd.read_sql(
            text("SELECT city_id, city_name FROM dim_cities"),
            conn
        )

        df_merged = df.merge(
            cities_map,
            left_on="city",
            right_on="city_name"
        )

        # 3. Insertion des données météo
        query_fact = text("""
            INSERT INTO fact_weather_forecasts (
                city_id,
                forecast_date,
                temp_max,
                temp_min,
                precipitation_sum,
                precipitation_probability_max,
                wind_speed_max,
                wind_gusts_max,
                weather_code,
                risk_score,
                risk_level
            )
            VALUES (
                :city_id,
                :forecast_date,
                :temp_max,
                :temp_min,
                :precipitation_sum,
                :precipitation_probability_max,
                :wind_speed_max,
                :wind_gusts_max,
                :weather_code,
                :risk_score,
                :risk_level
            )
            ON CONFLICT (city_id, forecast_date)
            DO UPDATE SET
                temp_max = EXCLUDED.temp_max,
                temp_min = EXCLUDED.temp_min,
                precipitation_sum = EXCLUDED.precipitation_sum,
                wind_speed_max = EXCLUDED.wind_speed_max,
                wind_gusts_max = EXCLUDED.wind_gusts_max,
                weather_code = EXCLUDED.weather_code,
                risk_score = EXCLUDED.risk_score,
                risk_level = EXCLUDED.risk_level,
                updated_at = CURRENT_TIMESTAMP;
        """)

        fact_records = []

        for _, row in df_merged.iterrows():
            fact_records.append({
                "city_id": int(row["city_id"]),
                "forecast_date": str(row["date"]),
                "temp_max": float(row["temperature_max"]),
                "temp_min": float(row["temperature_min"]),
                "precipitation_sum": float(row["precipitation_sum"]),
                "precipitation_probability_max": int(
                 float(row.get("precipitation_probability_max", 0))

                ),
                "wind_speed_max": float(row["wind_speed_max"]),
                "wind_gusts_max": float(row["wind_gusts_max"]),
                "weather_code": int(row.get("weather_code", 0)),
                "risk_score": float(row["risk_score"]),
                "risk_level": str(row["risk_level"])
            })

        conn.execute(query_fact, fact_records)

        print("Chargement PostgreSQL réussi sans erreur !")