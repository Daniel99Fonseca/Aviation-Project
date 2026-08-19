import json
from pathlib import Path

DATA_DIR = Path("data/raw/opensky")

files = list(DATA_DIR.glob("*.json"))

total_snapshots = len(files)
total_records = 0

icao24_values = set()

missing_latitude = 0
missing_longitude = 0
missing_callsign = 0
missing_velocity = 0
missing_vertical_rate = 0

missing_vertical_rate_on_ground = 0
missing_vertical_rate_airborne = 0

on_ground_true = 0
on_ground_false = 0

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as file:
        snapshot = json.load(file)

    states = snapshot["states"] # Acessing states key
    total_records += len(states)

    for state in states:
        icao24_values.add(state["icao24"])

        if state["latitude"] is None:
            missing_latitude += 1

        if state["longitude"] is None:
            missing_longitude += 1

        if state["callsign"] is None:
            missing_callsign += 1

        if state["velocity"] is None:
            missing_velocity += 1

        if state["vertical_rate"] is None:
            missing_vertical_rate += 1

            if state["on_ground"] is True:
                missing_vertical_rate_on_ground += 1

            elif state["on_ground"] is False:
                missing_vertical_rate_airborne += 1


        if state["on_ground"] is True:
            on_ground_true += 1

        elif state["on_ground"] is False:
            on_ground_false += 1


        
        

print("Snapshots:", total_snapshots)
print("Aircraft records:", total_records)
print("Unique aircraft:", len(icao24_values))

print()
print("Missing values:")
print("Latitude:", missing_latitude)
print("Longitude:", missing_longitude)
print("Callsign:", missing_callsign)
print("Velocity:", missing_velocity)
print("Vertical rate:", missing_vertical_rate)

print()
print("On ground:")
print("True:", on_ground_true)
print("False:", on_ground_false)

print()
print("Missing vertical rate:")
print("On ground:", missing_vertical_rate_on_ground)
print("Airborne:", missing_vertical_rate_airborne)
