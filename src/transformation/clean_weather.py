import os
import pandas as pd
import json

def transform_bronze_To_silver():
    path_data="data/bronze/raw_weather_data.json"
    silver_dir="data/silver"
    if not os.path.exists(path_data):
        raise FileNotFoundError(f"le fichier {path_data} n'existe pas")
    
    with open(path_data, "r",encoding="utf-8") as f:
        bronze_data=json.load(f)
    silver_records=[]
    
    for record in bronze_data:
        city=record.get("city")
        lat=record.get("lat")
        lng=record.get("lng")
        extracted_at=record.get("extracted_at")
        
        raw_response=record.get("raw_response", {})
        
        daily_data = raw_response.get("daily", {})
        
        dates = daily_data.get("time", [])
        temp_max = daily_data.get("temperature_2m_max", [])#
        temp_min=daily_data.get("temperature_2m_min", [])
        precip_sum=daily_data.get("precipitation_sum", [])#
        precip_prob=daily_data.get("precipitation_probability_max", [])
        wind_speed = daily_data.get("wind_speed_10m_max", [])#
        wind_gusts = daily_data.get("wind_gusts_10m_max", [])#
        weather_code = daily_data.get("weather_code", [])
        
        for i in range(len(dates)):
            row={
                "city":city,
                "latitude":lat,
                "longtitude":lng,
                "date":dates[i],
                "temperature_max": (
                    temp_max[i] if i <len(temp_max) else None
                ),
                "temperature_min": (
                    temp_min[i] if i <len(temp_min) else None
                ),
                "precipitation_sum":(
                    precip_sum[i] if i < len(precip_sum) else None
                ),
                "precipitation_probability_max":(
                    precip_prob[i] if i < len(precip_prob) else None
                ),
                "wind_speed_max": (
                    wind_speed[i] if i < len(wind_speed) else None
                ),
                "wind_gusts_max":(
                    wind_gusts[i] if i < len(wind_gusts) else None
                ),
                "weather_code": (
                    weather_code[i] if i < len(weather_code) else None
                ),
                "extracted_at":extracted_at
            }
            silver_records.append(row)
            

    df = pd.DataFrame(silver_records)

    df["date"] = pd.to_datetime(df["date"])
    df["extracted_at"] = pd.to_datetime(df["extracted_at"])

    
    numeric_cols = [
        "temperature_max",
        "temperature_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "wind_speed_max",
        "wind_gusts_max",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[numeric_cols] = df[numeric_cols].fillna(0)

  
    os.makedirs(silver_dir, exist_ok=True)

    csv_output_path = os.path.join(silver_dir, "weather_silver.csv")
    parquet_output_path = os.path.join(silver_dir, "weather_silver.parquet")

    df.to_csv(csv_output_path, index=False, encoding="utf-8")
    df.to_parquet(parquet_output_path, index=False)

    print(
        f" {len(df)}:"
    )
    print(f" - CSV: {csv_output_path}")
    print(f" - Parquet: {parquet_output_path}")


if __name__ == "__main__":
    transform_bronze_To_silver()