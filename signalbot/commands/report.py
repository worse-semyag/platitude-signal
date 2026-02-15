import asyncio
import json
import logging
import re
import httpx
import os

from signalbot import SignalBot, Command, Context, triggered, enable_console_logging, regex_triggered

logger = logging.getLogger(__name__)

class report(Command):
    def __init__(self, report_url=None):
        # Allow URL to be passed in or get from environment variable
        self.report_url = report_url or os.getenv("REPORT_URL")
        if not self.report_url:
            raise ValueError("REPORT_URL must be provided either as parameter or via environment variable")
        
    @regex_triggered(r"^/report")
    async def handle(self, c: Context) -> None:
        logger.debug("Request for report info detected")
        await c.react("\U0001f440")
        await c.reply(f"Please access {self.report_url}")
