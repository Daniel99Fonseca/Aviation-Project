import pandas as pd

from geopy.distance import geodesic
from pathlib import Path


INPUT_FILE = Path("data/processed/opensky/aircraft_states.parquet")

LIS_COORDS = (38.7742, -9.1342)
MAX_DISTANCE_KM = 40


df = pd.read_parquet(INPUT_FILE)

df["callsign"] = df["callsign"].str.strip()

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
        min_distance=("distance_to_lis", "min"),
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
        and row["min_distance"] <= 10
        and row["min_altitude_10km"] < 1000
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

# Ficar apenas com sessões classificadas como arrival
arrival_sessions = session_summary[
    session_summary["movement_type"] == "arrival"
].copy()

closest_point_altitudes = []

for _, session_row in arrival_sessions.iterrows():

    session_points = lis_data[
        (lis_data["icao24"] == session_row["icao24"])
        & (lis_data["callsign"] == session_row["callsign"])
        & (lis_data["session"] == session_row["session"])
    ]

    closest_point = session_points.loc[
        session_points["distance_to_lis"].idxmin()
    ]

    closest_point_altitudes.append(
        closest_point["baro_altitude"]
    )

arrival_sessions["closest_altitude"] = closest_point_altitudes

points_within_10km = lis_data[
    lis_data["distance_to_lis"] <= 10
]

min_altitude_10km = (
    points_within_10km
    .groupby(["icao24", "callsign", "session"])["baro_altitude"]
    .min()
    .reset_index(name="min_altitude_10km")
)

session_summary = session_summary.merge(
    min_altitude_10km,
    on=["icao24", "callsign", "session"],
    how="left"
)

print()
print("Movement types:")
print(session_summary["movement_type"].value_counts())
print(
    session_summary[
        session_summary["movement_type"] == "arrival"
    ][
        [
            "callsign",
            "points",
            "min_distance",
            "min_altitude_10km"
        ]
    ].head(20)
)

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
            "movement_type",
            "min_distance"
        ]
    ].head(30)
)

print()
print("Closest-point altitude statistics:")
print(
    arrival_sessions["closest_altitude"].describe()
)

print()
print("Arrival candidates by closest altitude:")

print(
    "Below 500 m:",
    (arrival_sessions["closest_altitude"] < 500).sum()
)

print(
    "Below 1000 m:",
    (arrival_sessions["closest_altitude"] < 1000).sum()
)

print(
    "Below 2000 m:",
    (arrival_sessions["closest_altitude"] < 2000).sum()
)

print(
    "Above 5000 m:",
    (arrival_sessions["closest_altitude"] > 5000).sum()
)

print(
    "Above 10000 m:",
    (arrival_sessions["closest_altitude"] > 10000).sum()
)

print()
print("Highest closest-point altitudes:")

print(
    arrival_sessions[
        [
            "icao24",
            "callsign",
            "session",
            "min_distance",
            "closest_altitude"
        ]
    ]
    .sort_values(
        by="closest_altitude",
        ascending=False
    )
    .head(20)
)

print()
print("Arrivals with missing closest altitude:")

print(
    arrival_sessions[
        arrival_sessions["closest_altitude"].isna()
    ][
        [
            "icao24",
            "callsign",
            "session",
            "points",
            "min_distance"
        ]
    ]
)


tap028 = lis_data[
    (lis_data["icao24"] == "4952a2")
    & (lis_data["callsign"] == "TAP028")
    & (lis_data["session"] == 1)
]

print()
print("TAP028 session:")

print(
    tap028[
        [
            "snapshot_time",
            "distance_to_lis",
            "baro_altitude",
            "geo_altitude",
            "velocity",
            "vertical_rate"
        ]
    ]
)