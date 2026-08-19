import pandas as pd

from geopy.distance import geodesic
from pathlib import Path


INPUT_FILE = Path("data/processed/opensky/aircraft_states.parquet")

LIS_COORDS = (38.7742, -9.1342)
MAX_DISTANCE_KM = 40


df = pd.read_parquet(INPUT_FILE)

# Para estudar aproximações, interessam-nos primeiro as aeronaves no ar
df = df[df["on_ground"] == False].copy()


# Calcular distância de cada posição ao aeroporto de Lisboa
def distance_to_lis(row):

    aircraft_position = (row["latitude"], row["longitude"])

    return geodesic(aircraft_position, LIS_COORDS).km


df["distance_to_lis"] = df.apply(distance_to_lis, axis=1)

# Ficar apenas com pontos até 40 km de LIS
lis_data = df[df["distance_to_lis"] <= MAX_DISTANCE_KM].copy()

# Ordenar cada aeronave cronologicamente
lis_data = lis_data.sort_values(
    by=["icao24", "callsign", "snapshot_time"]
)

# Diferença de tempo entre registos consecutivos
# da mesma aeronave e callsign
lis_data["time_gap"] = (
    lis_data
    .groupby(["icao24", "callsign"])["snapshot_time"]
    .diff()
)

print("Airborne records within 40 km of LIS:", len(lis_data))
print("Unique aircraft:", lis_data["icao24"].nunique())

print()
print(
    lis_data[
        [
            "icao24",
            "callsign",
            "snapshot_time",
            "baro_altitude",
            "velocity",
            "vertical_rate",
            "distance_to_lis"
        ]
    ].head(30)
)

SESSION_GAP = 3600
lis_data["new_session"] = (
    lis_data["time_gap"].isna()
    | (lis_data["time_gap"] > SESSION_GAP)
)

lis_data["session"] = (
    lis_data
    .groupby(["icao24", "callsign"])["new_session"]
    .cumsum()
)

sessions = (
    lis_data[
        ["icao24", "callsign", "session"]
    ]
    .drop_duplicates()
)

print()
print("Total sessions:", len(sessions))

print()
print(sessions.head(20))

session_sizes = (
    lis_data
    .groupby(["icao24", "callsign", "session"])
    .size()
)

print()
print("Session size statistics:")
print(session_sizes.describe())

session_summary = (
    lis_data
    .groupby(["icao24", "callsign", "session"])
    .agg(
        points=("snapshot_time", "count"),
        start_distance=("distance_to_lis", "first"),
        end_distance=("distance_to_lis", "last"),
        start_altitude=("baro_altitude", "first"),
        end_altitude=("baro_altitude", "last")
    )
    .reset_index()
)

session_summary["distance_change"] = (
    session_summary["end_distance"]
    - session_summary["start_distance"]
)

session_summary["altitude_change"] = (
    session_summary["end_altitude"]
    - session_summary["start_altitude"]
)

def classify_session(row):

    if (
        row["distance_change"] < 0
        and row["altitude_change"] < 0
    ):
        return "arrival"

    elif (
        row["distance_change"] > 0
        and row["altitude_change"] > 0
    ):
        return "departure"

    else:
        return "other"


session_summary["movement_type"] = session_summary.apply(
    classify_session,
    axis=1
)

print()
print("Movement types:")
print(session_summary["movement_type"].value_counts())

print()
print(
    session_summary[
        [
            "icao24",
            "callsign",
            "session",
            "points",
            "start_distance",
            "end_distance",
            "start_altitude",
            "end_altitude",
            "movement_type"
        ]
    ].head(30)
)