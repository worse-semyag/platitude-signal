import asyncio
import json
import logging
import re
import httpx
import os

from signalbot import SignalBot, Command, Context, triggered, enable_console_logging, regex_triggered

logger = logging.getLogger(__name__)

class platecheck(Command):
    def __init__(self, platitude_url=None):
        # Allow URL to be passed in or get from environment variable
        self.platitude_url = platitude_url or os.getenv("PLATITIDE_URL")
        if not self.platitude_url:
            raise ValueError("PLATITIDE_URL must be provided either as parameter or via environment variable")
    
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
        await self._process_plate_check(c, raw_plate)
    
    async def _process_plate_check(self, c: Context, raw_plate: str) -> None:
        """Process the plate check logic"""
        # Check if plate has been entered into DB
        try: 
            async with httpx.AsyncClient() as client:
                logger.debug(f"Checking plate at {self.platitude_url}/plates/code/{raw_plate}")
                response = await client.get(f"{self.platitude_url}/plates/code/{raw_plate}")
            
            if response.status_code == 200:
                data = response.json()
                plate_id = data["id"]
                plate_code = data["code"]
                logger.info(f"GOT PLATE {plate_code}")
                await self._handle_plate_found(c, plate_id, plate_code)
            else: 
                await c.reply("No Plate Found")
                logger.debug(response.status_code)

        except Exception as e:
            logger.error(f"Error connecting to Platitude: {e}")
            await c.reply("Unable to connect to Platitude try again later.")
    
    async def _handle_plate_found(self, c: Context, plate_id: str, plate_code: str) -> None:
        """Handle the case when a plate is found in database"""
        # If plate has been found we look for sightings
        try:
            async with httpx.AsyncClient() as client:
                sight_response = await client.get(f"{self.platitude_url}/sightings/plate/{plate_id}")
                logger.debug("SIGHTING TESTED")
                
                if sight_response.status_code == 200: 
                    sighting = sight_response.json()
                    logger.debug(sighting)
                    return await self._handle_sightings(c, sighting, plate_code)
                else:
                    await c.send(f"No Sightings found for plate {plate_code} please use /plateadd to add the plate")
        except Exception as e:
            logger.error(f"Error fetching sightings: {e}")
            await c.reply("Unable to connect to Platitude try again later.")
    
    async def _handle_sightings(self, c: Context, sighting: list, plate_code: str) -> None:
        """Handle formatting and sending of sighting information"""
        sightings_formatted = []
        vehicle_info = None
        
        # Get vehicle info if available
        if sighting[0].get("vehicle_id") is not None:
            vehicle_id = sighting[0]['vehicle_id']
            logger.debug("VEHICLE_ID " + vehicle_id)
            try:
                async with httpx.AsyncClient() as client:
                    logger.debug("GETTING VEHICLE")
                    vehicle_response = await client.get(f"{self.platitude_url}/vehicles/{vehicle_id}")
                    logger.debug("GOT VEHICLE")
                    logger.debug(vehicle_response)
                    vehicle_info = vehicle_response.json()
            except Exception as e:
                logger.error(f"Error fetching vehicle info: {e}")
        else: 
            logger.debug("NO VEHICLEID")

        # Format sightings to look nice in signal
        logger.debug("STARTING SIGHTINGS LOOP")
        for s in sighting:
            longitude = s["longitude"]
            latitude = s["latitude"]
            timestamp = s["timestamp"]
            plate= plate_code
            #vehicle = s.get("vehicle_id", "unknown")
            
            line = (f"Location:{longitude},{latitude}", f" || Time:{timestamp}")
            sightings_formatted.append(line)
            logger.debug("LOOP")
        
        # Format vehicle info
        logger.debug("FORMATTING VEHICLE INFO")
        logger.debug(vehicle_info)
        if vehicle_info is not None: 
            vehicle_msg = (
                f"Make {vehicle_info.get('make', 'unknown')}\n"
                f"Model  {vehicle_info.get('model', 'unknown')}\n"
                f"Color  {vehicle_info.get('color', 'unknown')}"
            )
        else: 
            vehicle_msg = "VEHICLE INFO UNKNOWN"
        logger.debug(vehicle_msg)
        
        msg = "\n\n".join(f"{loc},{time}" for loc, time in sightings_formatted)
        logger.debug(f"MSG: {msg}")
        
        # Send appropriate message based on number of sightings
        if len(sighting) == 1:
            await c.send(f"One Sighting found\nPlate: {plate}\n{vehicle_msg}\n{msg}")
        elif len(sighting) > 1:
            await c.send(f"Multiple Sightings found\nPlate: {plate}\n{vehicle_msg}\n{msg}")