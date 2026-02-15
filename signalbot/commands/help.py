from signalbot import Command, Context, triggered
import logging

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "/plate [LICENSE PLATE] - Check if a plate is monitored\n"
    "Juntos 215-218-9079\n"
    "/help - Show this message\n"
    "Fuck ICE GO BIRDS \U0001F985"
)


class HelpCommand(Command):
    @triggered("/help")
    async def handle(self, c: Context) -> None:
        logger.debug("Help command triggered")
        await c.send(HELP_TEXT)
