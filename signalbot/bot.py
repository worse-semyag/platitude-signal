import os
import re
import logging
from dotenv import load_dotenv
from signalbot import SignalBot, Command, Context, triggered, enable_console_logging, regex_triggered
import requests
import json
import httpx

from commands import platecheck, HelpCommand, report

logger = logging.getLogger(__name__)

class PingCommand(Command):
    @triggered("Ping")
    async def handle(self, c: Context) -> None:
        await c.send("Pong")





class healthcheck(Command):
    @regex_triggered(r"^/healthcheck")
    async def handle(self, c: Context) -> None:
        try:
            platitude_url = os.getenv("PLATITIDE_URL")
            response = requests.get(url=f"{platitude_url}/health")
            if response.status_code == 200:
                data = response.json()

                status = data["status"]
                database = data["database"]
                timestamp= data["timestamp"]

               
                await c.send(f"Status: {status} \nDatabase: {database} \nTimestamp: {timestamp}")
            else:
                logger.debug(response)
        except: 
            logger.warning("Unable to connect to health")
            await c.send("Unable to connect to health")

            



if __name__ == "__main__":
    # Environment variables should already be loaded by start.sh
    enable_console_logging(logging.INFO)
    platitude_url = os.getenv("PLATITIDE_URL")
    report_url = os.getenv("REPORT_URL")
    print(report_url)
    logger.info(report_url)
    signal_service = os.getenv("SIGNAL_SERVICE")
    logger.info(signal_service)
    phone_number= os.getenv("PHONE_NUMBER")
    logger.info(phone_number)


    bot = SignalBot({
        "signal_service": os.getenv("SIGNAL_SERVICE"),
        "phone_number": os.getenv("PHONE_NUMBER")
    })
    #plate_cmd = platecheck()
    #bot.register(PingCommand(),groups=["group.VDFIZ2ZZdmw3RGROTEROelNobWdpZW55MkZQRTNjRlNGU0tPZFFFOURPVT0=","group.QjFVVW16V3hKb3hLVUFjQll0RFpRbXYvdCtOWkFweGVlWi9aT1l5M29Gdz0="])
    bot.register(healthcheck())
    bot.register(PingCommand())
    bot.register(HelpCommand())
    bot.register(platecheck(platitude_url))
    bot.register(report(report_url))

    bot.start()

