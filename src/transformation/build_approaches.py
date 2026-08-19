import pandas as pd

from geopy.distance import geodesic
from pathlib import Path


INPUT_FILE = Path("data/processed/opensky/aircraft_states.parquet")

LIS_COORDS = (38.7742, -9.1342)
MAX_DISTANCE_KM = 40
SESSION_GAP = 3600


df = pd.read_parquet(INPUT_FILE)

# Limpar espaços extra nos callsigns
df["callsign"] = df["callsign"].str.strip()

# Para estudar aproximações, interessam-nos primeiro as aeronaves no ar
df = df[df["on_ground"] == False].copy()


def distance_to_lis(row):

    aircraft_position = (
        row["latitude"],
        row["longitude"]
    )

    return geodesic(
        aircraft_position,
        LIS_COORDS
    ).km


# Calcular distância de cada posição ao aeroporto de Lisboa
df["distance_to_lis"] = df.apply(
    distance_to_lis,
    axis=1
)

# Ficar apenas com pontos até 40 km de LIS
lis_data = df[
    df["distance_to_lis"] <= MAX_DISTANCE_KM
].copy()

# Ordenar cada aeronave cronologicamente
lis_data = lis_data.sort_values(
    by=["icao24", "callsign", "snapshot_time"]
)

# Diferença temporal entre registos consecutivos
# da mesma aeronave + callsign
lis_data["time_gap"] = (
    lis_data
    .groupby(["icao24", "callsign"])["snapshot_time"]
    .diff()
)

# Uma nova sessão começa:
# - no primeiro registo do grupo
# - ou quando o gap é superior a 1 hora
lis_data["new_session"] = (
    lis_data["time_gap"].isna()
    | (lis_data["time_gap"] > SESSION_GAP)
)

# Número da sessão dentro de cada combinação
# icao24 + callsign
lis_data["session"] = (
    lis_data
    .groupby(["icao24", "callsign"])["new_session"]
    .cumsum()
)


print(
    "Airborne records within 40 km of LIS:",
    len(lis_data)
)

print(
    "Unique aircraft:",
    lis_data["icao24"].nunique()
)


# Número total de sessões
sessions = (
    lis_data[
        ["icao24", "callsign", "session"]
    ]
    .drop_duplicates()
)

print()
print("Total sessions:", len(sessions))


# Estatísticas do número de pontos por sessão
session_sizes = (
    lis_data
    .groupby(["icao24", "callsign", "session"])
    .size()
)

print()
print("Session size statistics:")
print(session_sizes.describe())


# Criar resumo de cada sessão
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


# Alteração da distância ao longo da sessão
session_summary["distance_change"] = (
    session_summary["end_distance"]
    - session_summary["start_distance"]
)

# Alteração da altitude ao longo da sessão
session_summary["altitude_change"] = (
    session_summary["end_altitude"]
    - session_summary["start_altitude"]
)


# Pontos observados dentro de 10 km de LIS
points_within_10km = lis_data[
    lis_data["distance_to_lis"] <= 10
]

# Altitude mínima observada dentro dos 10 km
min_altitude_10km = (
    points_within_10km
    .groupby(
        ["icao24", "callsign", "session"]
    )["baro_altitude"]
    .min()
    .reset_index(
        name="min_altitude_10km"
    )
)

# Adicionar essa informação ao resumo das sessões
session_summary = session_summary.merge(
    min_altitude_10km,
    on=[
        "icao24",
        "callsign",
        "session"
    ],
    how="left"
)

velocity_summary = (
    lis_data
    .groupby(["icao24", "callsign", "session"])
    .agg(
        start_velocity=("velocity", lambda x: x.head(2).mean()),
        end_velocity=("velocity", lambda x: x.tail(2).mean())
    )
    .reset_index()
)

session_summary = session_summary.merge(
    velocity_summary,
    on=["icao24", "callsign", "session"],
    how="left"
)

session_summary["velocity_change"] = (
    session_summary["end_velocity"]
    - session_summary["start_velocity"]
)

def classify_session(row):

    if (
    row["points"] >= 5
    and row["distance_change"] < 0
    and row["altitude_change"] < 0
    and row["velocity_change"] < 0
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
    
# Classificar cada sessão
session_summary["movement_type"] = (
    session_summary.apply(
        classify_session,
        axis=1
    )
)

print()
print("Movement types:")
print(
    session_summary[
        "movement_type"
    ].value_counts()
)


print()
print("Arrival examples:")

print(
    session_summary[
        session_summary["movement_type"] == "arrival"
    ][
        [
            "icao24",
            "callsign",
            "session",
            "points",
            "start_distance",
            "end_distance",
            "min_distance",
            "start_altitude",
            "end_altitude",
            "min_altitude_10km"
        ]
    ].head(20)
)