import requests
import json

from datetime import datetime
from pathlib import Path


IPMA_URL = "https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json"

IPMA_STATIONS = {
    "LIS": "1210580",
    "OPO": "1200545",
    "FAO": "1200554"
}


response = requests.get(IPMA_URL)

data = response.json()

selected_data = {}

for timestamp, stations in data.items():
    selected_data[timestamp] = {}
    for airport, station_id in IPMA_STATIONS.items():
        if station_id in stations:
            selected_data[timestamp][airport] = stations[station_id]


output_dir = Path("data/raw/ipma")
output_dir.mkdir(parents=True, exist_ok=True)

timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = output_dir / f"ipma_{timestamp_str}.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(selected_data, file, indent=4)

print("Snapshot saved:", output_file)