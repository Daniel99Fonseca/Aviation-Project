# src/transformation/opensky_to_parquet.py

import json
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw/opensky")
OUTPUT_DIR = Path("data/processed/opensky")

records = [] # list of dictionaries, each file is a dictionary of different states (planes)

files = RAW_DIR.glob("*.json")

for file_path in files:

    with open(file_path, "r", encoding="utf-8") as file:
        snapshot = json.load(file) # reading each file

    snapshot_time = snapshot["timestamp"] # getting time of each snapshot to later match with variable
                                          # last_contact

    for state in snapshot["states"]:
        state["snapshot_time"] = snapshot_time
        records.append(state)


df = pd.DataFrame(records) # turning into dataframe for tabular

OUTPUT_DIR.mkdir(parents=True, exist_ok=True) # creating output directory

output_file = OUTPUT_DIR / "aircraft_states.parquet"

df.to_parquet(output_file, index=False) # turning into parquet

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Parquet saved:", output_file)

print()
print(df.columns.tolist())

print()
print(df.dtypes)

print()
print(df.head())