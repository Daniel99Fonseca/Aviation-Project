import json
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw/ipma")
OUTPUT_DIR = Path("data/processed/ipma")


records = []
missing_weather = 0

files = RAW_DIR.glob("*.json")

for file_path in files:

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for timestamp, airports in data.items():

        for airport, weather in airports.items():

            if weather is None:
                missing_weather += 1
                continue

            record = {
                "weather_time": timestamp,
                "airport": airport,
                **weather
            }

            records.append(record)


df = pd.DataFrame(records)

df["weather_time"] = pd.to_datetime(
    df["weather_time"],
    utc=True
)

df = df.drop_duplicates(
    subset=["weather_time", "airport"]
)

df = df.sort_values(
    by=["airport", "weather_time"]
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

output_file = OUTPUT_DIR / "weather.parquet"

df.to_parquet(
    output_file,
    index=False
)

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Airports:", df["airport"].unique())

print()
print(df.head())

print()
print("Saved:", output_file)