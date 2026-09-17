import csv
import json
import logging
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# load settings from .env file
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO")
alert_threshold = float(os.getenv("ALERT_THRESHOLD_C", "30"))

# project root (lab_wpl_0809/) — monkeypatchable in tests
PROJECT_ROOT = Path(__file__).parent.parent

# set up logging to write to pipeline.log
log_file = PROJECT_ROOT / "pipeline.log"
logging.basicConfig(
    filename=log_file,
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def clean_city_name(raw_name: str) -> str:
    """Normalize a messy city name: strip junk chars, whitespace, title-case."""
    name = re.sub(r"[^a-zA-Z\s]", "", raw_name)
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    return name.title()


def load_and_clean_cities(csv_file: Path) -> list[dict]:
    """Read the cities CSV and return cleaned city/lat/lon records."""
    rows = []
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                name = clean_city_name(row["city"])
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                rows.append({
                    "city": name,
                    "latitude": lat,
                    "longitude": lon,
                })
                logger.info("Cleaned row: %s -> %s", row["city"], name)
            except Exception as e:
                logger.error("Skipping bad row %s: %s", row, e)
    return rows


def fetch_weather(city: str, latitude: float, longitude: float) -> dict | None:
    """Fetch hourly weather for one city from Open-Meteo. Returns None on failure."""
    params = {
        "hourly": "temperature_2m,precipitation",
        "timezone": "auto",
        "latitude": latitude,
        "longitude": longitude,
    }
    try:
        response = requests.get(url=OPEN_METEO_URL, params=params, verify=False)
        response.raise_for_status()
    except Exception as e:
        logger.error("API call failed for %s: %s", city, e)
        return None

    data = response.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temperature = hourly.get("temperature_2m", [])
    precipitation = hourly.get("precipitation", [])

    if not times:
        logger.info("Hourly data not seen for %s", city)
        return None

    if not (len(times) == len(temperature) == len(precipitation)):
        logger.error("Hourly data not present for all parameters for %s", city)
        return None

    fixed_precipitation = []
    for j in range(len(times)):
        if j < len(precipitation) and precipitation[j] is not None:
            fixed_precipitation.append(precipitation[j])
        else:
            fixed_precipitation.append(0)

    return {
        "city": city,
        "data": {
            "time": times,
            "temperature_2m": temperature,
            "precipitation": fixed_precipitation,
        },
    }


def write_reports(merged_df):
    # make the reports folder if it does not exist
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    # save full report to excel
    excel_path = reports_dir / "weather_report.xlsx"
    merged_df.to_excel(excel_path, index=False, sheet_name="Daily Weather")
    logger.info("Saved excel report to %s", excel_path)

    # find cities hotter than the alert threshold
    alert_list = []
    for i in range(len(merged_df)):
        row = merged_df.iloc[i]
        max_temp = row["max_temp"]
        if max_temp > alert_threshold:
            alert_list.append({
                "city": row["city"],
                "date": str(row["date"]),
                "max_temp": max_temp,
                "latitude": row["latitude"],
                "longitude": row["longitude"],
            })

    # save alert list to json file
    json_path = reports_dir / "heat_alerts.json"
    with open(json_path, "w", encoding="utf-8") as alert_file:
        json.dump(alert_list, alert_file, indent=2)
    logger.info("Saved %d heat alerts to %s", len(alert_list), json_path)


def run_pipeline():
    csv_file = PROJECT_ROOT / "data" / "raw_cities.csv"

    logger.info("Starting to parse CSV file: %s", csv_file)

    try:
        rows = load_and_clean_cities(csv_file)
    except FileNotFoundError as e:
        logger.error("Could not find CSV file: %s", e)
        return

    logger.info("Finished parsing CSV file. Total rows: %d", len(rows))

    weather_data = []
    start_time = time.time()

    for row in rows:
        result = fetch_weather(row["city"], row["latitude"], row["longitude"])
        if result is None:
            continue

        hourly = result["data"]
        city_df = pd.DataFrame(hourly)
        city_df["city"] = result["city"]
        weather_data.append(city_df)
        logger.info("Fetched %d hourly rows for %s", len(city_df), row["city"])

    end_time = time.time()
    logger.info(
        "Fetched weather data for %d cities in %.2f seconds",
        len(weather_data),
        end_time - start_time,
    )

    if len(weather_data) == 0:
        logger.error("No weather data was fetched. Stopping pipeline.")
        return

    all_weather_df = pd.concat(weather_data, ignore_index=True)

    # go through each row and fix missing values
    cleaned_weather = []
    for i in range(len(all_weather_df)):
        row = all_weather_df.iloc[i]

        temp = row["temperature_2m"]
        if temp is None or str(temp) == "nan":
            continue

        rain = row["precipitation"]
        if rain is None or str(rain) == "nan":
            rain = 0

        # time looks like "2024-09-10T12:00" so date is the part before T
        time_str = str(row["time"])
        date_str = time_str.split("T")[0]

        cleaned_weather.append({
            "city": row["city"],
            "time": time_str,
            "date": date_str,
            "temperature_2m": temp,
            "precipitation": rain,
        })

    all_weather_df = pd.DataFrame(cleaned_weather)

    # group by city and day and get max temp and total rain
    daily_stats = all_weather_df.groupby(["city", "date"]).agg({
        "temperature_2m": "max",
        "precipitation": "sum",
    })
    daily_stats = daily_stats.reset_index()
    daily_stats = daily_stats.rename(columns={
        "temperature_2m": "max_temp",
        "precipitation": "total_precip",
    })

    # join city info from csv with the weather stats
    cities_df = pd.DataFrame(rows)
    merged_df = pd.merge(cities_df, daily_stats, on="city", how="left")

    logger.info("Final merged dataframe has %d rows", len(merged_df))

    write_reports(merged_df)
    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    run_pipeline()
