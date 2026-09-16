# 🌤️ Morocco Weather Data Pipeline (ETL)

Un pipeline de données Data Engineering complet pour collecter, nettoyer, stocker et visualiser les données météorologiques des villes marocaines en utilisant une architecture Medallion (Bronze & Silver) orchestrée par Docker.

---

## 📌 Architecture du Projet

Le projet suit une approche de Data Engineering moderne basée sur une architecture multi-couches :

1. **Ingestion (Couche Bronze) :** Extraction des données météorologiques brutes depuis l'API **Open-Meteo** à partir des coordonnées GPS des villes marocaines (`data/raw_cities.csv`).
2. **Transformation (Couche Silver) :** Nettoyage des données JSON, aplatissement des structures imbriquées (*flattening/unnesting*), gestion des valeurs manquantes (`NaN`) et conversion des types de données.
3. **Stockage & Orchestration :** Conteneurisation de l'environnement avec **Docker Compose** intégrant **PostgreSQL** pour le stockage final, **Apache Airflow** pour l'automatisation, et **Streamlit** pour la visualisation.

---

## 📁 Structure du Projet

```text
morocco-weather-pipeline/
│
├── data/
│   ├── raw_cities.csv           # Liste des villes marocaines avec coordonnées GPS
│   ├── bronze/                  # Stockage des données brutes JSON (Bronze Layer)
│   └── silver/                  # Données nettoyées au format CSV et Parquet (Silver Layer)
│
├── sql/
│   └── schema.sql               # Script de création des tables PostgreSQL
│
├── src/
│   ├── extraction/
│   │   └── fetch_weather.py     # Script d'extraction des données API (Bronze)
│   └── transformation/
│       └── clean_silver.py      # Script de nettoyage et structuration (Silver)
│
├── dashboard/
│   └── app.py                   # Application Streamlit pour l'affichage des données
│
├── dags/                        # DAGs Apache Airflow pour la planification
├── .env                         # Configuration des variables d'environnement
├── docker-compose.yml           # Service Orchestration (Postgres, Airflow, Streamlit, PgAdmin)
├── Dockerfile                   # Image Docker personnalisée Python/Airflow
├── requirements.txt             # Dépendances Python
└── README.md                    # Documentation du projet