import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

silver_data_path = "data/silver/weather_silver.csv"

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
# Remplace "ton_mot_de_passe" par ton vrai mot de passe
user = "postgres"
password = quote_plus("ton_mot_de_passe")  # Échappe les caractères spéciaux s'il y en a
host = "localhost"
port = "5432"
db = "weather_db"

# Utilisation de psycopg (v3) sans problème d'encodage Windows
DB_URL = "postgresql+psycopg://weather_user:weather_password@localhost:5432/weather_db"

def categorer_precipitation(precip):
    if precip >= 25:
        return "fortes pluies"
    elif precip >= 5:
        return "pluie moderee"
    else:
        return "faibles pluies"

def categorer_wind(wind):
    if wind >= 50:
        return "Vent violent"
    elif wind >= 30:
        return "Vent modéré"
    else:
        return "Calme"

def calculer_risque_score(ligne):
    score = 0
    # Précipitations (max 40)
    p = ligne["precipitation_sum"]
    if p >= 25:
        score += 40
    elif p >= 10:
        score += 20

    # Rafales de vent (max 30)
    gusts = ligne["wind_gusts_max"]
    if gusts >= 70:
        score += 30
    elif gusts >= 45:
        score += 15

    # Vent moyen (max 15)
    wind = ligne["wind_speed_max"]
    if wind > 50:
        score += 15
    elif wind >= 30:
        score += 7.5

    # Température extrême (max 15)
    temp = ligne["temperature_max"]
    if temp > 40 or temp < 2:
        score += 15
    elif temp >= 35:
        score += 7.5

    return min(score, 100)

def niveau_risque(score):
    if score >= 80:
        return "critique"
    elif score >= 50:
        return "eleve"
    elif score >= 35:
        return "modere"
    else:
        return "faible"

def run_gold_pipeline():
    # 1. Lecture du fichier Silver
    if not os.path.exists(silver_data_path):
        raise FileNotFoundError(f"Le fichier {silver_data_path} n'existe pas.")

    df = pd.read_csv(silver_data_path)

    # 2. Enrichissement des données métier
    df["temp_category"] = df["temperature_max"].apply(categorer_temperature)
    df["precip_category"] = df["precipitation_sum"].apply(categorer_precipitation)
    df["wind_category"] = df["wind_speed_max"].apply(categorer_wind)

    df["risk_score"] = df.apply(calculer_risque_score, axis=1)
    df["risk_level"] = df["risk_score"].apply(niveau_risque)

    # 3. Sauvegarde locale Gold
    os.makedirs("data/gold", exist_ok=True)
    df.to_csv("data/gold/weather_gold.csv", index=False)
    print("Données Gold sauvegardées localement dans data/gold/weather_gold.csv")

    # 4. Chargement PostgreSQL
    print("Chargement des données Gold dans PostgreSQL...")
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        # A. Upsert des Villes
        cities_df = df[["city", "latitude", "longtitude"]].drop_duplicates()
        cities_records = [
            {"city": row["city"], "lat": row["latitude"], "lng": row["longtitude"]}
            for _, row in cities_df.iterrows()
        ]

        query_cities = text("""
            INSERT INTO dim_cities (city_name, lat, lng)
            VALUES (:city, :lat, :lng)
            ON CONFLICT (city_name) DO UPDATE 
            SET lat = EXCLUDED.lat, lng = EXCLUDED.lng;
        """)
        conn.execute(query_cities, cities_records)

        # B. Récupération des city_id
        cities_map = pd.read_sql(text("SELECT city_id, city_name FROM dim_cities"), conn)
        df_final = df.merge(cities_map, left_on="city", right_on="city_name")

        # C. Upsert des Prévisions Métaphoriques (fact_weather_forecasts)
        query_fact = text("""
            INSERT INTO fact_weather_forecasts (
                city_id, forecast_date, temp_max, temp_min, precipitation_sum,
                precipitation_probability_max, wind_speed_max, wind_gusts_max,
                weather_code, risk_score, risk_level
            ) VALUES (
                :city_id, :forecast_date, :temp_max, :temp_min, :precipitation_sum,
                :precipitation_probability_max, :wind_speed_max, :wind_gusts_max,
                :weather_code, :risk_score, :risk_level
            )
            ON CONFLICT (city_id, forecast_date) DO UPDATE SET
                temp_max = EXCLUDED.temp_max,
                temp_min = EXCLUDED.temp_min,
                precipitation_sum = EXCLUDED.precipitation_sum,
                precipitation_probability_max = EXCLUDED.precipitation_probability_max,
                wind_speed_max = EXCLUDED.wind_speed_max,
                wind_gusts_max = EXCLUDED.wind_gusts_max,
                weather_code = EXCLUDED.weather_code,
                risk_score = EXCLUDED.risk_score,
                risk_level = EXCLUDED.risk_level,
                updated_at = CURRENT_TIMESTAMP;
        """)

        # Mappage des colonnes du DataFrame vers les paramètres SQL
        fact_records = []
        for _, row in df_final.iterrows():
            fact_records.append({
                "city_id": int(row["city_id"]),
                "forecast_date": str(row["date"]),
                "temp_max": float(row["temperature_max"]),
                "temp_min": float(row["temperature_min"]),
                "precipitation_sum": float(row["precipitation_sum"]),
                "precipitation_probability_max": float(row["precipitation_probability_max"]),
                "wind_speed_max": float(row["wind_speed_max"]),
                "wind_gusts_max": float(row["wind_gusts_max"]),
                "weather_code": int(row["weather_code"]),
                "risk_score": float(row["risk_score"]),
                "risk_level": str(row["risk_level"])
            })

        # Insertion groupée (Batch Insert)
        conn.execute(query_fact, fact_records)

    print("Pipeline Gold exécuté et données chargées avec succès !")

if __name__ == "__main__":
    run_gold_pipeline()