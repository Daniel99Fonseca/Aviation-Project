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
    by=["icao24", "snapshot_time"]
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