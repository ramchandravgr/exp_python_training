import json
from unittest.mock import MagicMock, patch

import pandas as pd

import src.pipeline as pipeline
from src.pipeline import clean_city_name, fetch_weather, load_and_clean_cities, write_reports


# 1. Unit test for data normalization
# Verifies that city-name cleaning handles dirty formatting (spaces, casing, punctuation)
def test_clean_city_name():
    assert clean_city_name(" pArIS!! ") == "Paris"
    assert clean_city_name("TOkyO") == "Tokyo"
    assert clean_city_name("Sao Paulo!!") == "Sao Paulo"
    assert clean_city_name("  new york ") == "New York"
    assert clean_city_name("Lagos***") == "Lagos"


def test_load_and_clean_cities(tmp_path):
    test_csv = tmp_path / "test_cities.csv"
    test_csv.write_text(
        "city,latitude,longitude\n"
        " pArIS!! ,48.85,2.35\n"
        "TOkyO,35.68,139.69\n"
    )

    rows = load_and_clean_cities(test_csv)

    assert [row["city"] for row in rows] == ["Paris", "Tokyo"]
    assert len(rows) == 2
    assert rows[0]["latitude"] == 48.85
    assert rows[1]["longitude"] == 139.69


# 2. Unit test for API mocking
# Mocks an HTTP GET response so the test never hits Open-Meteo
@patch("src.pipeline.requests.get")
def test_fetch_weather(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "hourly": {
            "time": ["2026-01-01T00:00"],
            "temperature_2m": [22.5],
            "precipitation": [0.0],
        }
    }
    mock_get.return_value = mock_response

    result = fetch_weather("Paris", 48.85, 2.35)

    assert result is not None
    assert result["city"] == "Paris"
    assert result["data"]["temperature_2m"][0] == 22.5
    assert result["data"]["precipitation"][0] == 0.0
    mock_get.assert_called_once()


@patch("src.pipeline.requests.get")
def test_fetch_weather_fills_missing_precipitation(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "hourly": {
            "time": ["2026-01-01T00:00", "2026-01-01T01:00"],
            "temperature_2m": [20.0, 21.0],
            "precipitation": [1.0, None],
        }
    }
    mock_get.return_value = mock_response

    result = fetch_weather("London", 51.5, -0.1)

    assert result["data"]["precipitation"] == [1.0, 0]


@patch("src.pipeline.requests.get")
def test_fetch_weather_returns_none_on_api_error(mock_get):
    mock_get.side_effect = Exception("connection failed")

    result = fetch_weather("Paris", 48.85, 2.35)

    assert result is None


# 3. Unit test for reporting / alerts
# Verifies Excel + JSON outputs and that high temps become heat alerts
def test_write_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "alert_threshold", 25.0)

    merged_df = pd.DataFrame(
        [
            {
                "city": "Paris",
                "latitude": 48.85,
                "longitude": 2.35,
                "date": "2026-01-01",
                "max_temp": 30.0,
                "total_precip": 3.0,
            },
            {
                "city": "Tokyo",
                "latitude": 35.68,
                "longitude": 139.69,
                "date": "2026-01-01",
                "max_temp": 20.0,
                "total_precip": 1.0,
            },
        ]
    )

    write_reports(merged_df)

    excel_path = tmp_path / "reports" / "weather_report.xlsx"
    json_path = tmp_path / "reports" / "heat_alerts.json"
    assert excel_path.exists()
    assert json_path.exists()

    with open(json_path, encoding="utf-8") as f:
        alert_data = json.load(f)

    assert len(alert_data) == 1
    assert alert_data[0]["city"] == "Paris"
    assert alert_data[0]["max_temp"] == 30.0
