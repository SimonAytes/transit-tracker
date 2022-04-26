# main.py

###################
# IMPORT LIBARIES #
###################
import transit_tracker_utilities as ttu
import json
import requests
import datetime as dt
import time
import pandas as pd

#################
### VARIABLES ###
#################

# Load in API keys
bus_api_key, subway_api_key = ttu.getAPIKey()

# Load in bus and subway ids
bus_stop_id, subway_stop_id = ttu.getConfig()

# NOTE: Bus stops are as follows
# W 125 ST/MALCOM X BLVD
# 402507 -- 125 ST TO COLUMBIA (WEST)
# 402659 -- 125 ST TO LAGUARDIA (EAST)

bus_stop_name = ttu.getBusStopName(bus_stop_id)
subway_station_name = "TO DO"

# Time between updates
sleep_time = 10

# Flag to stop the loop (will only occur if there is an error)
stop_flag = False

#########################
### MAIN PROGRAM LOOP ###
#########################

# This loop will run every n-seconds until the program is quit or the stop flag is set to True
while not stop_flag:
    # Only run the main loop if there are no errors
    try:
        # Gather bus data
        bus_url = f"http://bustime.mta.info/api/siri/stop-monitoring.json?key={bus_api_key}&OperatorRef=MTA&MonitoringRef={bus_stop_id}"
        bus_res = requests.request("GET", bus_url)
        bus_json = json.loads(bus_res.text)

        # Gather subway data
        # TODO

        # Create bus stop object
        bus_stop = ttu.BusStop(json=bus_json, name=bus_stop_name, id=bus_stop_id)

        # Create subway station object
        # TODO

        # Log time of last update
        last_update_time = dt.datetime.now()

        # DEBUG -- PRINT DATA
        print(f"Data as of: {last_update_time}")
        bus_stop.getClosestBusses()
        print("-"*10)

        # Display results to screen
        # TODO

        # Sleep for a set amount of time
        time.sleep(sleep_time)
    
    # Set the stop flag as TRUE if any errors are presented
    except Exception as e:
        # Print the error
        print(f"An error has occured and Transit Tracker has stopped running. See below for a detailed error message:\n\n{e}\n\n")

        # Set stop flag as true (will terminate loop)
        stop_flag = True

