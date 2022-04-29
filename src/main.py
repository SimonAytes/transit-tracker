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
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict

#################
### VARIABLES ###
#################

# Load in API keys
bus_api_key, subway_api_key = ttu.getAPIKey()

# Load in bus and subway ids
bus_stop_id, subway_stop_id = ttu.getConfig()

print(f"BUS : {bus_stop_id} \t SUBWAY : {subway_stop_id}")

# NOTE: Bus stops are as follows
# W 125 ST/MALCOM X BLVD
# 402507 -- 125 ST TO COLUMBIA (WEST)
# 402659 -- 125 ST TO LAGUARDIA (EAST)

bus_stop_name = ttu.getBusStopName(bus_stop_id)
subway_station_name = ttu.getSubwayStationName(subway_stop_id)

print(f"SUBWAY STATION NAME: {subway_station_name}")

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
        # Gather bus data & make bus stop object
        bus_stop = ttu.BusStop(name=bus_stop_name, id=bus_stop_id, api_key=bus_api_key)

        # Gather subway data
        subway_headers = {"x-api-key": subway_api_key}
        subway_url = ttu.getSubwayEndpoint("2")
        subway_res = requests.request("GET", subway_url, headers=subway_headers)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(subway_res.content)
        subway_feed = protobuf_to_dict(feed) # subway_feed is a dictionary
        subway_json = subway_feed['entity'] # train_data is a list

        # Create subway station object
        subway_station = ttu.SubwayStation(name=subway_station_name, id=subway_stop_id, data=subway_json)

        # Log time of last update
        last_update_time = dt.datetime.now()

        # DEBUG -- PRINT DATA
        print(f"Data as of: {last_update_time}\n")
        print("BUS SCHEDULE \n\n")
        bus_stop.getClosestBusses()
        print("TRAIN SCHEDULE \n\n")
        subway_station.getClosestTrains()
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
        #stop_flag = True

