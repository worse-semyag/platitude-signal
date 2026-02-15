import requests
from datetime import datetime

platitude_url= "http://127.0.0.1:8000/"
plate = "ABC123"

payload = {"code": "XYZ789"}
plate_id = "45efc6a0-3575-43af-b8e6-fb330ac281ac"
time = datetime.now()
#response = requests.post("http://localhost:8000/plates/", json=payload)
#response = requests.post(url=f"{platitude_url}/plates/", json=payload)
#print(response)
sighting_payload = {
           "longitude": -122.4194,
           "latitude": 37.7749,
           "timestamp": "2026-02-12T14:30:00Z",

           "plate_id": "45efc6a0-3575-43af-b8e6-fb330ac281ac"
         }

#response = requests.post(f"{platitude_url}/sightings/", json=sighting_payload)
#print(response)
plates = requests.get(url=f"{platitude_url}/plates/code/XYZ789")
sightings = requests.get(url=f"{platitude_url}/sightings/")
sighting_data = sightings.json()
print(sighting_data)
#print(plates)
data = plates.json()
print(data)