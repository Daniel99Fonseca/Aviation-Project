import json 

from datetime import datetime
from pathlib import Path

from opensky_api import OpenSkyApi, TokenManager

PORTUGAL_BBOX = (36.9, 42.2, -9.6, -6.0)

token_manager = TokenManager.from_json_file("credentials.json")
api = OpenSkyApi(token_manager=token_manager)

# get_states returns a 2D Array (OpenSkyStates):
# - states.time 
# - states.states which contains the information of every aircraft caught by the Boundary Box (BBOX)
#  in the form of a 'StateVector'
states = api.get_states(bbox=PORTUGAL_BBOX)

aircraft_data = []

for state in states.states: # states.states returns information on every aircraft in bbox
    aircraft_data.append(vars(state))

snapshot = { 
    "timestamp": states.time,
    "aircraft_count": len(states.states),
    "states": aircraft_data 
}

outputdir = Path("data/raw/opensky")
outputdir.mkdir(parents=True, exist_ok=True)

timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") # Making filename = time api was called
output_file = outputdir / f"opensky_{timestamp_str}.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(snapshot, file, indent=4)
    
print("Snapshot saved:", output_file)