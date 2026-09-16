import os 
import pandas as pd
import numpy as np
import requests
import time
import json

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration des chemins de fichiers
RAW_CITIES_PATH = "data/raw_cities.csv"
BRONZE_DIR = "data/bronze"

# Configuration API Open-Meteo
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_PARAMS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "weather_code"
]

#reload connection 3 fois si error de connexion
def create_resilient_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1, 
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

#lire le fichier des cities
def load_cities_data(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Le fichier {csv_path} est introuvable.")
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")
    required_cols = {"city", "lat", "lng"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Le CSV doit contenir au moins les colonnes : {required_cols}")  
    return df


def fetch_city_weather(session: requests.Session, lat: float, lng: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": ",".join(DAILY_PARAMS),
        "timezone": "auto"
    }
    
    try:
        response = session.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "daily" not in data:
            raise ValueError("Réponse API invalide : section 'daily' manquante.")
        return data

    except requests.exceptions.HTTPError as err:
        print(f"[ERREUR HTTP] ({lat}, {lng}): {err}")
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] Temps d'attente dépassé pour ({lat}, {lng}).")
    except requests.exceptions.RequestException as err:
        print(f"[ERREUR RESEAU] ({lat}, {lng}): {err}")
    except Exception as err:
        print(f"[ERREUR INATTENDUE] ({lat}, {lng}): {err}")
        
    return None


def run_bronze_extraction():
    """Exécute l'extraction complète et sauvegarde la couche Bronze."""
    os.makedirs(BRONZE_DIR, exist_ok=True)
    session = create_resilient_session()
    
    cities_df = load_cities_data(RAW_CITIES_PATH).head(30)
    bronze_results = []
    
    print(f"Début de l'extraction pour {len(cities_df)} villes...")

    for idx, row in cities_df.iterrows():
        city_name = row['city']
        lat = row['lat']
        lng = row['lng']

        weather_raw = fetch_city_weather(session, lat, lng)

        if weather_raw:
            record = {
                "city": city_name,
                "lat": lat,
                "lng": lng,
                "admin_name": row.get('admin_name', None),
                "raw_response": weather_raw,
                "extracted_at": pd.Timestamp.now().isoformat()
            }
            bronze_results.append(record)
            print(f"[{idx+1}/{len(cities_df)}] Succès : {city_name}")
        else:
            print(f"[{idx+1}/{len(cities_df)}] Échec : {city_name}")

        # Courte pause pour éviter de dépasser la limite de débit (Rate Limit) de l'API
        time.sleep(0.1)

    # Sauvegarde inchangée du résultat brut sous format JSON dans la zone Bronze
    output_path = os.path.join(BRONZE_DIR, "raw_weather_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bronze_results, f, ensure_ascii=False, indent=4)

    print(f"\nExtraction Bronze terminée. Données brutes sauvegardées dans : {output_path}")


if __name__ == "__main__":
    run_bronze_extraction()