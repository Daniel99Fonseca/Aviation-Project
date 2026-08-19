import requests
import json

from datetime import datetime
from pathlib import Path

# IPMA API
IPMA_URL = "https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json"

# Closest stations for LIS, OPO and FAO airports
IPMA_STATIONS = {
    "LIS": "1210580",
    "OPO": "1200545",
    "FAO": "1200554"
}

# Calling API Key
response = requests.get(IPMA_URL)

data = response.json()

selected_data = {}

for timestamp, stations in data.items(): # IPMA returns timestamp and stations
    selected_data[timestamp] = {} # Making dictionary with key:value - timestamp:stations
    for airport, station_id in IPMA_STATIONS.items(): # Getting data from API call related to relevant stations
        if station_id in stations:
            selected_data[timestamp][airport] = stations[station_id]


output_dir = Path("data/raw/ipma")
output_dir.mkdir(parents=True, exist_ok=True)

timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") # Making filename as time API was called
output_file = output_dir / f"ipma_{timestamp_str}.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(selected_data, file, indent=4)

print("Snapshot saved:", output_file)