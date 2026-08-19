import pandas as pd

from geopy.distance import geodesic
from pathlib import Path


INPUT_FILE = Path("data/processed/opensky/aircraft_states.parquet")

LIS_COORDS = (38.7742, -9.1342)

MAX_DISTANCE_KM = 40
LANDING_DISTANCE_KM = 10
SESSION_GAP = 3600


df = pd.read_parquet(INPUT_FILE)

df["callsign"] = df["callsign"].str.strip()


def distance_to_lis(row):

    aircraft_position = (
        row["latitude"],
        row["longitude"]
    )

    return geodesic(
        aircraft_position,
        LIS_COORDS
    ).km


df["distance_to_lis"] = df.apply(
    distance_to_lis,
    axis=1
)


# Ficar apenas com pontos até 40 km de LIS
lis_data = df[
    df["distance_to_lis"] <= MAX_DISTANCE_KM
].copy()


# Ordenar cronologicamente
lis_data = lis_data.sort_values(
    by=["icao24", "callsign", "snapshot_time"]
)


# Calcular diferença temporal entre pontos
lis_data["time_gap"] = (
    lis_data
    .groupby(["icao24", "callsign"])["snapshot_time"]
    .diff()
)


# Identificar início de novas sessões
lis_data["new_session"] = (
    lis_data["time_gap"].isna()
    | (lis_data["time_gap"] > SESSION_GAP)
)


lis_data["session"] = (
    lis_data
    .groupby(["icao24", "callsign"])["new_session"]
    .cumsum()
)


# Ver estado anterior de on_ground
lis_data["previous_on_ground"] = (
    lis_data
    .groupby(["icao24", "callsign", "session"])["on_ground"]
    .shift(1)
)


# Landing = transição False -> True perto do aeroporto
landing_events = lis_data[
    (lis_data["previous_on_ground"] == False)
    & (lis_data["on_ground"] == True)
    & (lis_data["distance_to_lis"] <= LANDING_DISTANCE_KM)
].copy()


print("Landing events detected:", len(landing_events))

print()
print(
    landing_events[
        [
            "icao24",
            "callsign",
            "session",
            "snapshot_time",
            "distance_to_lis",
            "baro_altitude",
            "velocity"
        ]
    ].head(20)
)


# Reconstruir os pontos anteriores a cada landing
approach_records = []


for _, landing in landing_events.iterrows():

    approach = lis_data[
        (lis_data["icao24"] == landing["icao24"])
        & (lis_data["callsign"] == landing["callsign"])
        & (lis_data["session"] == landing["session"])
        & (lis_data["snapshot_time"] <= landing["snapshot_time"])
    ].copy()

    approach_records.append(approach)


print()
print("Approaches reconstructed:", len(approach_records))


# Mostrar exemplo da primeira aproximação encontrada
if len(approach_records) > 0:

    print()
    print("Example approach:")

    print(
        approach_records[0][
            [
                "icao24",
                "callsign",
                "snapshot_time",
                "distance_to_lis",
                "baro_altitude",
                "velocity",
                "vertical_rate",
                "on_ground"
            ]
        ]
    )