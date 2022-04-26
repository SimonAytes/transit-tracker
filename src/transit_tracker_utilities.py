# transit_tracker_utlities.py

####################
# IMPORT LIBRARIES #
####################

import datetime as dt
from dateutil import parser
from pytz import timezone
import pandas as pd
import os

#####################
# UTILITY FUNCTIONS #
#####################

def getAPIKey():
    bus_api_key = ""
    subway_api_key = ""

    # Load the bus API key
    try: # Try to load from `secrets` folder (will not be on everyone's system)
        with open("./secrets/bus_api_key.txt") as f:
            bus_api_key = next(f)
    except: # If you don't have it set up, you will be prompted for it
        bus_api_key = input("INPUT BUS API KEY: ")

    # Load the subway API key
    # TODO
    subway_api_key = "TO DO"

    # Return the API keys
    return bus_api_key, subway_api_key

def getConfig():
    # Load config CSV file
    config = pd.read_csv("./config/config.csv")

    # Gather stop ids from file (index 0 is bus stop, 1 is subway)
    stop_ids = config["id"].tolist()
    
    # Return the ids
    return stop_ids[0], stop_ids[1]

def getBusStopName(bus_stop_id):
    # Load the bus stop data
    bus_stops = pd.read_csv("./config/bus_stops.csv")
    bus_stops = bus_stops[bus_stops["stop_id"] == int(bus_stop_id)]

    # Return the name of the bus stop
    return bus_stops["stop_name"].tolist()[0]


###########
# CLASSES #
###########

class Bus():
    # Plaintext bus line name
    line_id = ""
    # Distance status (e.g. 5 stops away, approaching, etc.)
    status = ""
    # Plaintext destination name
    destination = ""
    # Time from stop (seconds) -- TODO: See code in BusStop() class
    time_to_stop = 0.0
    # Flag for whether the time is based off of expected or scheduled arrival time -- TODO: See code in BusStop() class
    time_is_expected = 0

    def __init__(self, bus_id, presentable_distance, dest_name):
        self.line_id = bus_id # i.e. M60SBS, Bx15, etc.
        self.status = presentable_distance # i.e. 5 stops away, approaching, at stop, etc.
        self.destination = dest_name # i.e. W. HARLEM BWAY - 125 via 3 AV
        # self.time_to_stop = bus_time_dist # time in seconds
        # self.time_is_expected = is_expected

class BusStop():
    # List of closest busses
    busses = []
    # ID of the stop
    stop_id = ""
    # Plaintext stop name
    stop_name = ""
    # Direction of travel (for reference only)
    direction = ""

    def __init__(self, json, name, id):
        # Assign name
        self.stop_name = name

        # Assign Id
        self.stop_id = id

        # Assign direction
        self.direction = self.determineDirection()

        # Clear busses list
        self.busses = []

        # Get closes three busses to stop
        closest_busses = json["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"][0]['MonitoredStopVisit'][0:3]

        for bus in closest_busses:
            # Expected vs. Aimed flag
            #t_is_expected = 0

            # Bus Line ID
            t_line_id = bus["MonitoredVehicleJourney"]["LineRef"].split("_")[1]

            # Bus Status
            t_status = bus["MonitoredVehicleJourney"]["MonitoredCall"]["Extensions"]["Distances"]["PresentableDistance"]

            # Destination Name
            t_destination_name = bus['MonitoredVehicleJourney']['DestinationName']

            # Time to stop -- TODO: API reference was not clear and this is making no sense atm. Will try again later.
            #if "ExpectedArrivalTime" in bus["MonitoredVehicleJourney"]["MonitoredCall"]:
            #    print(bus["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedArrivalTime"])
            #    t_expected_arrival = parser.parse(bus["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedArrivalTime"])
            #    t_expected_arrival = t_expected_arrival.replace(tzinfo=timezone('EST'))
            #    t_is_expected = 1
            #else:
            #    t_expected_arrival = parser.parse(bus["MonitoredVehicleJourney"]["MonitoredCall"]["AimedArrivalTime"])
            #    t_expected_arrival = t_expected_arrival.replace(tzinfo=timezone('EST'))
            #    t_is_expected = 1
    
            #curr_time = dt.datetime.now()
            #curr_time = curr_time.replace(tzinfo=timezone('EST'))
            #self.t_time_to_stop = (t_expected_arrival - curr_time).seconds

            # Create Bus object and store in `busses` list
            #self.busses.append(Bus(t_line_id, t_status, t_expected_arrival, t_is_expected))
            self.busses.append(Bus(t_line_id, t_status, t_destination_name))

    def determineDirection(self):
        # Load config file
        config = pd.read_csv("./config/config.csv")

        # Grab matching bus
        config = config[config['id'] == self.stop_id]
        
        # Return direction from config file
        return config['direction'].tolist()[0]

    def getClosestBusses(self):
        print(f"STOP: {self.stop_name} (id: {self.stop_id})\tDIR: {self.direction}\n")
        for bus in self.busses:
            print(f"ID: {bus.line_id}\tSTATUS: {bus.status}\tDEST: {bus.destination}\n")