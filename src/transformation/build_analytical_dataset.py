from pathlib import Path

import pandas as pd


APPROACHES_FILE = Path(
    "data/processed/approaches/approaches_lis.parquet"
)

WEATHER_FILE = Path(
    "data/processed/ipma/weather.parquet"
)

OUTPUT_DIR = Path(
    "data/processed/analytical"
)

OUTPUT_FILE = OUTPUT_DIR / "approaches_weather_lis.parquet"


# --------------------------------------------------
# Load data
# --------------------------------------------------

approaches = pd.read_parquet(APPROACHES_FILE)
weather = pd.read_parquet(WEATHER_FILE)


print("Approaches:", len(approaches))
print("Weather records:", len(weather))


# --------------------------------------------------
# Prepare approach timestamps
# --------------------------------------------------

approaches["landing_datetime"] = pd.to_datetime(
    approaches["landing_time"],
    unit="s",
    utc=True
)

approaches["weather_time"] = (
    approaches["landing_datetime"]
    .dt.floor("h")
)


# --------------------------------------------------
# Keep Lisbon weather only
# --------------------------------------------------

weather_lis = weather[
    weather["airport"] == "LIS"
].copy()

# We already know these approaches belong to LIS,
# so avoid having two airport columns after the merge.
weather_lis = weather_lis.drop(
    columns=["airport"]
)


print("LIS weather records:", len(weather_lis))


# --------------------------------------------------
# Join OpenSky approaches with IPMA weather
# --------------------------------------------------

analytical = approaches.merge(
    weather_lis,
    on="weather_time",
    how="left"
)


# --------------------------------------------------
# Validation
# --------------------------------------------------

weather_columns = [
    "intensidadeVentoKM",
    "temperatura",
    "radiacao",
    "idDireccVento",
    "precAcumulada",
    "intensidadeVento",
    "humidade",
    "pressao"
]

matched = analytical[
    weather_columns
].notna().any(axis=1).sum()

unmatched = len(analytical) - matched


print()
print("Join results:")
print("Total approaches:", len(analytical))
print("Matched with weather:", matched)
print("Without weather:", unmatched)

print()
print("Weather coverage:")
print(f"{matched / len(analytical) * 100:.2f}%")


# --------------------------------------------------
# Preview
# --------------------------------------------------

preview_columns = [
    "approach_id",
    "callsign",
    "landing_datetime",
    "weather_time",
    "duration_seconds",
    "last_airborne_velocity",
    "mean_vertical_rate",
    "temperatura",
    "intensidadeVentoKM",
    "idDireccVento",
    "precAcumulada",
    "humidade",
    "pressao"
]

print()
print(analytical[preview_columns].head(20))


# --------------------------------------------------
# Save analytical dataset
# --------------------------------------------------

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

analytical.to_parquet(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved:", OUTPUT_FILE)