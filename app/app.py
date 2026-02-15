import sqlite3
from flask import Flask, render_template, request, Response, redirect, url_for, send_from_directory
from datetime import datetime
import asyncio
import requests
import httpx
import logging

# Set up logging with more detailed configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

platitude_url = "http://192.168.3.141:8000"

app = Flask(__name__)

async def post_sighting(submission) -> dict:
    # Get form data from submission
    plate_code = submission.get("platecode")
    timestamp = submission.get("sighttime")
    latitude = submission.get("latitude") 
    longitude = submission.get("longitude")
    
    vehicle_id = None
    
    # Check if vehicle data exists  
    has_vehicle_data = any(k in submission for k in ("vehiclemake","vehiclemodel","vehiclecolor","vehicleyear"))
    
    try:
        logger.info(f"Starting post_sighting with submission: {submission}")
        async with httpx.AsyncClient() as client:
            # Step 1: If vehicle data exists, post vehicle and get vehicle_id
            if has_vehicle_data:
                vehicle_json = {
                    "make": submission.get("vehiclemake"),
                    "model": submission.get("vehiclemodel"), 
                    "year": submission.get("vehicleyear"),
                    "color": submission.get("vehiclecolor")
                }
                logger.info(f"Attempting to create vehicle with data: {vehicle_json}")
                try:
                    vehicle_response = await client.post(f"{platitude_url}/vehicles/", json=vehicle_json)
                    logger.info(f"Vehicle creation response status: {vehicle_response.status_code}, text: {vehicle_response.text[:200]}")
                    if vehicle_response.status_code != 201:
                        return {"error": f"Failed to create vehicle - Status: {vehicle_response.status_code}, Response: {vehicle_response.text}"}
                    
                    vehicle_data = vehicle_response.json()
                    vehicle_id = vehicle_data.get("id")
                    logger.info(f"Vehicle created successfully with ID: {vehicle_id}")
                except Exception as e:
                    logger.error(f"Error creating vehicle: {str(e)}", exc_info=True)
                    return {"error": f"Vehicle creation error: {str(e)}"}
            
            # Step 2: Post plate and get plate_id (with vehicle_id if it exists)
            plate_json = {"code": plate_code}
            if vehicle_id:
                plate_json["vehicle_id"] = vehicle_id
                
            logger.info(f"Attempting to create plate: {plate_code} with data: {plate_json}")
            try:
                plate_response = await client.post(f"{platitude_url}/plates/", json=plate_json)
                logger.info(f"Plate creation response status: {plate_response.status_code}, text: {plate_response.text[:200]}")
                if plate_response.status_code != 201:
                    return {"error": f"Failed to create plate - Status: {plate_response.status_code}, Response: {plate_response.text}"}
                
                plate_data = plate_response.json()
                plate_id = plate_data.get("id")
                logger.info(f"Plate created successfully with ID: {plate_id}")
            except Exception as e:
                logger.error(f"Error creating plate: {str(e)}", exc_info=True)
                return {"error": f"Plate creation error: {str(e)}"}
            
            # Step 3: Post sighting with plate_id and optional vehicle_id
            sighting_json = {
                "longitude": float(longitude),
                "latitude": float(latitude), 
                "timestamp": timestamp,
                "plate_id": plate_id,
                "vehicle_id": vehicle_id
            }
            logger.info(f"Attempting to create sighting with data: {sighting_json}")
            try:
                sighting_response = await client.post(f"{platitude_url}/sightings/", json=sighting_json)
                logger.info(f"Sighting creation response status: {sighting_response.status_code}, text: {sighting_response.text[:200]}")
                if sighting_response.status_code != 201:
                    return {"error": f"Failed to create sighting - Status: {sighting_response.status_code}, Response: {sighting_response.text}"}
                
                logger.info("Sighting created successfully")
                return {
                    "success": True,
                    "plate_id": plate_id,
                    "vehicle_id": vehicle_id
                }
            except Exception as e:
                logger.error(f"Error creating sighting: {str(e)}", exc_info=True)
                return {"error": f"Sighting creation error: {str(e)}"}
                
    except httpx.RequestError as e:
        logger.error(f"HTTP request error in post_sighting: {str(e)}")
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        logger.error(f"General error in post_sighting: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.route('/read_form', methods=['POST'])
def read_form():
    # Get data from the form submission 
    submission = {
        "platecode": request.form.get("platecode"),
        "sighttime": request.form.get("sighttime"),  
        "latitude": request.form.get("latitude"),
        "longitude": request.form.get("longitude"),
        "vehiclemake": request.form.get("vehiclemake"),
        "vehiclemodel": request.form.get("vehiclemodel"),
        "vehiclecolor": request.form.get("vehiclecolor"),
        "vehicleyear": request.form.get("vehicleyear")
    }
    
    logger.info(f"Form submission received: {submission}")
    
    # Process the sighting asynchronously
    result = asyncio.run(post_sighting(submission))
    
    if "error" in result:
        logger.error(f"Error processing form submission: {result['error']}")
        return f"Error: {result['error']}"

    logger.info("Form submission processed successfully")
    return "Sighting submitted successfully!"


@app.route('/report')
def show_report():
    return render_template('report.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
