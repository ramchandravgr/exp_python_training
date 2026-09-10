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
alert_threshold = 30

# set up logging to write to pipeline.log
log_file = Path(__file__).parent.parent / "pipeline.log"
logging.basicConfig(
    filename=log_file,
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def write_reports(merged_df):
    # make the reports folder if it does not exist
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # save full report to excel
    excel_path = reports_dir / "weather_report.xlsx"
    merged_df.to_excel(excel_path, index=False, sheet_name="Daily Weather")
    logger.info("Saved excel report to %s", excel_path)

    # find cities hotter than 30 degrees
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
    csv_file = Path(__file__).parent.parent / "data" / "raw_cities.csv"

    logger.info("Starting to parse CSV file: %s", csv_file)
    rows = []

    try:
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # remove special characters like ! and *
                    name = re.sub(r"[^a-zA-Z\s]", "", row["city"])
                    # remove extra spaces at start/end
                    name = name.strip()
                    # replace multiple spaces with single space
                    name = re.sub(r"\s+", " ", name)
                    # make it title case, e.g. "new york" -> "New York"
                    name = name.title()

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
    except FileNotFoundError as e:
        logger.error("Could not find CSV file: %s", e)
        return

    logger.info("Finished parsing CSV file. Total rows: %d", len(rows))

    url = "https://api.open-meteo.com/v1/forecast"
    weather_data = []
    start_time = time.time()

    for row in rows:
        params = {
            "hourly": "temperature_2m,precipitation",
            "timezone": "auto",
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }

        try:
            response = requests.get(url=url, params=params, verify=False)
            response.raise_for_status()
        except Exception as e:
            logger.error("API call failed for %s: %s", row["city"], e)
            continue

        data = response.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temperature = hourly.get("temperature_2m", [])
        precipitation = hourly.get("precipitation", [])

        if not times:
            logger.info("Hourly data not seen for %s", row["city"])
            continue

        if not (len(times) == len(temperature) == len(precipitation)):
            logger.error("Hourly data not present for all parameters for %s", row["city"])
            continue

        # fix missing precipitation values before making the dataframe
        fixed_precipitation = []
        for j in range(len(times)):
            if j < len(precipitation) and precipitation[j] is not None:
                fixed_precipitation.append(precipitation[j])
            else:
                fixed_precipitation.append(0)

        hourly["precipitation"] = fixed_precipitation

        city_df = pd.DataFrame(hourly)
        city_df["city"] = row["city"]
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
