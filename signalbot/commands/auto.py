import asyncio
import json
import logging
import os
import re
from datetime import datetime

import httpx

from signalbot import SignalBot, Command, Context, regex_triggered

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
        self.platitude_url = platitude_url or os.getenv("PLATITUDE_URL")
        if not self.platitude_url:
            raise ValueError(
                "PLATITUDE_URL must be provided either as parameter or via environment variable"
            )
        logger.info(f"Initialized autoplate with URL: {self.platitude_url}")
    
    @regex_triggered(r".*")  # Match all messages for regex scanning
    async def handle(self, c: Context) -> None:
        """Handle incoming messages and detect license plates."""
        message_text = c.message.text
        
        # Search for license plate patterns in the message
        matches = PLATE_REGEX.findall(message_text)
        
        if not matches:
            return  # No plate found, ignore this message
        
        # Process each detected plate (deduplicate by converting to uppercase)
        seen_plates = set()
        for match in matches:
            plate = match.strip().upper()
            if plate and plate not in seen_plates:
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
    
