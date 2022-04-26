# main.py

###################
# IMPORT LIBARIES #
###################
import transit_tracker_utilities as ttu
import json
import requests
import datetime as dt
import time

#################
### VARIABLES ###
#################

# API Key
bus_api_key = "YOUR API KEY HERE"

# Load in API key
with open("./secrets/bus_api_key.txt") as f:
    bus_api_key = next(f)

# Choose bus stop
bus_stop_id = "402659" # W 125 ST/MALCOM X BLVD
        # 402507 -- 125 ST TO COLUMBIA (WEST)
        # 402659 -- 125 ST TO LAGUARDIA (EAST)
bus_stop_name = "W 125 ST/MALCOM X BLVD"

# Time between updates
sleep_time = 10

# Flag to stop the loop (will only occur if there is an error)
stop_flag = False

#########################
### MAIN PROGRAM LOOP ###
#########################

while not stop_flag:
    # Loop structure
    last_update_time = dt.datetime.now()

    # Gather bus data
    bus_url = f"http://bustime.mta.info/api/siri/stop-monitoring.json?key={bus_api_key}&OperatorRef=MTA&MonitoringRef={bus_stop_id}"
    bus_res = requests.request("GET", bus_url)
    bus_json = json.loads(bus_res.text)
    bus_stop = ttu.BusStop(json=bus_json, name=bus_stop_name, id=bus_stop_id)

    # DEBUG -- PRINT DATA
    print(f"Data as of: {last_update_time}")
    bus_stop.GetClosestBusses()
    print("_"*10)

    # Sleep for a set amount of time
    time.sleep(sleep_time)

