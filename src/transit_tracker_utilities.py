# transit_tracker_utlities.py

####################
# IMPORT LIBRARIES #
####################

import datetime as dt
from re import sub
from wsgiref.simple_server import sys_version
from dateutil import parser
from pytz import timezone
import pandas as pd
import requests
import json
import os
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict

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

    # Load the subway API key (Link to retrieve: https://api.mta.info/#/AccessKey)
    try: # Try to load from `secrets` folder (will not be on everyone's system)
        with open("./secrets/subway_api_key.txt") as f:
            subway_api_key = next(f)
    except: # If you don't have it set up, you will be prompted for it
        subway_api_key = input("INPUT SUBWAY API KEY: ")

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

def getSubwayStationName(subway_stop_id):
    # Load the subway station data
    subway_stops = pd.read_csv("./config/subway_stops.csv")
    subway_stops = subway_stops[subway_stops["stop_id"] == str(subway_stop_id)]
    
    # Return the name of the subway station
    return subway_stops["stop_name"].tolist()[0]

def getSubwayEndpoint(subway_line):
    # Load the endpoint data
    endpoints = pd.read_csv("./config/subway_api_endpoints.csv")
    
    # Find matching endpoint for subway line
    endpoints = endpoints[endpoints['line'] == subway_line.lower()]
    
    # Return matching endpoint
    return endpoints['endpoint'].tolist()[0]


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

    def __init__(self, bus_id, presentable_distance, dest_name):
        self.line_id = bus_id # i.e. M60SBS, Bx15, etc.
        self.status = presentable_distance # i.e. 5 stops away, approaching, at stop, etc.
        self.destination = dest_name # i.e. W. HARLEM BWAY - 125 via 3 AV

class BusStop():
    # List of closest busses
    busses = []
    # ID of the stop
    stop_id = ""
    # Plaintext stop name
    stop_name = ""
    # Direction of travel (for reference only)
    direction = ""

    def __init__(self, name, id, api_key):
        # Assign name
        self.stop_name = name

        # Assign Id
        self.stop_id = id

        # Assign direction
        self.direction = self.determineDirection()

        # Clear busses list
        self.busses = []

        # Make API call
        json_obj = self.__getBusData__(api_key)

        # Get closes three busses to stop
        closest_busses = json_obj["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"][0]['MonitoredStopVisit'][0:3]

        for bus in closest_busses:
            # Expected vs. Aimed flag
            #t_is_expected = 0

            # Bus Line ID
            t_line_id = bus["MonitoredVehicleJourney"]["LineRef"].split("_")[1]

            # Bus Status
            t_status = bus["MonitoredVehicleJourney"]["MonitoredCall"]["Extensions"]["Distances"]["PresentableDistance"]

            # Destination Name
            t_destination_name = bus['MonitoredVehicleJourney']['DestinationName']

            # Create Bus object and store in `busses` list
            self.busses.append(Bus(t_line_id, t_status, t_destination_name))

    def __getBusData__(self, api_key):
        # Gather bus data
        bus_url = f"http://bustime.mta.info/api/siri/stop-monitoring.json?key={api_key}&OperatorRef=MTA&MonitoringRef={self.stop_id}"
        bus_res = requests.request("GET", bus_url)

        # Return the JSON data
        return json.loads(bus_res.text)

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

class SubwayTrain():
    # Plaintext subway line name
    line_id = ""
    # Distance status (e.g. 5 stops away, approaching, etc.)
    status = ""
    # Plaintext destination name
    destination = ""
    # Train type (Uptown or Downtown)
    direction = ""

    def __init__(self, presentable_distance, route_id, subway_direction):
        self.line_id = route_id # i.e. 1, 7, N, etc.
        self.status = presentable_distance # i.e. 5 stops away, approaching, at stop, etc.
        self.destination = self.__getRouteText__(route_id) # i.e. 7 AVE EXPRESS
        self.direction = subway_direction # UPT or DWT

    def __getRouteText__(self, route_id):
        # Load route data
        subway_routes = pd.read_csv("./config/subway_routes.csv")
        
        # Find route name
        subway_routes = subway_routes[subway_routes['route_id'] == route_id]

        # Return route name
        return subway_routes["route_long_name"].tolist()[0]

class SubwayStation():
    # List of closest trains
    trains = []
    # ID of the station
    stop_id = ""
    # Plaintext station name
    stop_name = ""

    def __init__(self, name, id, data):
        # Assign name
        self.stop_name = name

        # Assign Id
        self.stop_id = str(id)

        # Get a dataframe with the first 5 arriving trains
        subway_data = self.__parseSubwayData__(data).head(5)

        # Clear trains list
        self.trains = []

        # Loop throuh subway data and create train objects
        for index, row in subway_data.iterrows():
            # Parse inputs from dataframe
            t_distance = self.__getPresentableDistance__(row['arrival_time'], row['departure_time'])
            t_route_id = row['route']
            t_direction = self.__getTrainDirection__(row['stop'])

            # Create train object and append to list
            self.trains.append(SubwayTrain(t_distance, t_route_id, t_direction))

    def __getTrainDirection__(self, stop):
        if stop[-1] == "N":
            return "UPT"
        else:
            return "DWT"

    def __getPresentableDistance__(self, arrivalTime, departureTime):
        curr_time = dt.datetime.now()

        if arrivalTime <= curr_time:
            if departureTime > curr_time:
                return("At station")
        elif arrivalTime >= curr_time:
            t_diff = arrivalTime - curr_time
            if t_diff.total_seconds() % 60 <= 0:
                return "<1 min"
            else:
                return f"{str(int(t_diff.total_seconds() / 60))} min"
        else:
            return("At station")

    def __parseSubwayData__(self, data):
        # Create empty lists
        stop_ids = []
        route_ids = []
        arrival_times = []
        departure_times = []

        # Loop through train data and grab info
        for train in data:
            if 'trip_update' in train:
                t_route_id = train['trip_update']['trip']['route_id']
                for stop in train['trip_update']['stop_time_update']:
                    if self.stop_id in stop['stop_id']:
                        # Grab stop id
                        stop_ids.append(stop['stop_id'])
                        
                        # Grab route id
                        route_ids.append(t_route_id)
                        
                        # Grab arrival time
                        
                        arrival_times.append(dt.datetime.fromtimestamp(stop['arrival']['time']))
                        
                        # Grab departure time
                        departure_times.append(dt.datetime.fromtimestamp(stop['departure']['time']))
            else:
                pass
        
        # Create dataframe
        train_arrival_data = pd.DataFrame()
        train_arrival_data['stop'] = stop_ids
        train_arrival_data['route'] = route_ids
        train_arrival_data['arrival_time'] = arrival_times
        train_arrival_data['departure_time'] = departure_times

        # Sort data by arrival time
        train_arrival_data = train_arrival_data.sort_values(by=['arrival_time'])

        # Return sorted data by arrival time
        return train_arrival_data

    def determineDirection(self):
        # Load config file
        config = pd.read_csv("./config/config.csv")

        # Grab matching bus
        config = config[config['id'] == self.stop_id]

        # Return direction from config file
        return config['direction'].tolist()[0]

    def getClosestTrains(self):
        print(f"STOP: {self.stop_name} (id: {self.stop_id})\n")
        for train in self.trains:
            print(f"ID: {train.line_id}\tSTATUS: {train.status}\tDEST: {train.destination} \tDIR: {train.direction}\n")
