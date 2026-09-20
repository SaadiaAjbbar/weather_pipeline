/*Quelles villes auront les températures les plus élevées ?*/
select fact_weather_forecasts.temp_max,dim_cities.city_name 
from  dim_cities join fact_weather_forecasts
on dim_cities.city_id=fact_weather_forecasts.city_id
order by fact_weather_forecasts.temp_max desc
limit 5


/*Quelles villes auront les plus fortes précipitations ? */
SELECT
    c.city_name,
    MAX(f.precipitation_sum) AS precipitation_max
FROM fact_weather_forecasts f
JOIN dim_cities c
    ON f.city_id = c.city_id
GROUP BY c.city_name
ORDER BY precipitation_max DESC;

/*Quelles villes présentent le risque moyen le plus élevé  ?*/
SELECT
    c.city_name,
    ROUND(AVG(f.risk_score), 2) AS risque_moyen
FROM fact_weather_forecasts f
JOIN dim_cities c
    ON f.city_id = c.city_id
GROUP BY c.city_name
ORDER BY risque_moyen DESC;

/*Quelles périodes présentent le risque maximal ?*/
SELECT
    f.forecast_date,
    c.city_name,
    f.risk_score,
    f.risk_level
FROM fact_weather_forecasts f
JOIN dim_cities c
    ON f.city_id = c.city_id
ORDER BY f.risk_score DESC;

/*Pour chaque ville, quelle période présente le plus grand risque ?*/
WITH ranked_risks AS (
    SELECT
        c.city_name,
        f.forecast_date,
        f.risk_score,
        f.risk_level,
        ROW_NUMBER() OVER (
            PARTITION BY c.city_name
            ORDER BY f.risk_score DESC
        ) AS rn
    FROM fact_weather_forecasts f
    JOIN dim_cities c
        ON f.city_id = c.city_id
)
SELECT
    city_name,
    forecast_date,
    risk_score,
    risk_level
FROM ranked_risks
WHERE rn = 1
ORDER BY risk_score DESC;