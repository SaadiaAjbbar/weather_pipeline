import os
import sys
from pathlib import Path
import pandas as pd

# Ajoute le dossier racine du projet au chemin Python
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.engineering.database import save_gold_to_db

silver_data_path = "data/silver/weather_silver.csv"


def categorer_temperature(tmp):
    if tmp >= 40:
        return "temperature eleve"
    elif tmp >= 30:
        return "temperature moderee"
    else:
        return "temperature bien"

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
    p = ligne["precipitation_sum"]
    if p >= 25:
        score += 40
    elif p >= 10:
        score += 20

    gusts = ligne["wind_gusts_max"]
    if gusts >= 70:
        score += 30
    elif gusts >= 45:
        score += 15

    wind = ligne["wind_speed_max"]
    if wind > 50:
        score += 15
    elif wind >= 30:
        score += 7.5

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
    if not os.path.exists(silver_data_path):
        raise FileNotFoundError(f"Le fichier {silver_data_path} n'existe pas.")

    df = pd.read_csv(silver_data_path)
    df = df.rename(columns={
    "latitude": "lat",
    "longtitude": "lng"
    })

    # Application des règles métier
    df["temp_category"] = df["temperature_max"].apply(categorer_temperature)
    df["precip_category"] = df["precipitation_sum"].apply(categorer_precipitation)
    df["wind_category"] = df["wind_speed_max"].apply(categorer_wind)

    df["risk_score"] = df.apply(calculer_risque_score, axis=1)
    df["risk_level"] = df["risk_score"].apply(niveau_risque)

    # Sauvegarde locale Gold
    os.makedirs("data/gold", exist_ok=True)
    df.to_csv("data/gold/weather_gold.csv", index=False)
    print("Données Gold sauvegardées localement dans data/gold/weather_gold.csv")

    # Insertion en base de données via database.py
    print("Chargement des données dans PostgreSQL...")
    save_gold_to_db(df)
    print("Pipeline Gold exécuté avec succès !")

if __name__ == "__main__":
    run_gold_pipeline()