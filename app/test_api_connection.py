import httpx
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

platitude_url = "http://192.168.3.141:8000"

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            # Test connection to the vehicles endpoint
            logger.info("Testing connection to FastAPI service...")
            response = await client.get(f"{platitude_url}/vehicles/")
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text[:200]}")
            
    except Exception as e:
        logger.error(f"Error connecting to FastAPI service: {str(e)}", exc_info=True)

async def healthcheck():
    try:
        async with httpx.AsyncClient() as client:
            logger.info("Testing healthcheck")
            response = await client.get(f"{platitude_url}/health")
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text[:200]}")
            
    except Exception as e:
        logger.error(f"Error connecting to FastAPI service: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_connection())
    asyncio.run(healthcheck())