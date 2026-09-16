-- sql/schema.sql
CREATE TABLE IF NOT EXISTS dim_cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL UNIQUE,
    lat NUMERIC(8, 6) NOT NULL,
    lng NUMERIC(8, 6) NOT NULL,
    admin_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS fact_weather_forecasts (
    id SERIAL PRIMARY KEY,
    city_id INT REFERENCES dim_cities(city_id),
    forecast_date DATE NOT NULL,
    temp_max NUMERIC(4, 1),
    temp_min NUMERIC(4, 1),
    precipitation_sum NUMERIC(5, 1),
    precipitation_probability_max INT,
    wind_speed_max NUMERIC(5, 1),
    wind_gusts_max NUMERIC(5, 1),
    weather_code INT,
    risk_score NUMERIC(5, 2),
    risk_level VARCHAR(20),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_city_date UNIQUE (city_id, forecast_date)
);
