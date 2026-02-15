import requests
from datetime import datetime
import csv

platitude_url= "http://192.168.3.141:8000/"

def create_plate(url, plate_data):
    """Create a new plate entry"""
    response = requests.post(f"{url}plates/", json=plate_data)
    return response.json()

def get_plate_by_code(url, code):
    """Get plate data by code"""
    response = requests.get(f"{url}plates/code/{code}")
    return response.json()

def create_vehicle(url, vehicle_data):
    """Create a new vehicle entry"""
    response = requests.post(f"{url}/vehicles/", json=vehicle_data)
    return response.json()

def create_sighting(url, sighting_data):
    """Create a new sighting entry"""
    response = requests.post(f"{url}/sightings/", json=sighting_data)
    return response.json()

# Test data
plate1 = {"code": "XYZ789"}
plate2 = {"code": "ABC123"}

###POST TEST PLATES
plate1_data = create_plate(platitude_url, plate1)
plate2_data = create_plate(platitude_url, plate2)

#GET TEST PLATES FOR TEST SIGHTINGS 
plate1data = get_plate_by_code(platitude_url, "XYZ789")
plate2data = get_plate_by_code(platitude_url, "ABC123")

print(plate1data)
plate1_id = plate1data["id"]
plate1_sighting1 = {
           "longitude": -122.4194,
           "latitude": 37.7749,
           "timestamp": "2026-02-12T14:30:00Z",
           "plate_id": plate1_id
         }

plate1_sighting2 = {
           "longitude": -133.4194,
           "latitude": 38.7749,
           "timestamp": "2026-02-10T06:30:00Z",
           "plate_id": plate1_id
         }

plate2_id = plate2data["id"]

plate2_vehice = {
           "make": "Ford",
           "model": "Focus",
           "year": "2019",
           "color": "red"
         }
vehicle_json = create_vehicle(platitude_url, plate2_vehice)
print(type(vehicle_json))
print(vehicle_json['id'])
plate2_vehicle_id = vehicle_json['id']
print(type(plate2_vehicle_id))





plate2_sighting1 = {
           "longitude": -133.4194,
           "latitude": 38.7749,
           "timestamp": "2026-02-10T06:30:00Z",
           "plate_id": plate2_id,
            "vehicle_id": plate2_vehicle_id,
         }

# Create sightings using the new function
create_sighting(platitude_url, plate1_sighting1)
create_sighting(platitude_url, plate1_sighting2)
create_sighting(platitude_url, plate2_sighting1)

#print(response)
#plates = requests.get(url=f"{platitude_url}/plates/code/XYZ789")
sightings = requests.get(url=f"{platitude_url}/sightings/")
#sighting_data = sightings.json()
#print(sighting_data)
#print(plates)
#data = plates.json()
#print(data)
