import asyncio
import json
import logging
import re
import httpx
import os
from datetime import datetime

from signalbot import SignalBot, Command, Context, triggered, enable_console_logging, regex_triggered

logger = logging.getLogger(__name__)

class platecheck(Command):
    def __init__(self, platitude_url=None):
        # Allow URL to be passed in or get from environment variable
        self.platitude_url = platitude_url or os.getenv("PLATITIDE_URL")
        if not self.platitude_url:
            raise ValueError("PLATITIDE_URL must be provided either as parameter or via environment variable")
        logger.info(f"Initialized platecheck with URL: {self.platitude_url}")
    
    @regex_triggered(r"^/platecheck\b")
    async def handle(self, c: Context) -> None:
        await c.react("\U0001f440")
        parts = c.message.text.split(maxsplit=1)
        has_text = len(parts) > 1 and parts[1].strip()
        logger.debug("HAS TEXT")
        if not has_text:
            await c.reply("No plate detected in message")
            return

        raw_plate = parts[1].strip().upper()
        logger.info(f"Processing plate check for: {raw_plate}")
        await self._process_plate_check(c, raw_plate)
    
    async def _process_plate_check(self, c: Context, raw_plate: str) -> None:
        """Process the plate check logic"""
        # Check if plate has been entered into DB
        try: 
            logger.info(f"Making request to plates endpoint for plate: {raw_plate}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.platitude_url}/plates/code/{raw_plate}"
                logger.debug(f"Request URL: {url}")
                response = await client.get(url)
                logger.info(f"Response status code: {response.status_code}")
                logger.debug(f"Response text: {response.text[:200]}...")  # First 200 chars
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Got plate data with {len(data)} entries")
                plate_id = data[0]["id"]
                plate_code = data[0]["code"]
                logger.info(f"GOT PLATE {plate_code} with ID: {plate_id}")
                await self._handle_plate_found(c, plate_id, plate_code)
            else: 
                logger.warning(f"Plate not found. Status code: {response.status_code}, Response: {response.text[:100]}...")
                await c.reply("No Plate Found")

        except httpx.TimeoutException:
            logger.error("Timeout connecting to Platitude Platecheck - request took too long")
            await c.reply("Unable to connect to Platitude: Request timed out. Try again later.")
        except httpx.NetworkError:
            logger.error("Network error connecting to Platitude Platecheck")
            await c.reply("Unable to connect to Platitude: Network error. Check your connection and try again later.")
        except Exception as e:
            logger.exception(f"Unexpected error in _process_plate_check: {e}")
            await c.reply("Unable to connect to Platitude try again later.")
    
    async def _handle_plate_found(self, c: Context, plate_id: str, plate_code: str) -> None:
        """Handle the case when a plate is found in database"""
        logger.info(f"Handling plate found for ID: {plate_id}, code: {plate_code}")
        # If plate has been found we look for sightings
        try:
            logger.info("Making request to sightings endpoint")
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.platitude_url}/sightings/plate/{plate_id}"
                logger.debug(f"Request URL: {url}")
                sight_response = await client.get(url)
                logger.info(f"Sightings response status code: {sight_response.status_code}")
                logger.debug(f"Sightings response text: {sight_response.text[:200]}...")  # First 200 chars
                
                if sight_response.status_code == 200: 
                    sighting = sight_response.json()
                    logger.info(f"Got {len(sighting)} sightings")
                    logger.debug(f"Sightings data: {sighting}")
                    return await self._handle_sightings(c, sighting, plate_code)
                else:
                    logger.warning(f"No sightings found. Status code: {sight_response.status_code}, Response: {sight_response.text[:100]}...")
                    await c.send(f"No Sightings found for plate {plate_code} please use /plateadd to add the plate")
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Platitude Platecheck during sightings request - request took too long")
            await c.reply("Unable to connect to Platitude: Request timed out. Try again later.")
        except httpx.NetworkError:
            logger.error("Network error connecting to Platitude Platecheck during sightings request")
            await c.reply("Unable to connect to Platitude: Network error. Check your connection and try again later.")
        except Exception as e:
            logger.exception(f"Unexpected error in _handle_plate_found: {e}")
            await c.reply("Unable to connect to Platitude try again later.")
    
    async def _handle_sightings(self, c: Context, sighting: list, plate_code: str) -> None:
        """Handle formatting and sending of sighting information"""
        sightings_formatted = []
        vehicle_info = None
        
        logger.info(f"Processing {len(sighting)} sightings for plate {plate_code}")
        # Get vehicle info if available
        if sighting[0].get("vehicle_id") is not None:
            vehicle_id = sighting[0]['vehicle_id']
            logger.debug("VEHICLE_ID " + vehicle_id)
            try:
                logger.info(f"Making request to vehicles endpoint for ID: {vehicle_id}")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"{self.platitude_url}/vehicles/{vehicle_id}"
                    logger.debug("GETTING VEHICLE")
                    logger.debug(f"Request URL: {url}") 
                    vehicle_response = await client.get(url)
                    logger.info(f"Vehicle response status code: {vehicle_response.status_code}")
                    logger.debug(f"Vehicle response text: {vehicle_response.text[:200]}...")  # First 200 chars
                    vehicle_info = vehicle_response.json()
            except httpx.TimeoutException:
                logger.error("Timeout connecting to Platitude Platecheck during vehicle request - request took too long")
                await c.reply("Unable to connect to Platitude: Request timed out. Try again later.")
            except httpx.NetworkError:
                logger.error("Network error connecting to Platitude Platecheck during vehicle request")
                await c.reply("Unable to connect to Platitude: Network error. Check your connection and try again later.")
            except Exception as e:
                logger.exception(f"Unexpected error fetching vehicle info: {e}")
        else: 
            logger.debug("NO VEHICLEID")

        # Format sightings to look nice in signal
        logger.debug("STARTING SIGHTINGS LOOP")
        for s in sighting:
            longitude = s["longitude"]
            latitude = s["latitude"]
            #timestamp = s["timestamp"]
            timestamp_raw = datetime.fromisoformat(s["timestamp"])
            logger.info(f"{type(timestamp_raw)}")
            timestamp =timestamp_raw.strftime("%I:%M %p on %b %d, %Y")
            plate= plate_code
            #vehicle = s.get("vehicle_id", "unknown")
            logger.info(f"{type(timestamp)}")
            line = (f"**Location**:{longitude},{latitude} || **Time**:{timestamp}")
            sightings_formatted.append(line)
            logger.debug("LOOP")
        
        # Format vehicle info
        logger.debug("FORMATTING VEHICLE INFO")
        logger.debug(vehicle_info)
        if vehicle_info is not None: 
            vehicle_msg = (
                f"**Make** {vehicle_info.get('make', 'unknown')}\n"
                f"**Model**  {vehicle_info.get('model', 'unknown')}\n"
                f"**Color**  {vehicle_info.get('color', 'unknown')}"
            )
        else: 
            vehicle_msg = "VEHICLE INFO UNKNOWN"
        logger.debug(vehicle_msg)
        
        msg = "\n\n".join(f"{loc},{time}" for loc, time in sightings_formatted)
        logger.debug(f"MSG: {msg}")
        
        # Send appropriate message based on number of sightings
        if len(sighting) == 1:
            await c.send(f"--**1 Sighting found**--\n**Plate**: {plate}\n{vehicle_msg}\n{msg}",text_mode="styled")
        elif len(sighting) > 1:
            await c.send(f"--**{len(sighting)} Sightings found**\n**Plate**: {plate}\n{vehicle_msg}\n{msg}",text_mode="styled")
