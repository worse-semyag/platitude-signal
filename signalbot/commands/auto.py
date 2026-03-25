import asyncio
import json
import logging
import os
import re
from datetime import datetime

import httpx

from signalbot import SignalBot, Command, Context, triggered, regex_triggered

logger = logging.getLogger(__name__)

# Standard US license plate patterns
PLATE_PATTERNS = [
    # AAA1234 (3 letters + 4 digits) - most common
    r'[A-Z]{3}\d{4}',
    # A1B1C11 (alternating letter/digit)
    r'[A-Z]\d[A-Z]\d\d\d',
    # AA123456 (2 letters + 6 digits)
    r'[A-Z]{2}\d{6}',
    # 1234AAA (4 digits + 3 letters)
    r'\d{4}[A-Z]{3}',
]

# Combined regex pattern for US license plates
PLATE_REGEX = re.compile('|'.join(PLATE_PATTERNS))


class autoplate(Command):
    """Auto-detect and check license plates in messages against the Platitude database."""
    
    def __init__(self, platitude_url=None):
        # Allow URL to be passed in or get from environment variable
        self.platitude_url = (platitude_url or os.getenv("PLATITUDE_URL")).strip() if (platitude_url or os.getenv("PLATITUDE_URL")) else None
        if not self.platitude_url:
            raise ValueError(
                "PLATITUDE_URL must be provided either as parameter or via environment variable"
            )
        logger.info(f"Initialized autoplate with URL: {self.platitude_url}")

    @regex_triggered(r"[A-Z]{3}\d{4}")
    async def handle(self, c: Context) -> None:
        """Handle incoming messages and detect license plates."""
        message_text = c.message.text
        print("AUTO WORKING" + message_text)
        # Search for license plate patterns in the message
        matches = PLATE_REGEX.findall(message_text)
        
        if not matches:
            logger.info("No matches")
            return  # No plate found, ignore this message
        
        # Process each detected plate (deduplicate by converting to uppercase)
        seen_plates = set()
        for match in matches:
            plate = match.strip().upper()
            if plate and plate not in seen_plates:
                logger.info("Auto looking")
                seen_plates.add(plate)
                await self._process_plate(c, plate)
    
    async def _log_success(self, message: str):
        """Log success messages to console."""
        logger.info(message)
    
    async def _log_failure(self, message: str):
        """Log failure messages to console."""
        logger.error(message)
    
    async def _process_plate(self, c: Context, raw_plate: str) -> None:
        """Process a detected license plate - check DB or auto-add."""
        await self._check_or_add_plate(c, raw_plate)
    
    async def _check_or_add_plate(self, c: Context, raw_plate: str) -> None:
        """Check if plate exists in database, auto-add if not found."""
        try:
            # First check if plate exists using GET request
            url = f"{self.platitude_url}/plates/code/{raw_plate}"
            response = await self._request(url)
            
            if response.status_code == 200:
                data = response.json()
                await self._log_success(f"Plate {raw_plate} found in database with ID: {data.get('id')}")
                
                plate_id = data["id"]
                plate_code = data["code"]
                
                # Fetch and send sightings for this plate
                await self._fetch_and_send_sightings(c, plate_id, plate_code)
            
            else:
                # Plate not found - auto-add it to database (silently log only)
                await self._log_success(f"Auto-adding plate to database: {raw_plate}")
                await self._add_plate_to_db(raw_plate)
                
        except KeyError as e:
            await self._log_failure(f"Missing key in API response for plate {raw_plate}: {e}")
    
    async def _fetch_and_send_sightings(self, c: Context, plate_id: str, plate_code: str) -> None:
        """Fetch sightings for a plate and send them back to Signal."""
        try:
            logger.info(f"Fetching sightings for plate ID: {plate_id}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.platitude_url}/sightings/plate/{plate_id}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    sightings = response.json()
                    logger.info(f"Got {len(sightings)} sightings")
                    
                    # Format and send sightings back to Signal
                    formatted_msg = self._format_sightings_message(sightings, plate_code)
                    await c.send(formatted_msg, text_mode="styled")
                else:
                    logger.warning(f"No sightings found. Status code: {response.status_code}")
                    await c.send(f"No Sightings found for plate {plate_code}", text_mode="styled")
                    
        except httpx.TimeoutException:
            logger.error("Timeout fetching sightings")
            await c.send("Unable to connect to Platitude: Request timed out.", text_mode="styled")
        except httpx.NetworkError:
            logger.error("Network error fetching sightings")
            await c.send("Unable to connect to Platitude: Network error.", text_mode="styled")
        except Exception as e:
            logger.exception(f"Unexpected error fetching sightings: {e}")
            await c.send("Unable to fetch sightings. Try again later.", text_mode="styled")
    
    async def _format_sightings_message(self, sightings: list, plate_code: str) -> str:
        """Format sightings into a readable message."""
        if not sightings:
            return f"No Sightings found for plate {plate_code}"
        
        vehicle_info = None
        sighting_lines = []
        
        # Get vehicle info if available from first sighting
        if sightings and sightings[0].get("vehicle_id"):
            vehicle_id = sightings[0]['vehicle_id']
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"{self.platitude_url}/vehicles/{vehicle_id}"
                    response = await client.get(url)
                    if response.status_code == 200:
                        vehicle_info = response.json()
            except Exception:
                pass
        
        # Format each sighting
        for s in sightings:
            longitude = s.get("longitude", "unknown")
            latitude = s.get("latitude", "unknown")
            timestamp_raw = s.get("timestamp", "")
            
            try:
                if timestamp_raw:
                    timestamp_dt = datetime.fromisoformat(timestamp_raw)
                    timestamp = timestamp_dt.strftime("%I:%M %p on %b %d, %Y")
                else:
                    timestamp = "unknown time"
            except (ValueError, TypeError):
                timestamp = "unknown time"
            
            line = f"**Location**: {longitude},{latitude} || **Time**: {timestamp}"
            sighting_lines.append(line)
        
        # Format vehicle info
        if vehicle_info:
            vehicle_msg = (
                f"\n\n**Make**: {vehicle_info.get('make', 'unknown')}\n"
                f"**Model**:  {vehicle_info.get('model', 'unknown')}\n"
                f"**Color**:   {vehicle_info.get('color', 'unknown')}"
            )
        else:
            vehicle_msg = "\n\n**Vehicle Info**: Unknown"
        
        # Build final message
        msg = (
            f"--**{len(sightings)} Sighting(s) found**--\n"
            f"**Plate**: {plate_code}\n"
            + "\n".join(sighting_lines) + vehicle_msg
        )
        
        return msg
    
    async def _request(self, url: str):
        """Reusable async HTTP client with timeout for GET requests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            return await client.get(url)
    
    async def _post_request(self, url: str, data: dict) -> None:
        """Reusable async HTTP client with timeout for POST requests with JSON body."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data)
            return response
    
    async def _add_plate_to_db(self, plate: str) -> None:
        """Add new plate to database - POST request with code parameter."""
        url = f"{self.platitude_url}/plates/"
        plate_data = {"code": plate}
        response = await self._post_request(url, plate_data)
        
        if response.status_code == 201 or response.status_code == 200:
            await self._log_success(f"Successfully added plate to database: {plate}")
        else:
            await self._log_failure(
                f"Failed to add plate {plate} - Status: {response.status_code}, "
                f"Response: {response.text[:200]}"
            )