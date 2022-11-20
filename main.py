#!/usr/bin/env python3

import asyncio
import logging
import os

import discord
from discord import Intents
from discord.ext.commands.errors import ExtensionError
from basedbot import DBot


async def main():
    # pylint: disable=missing-function-docstring
    bot = DBot(intents=Intents.default())

    discord.utils.setup_logging()

    for cog in bot.find_all_cogs():
        try:
            await bot.load_extension(cog)
        except ExtensionError:
            logging.exception("Exception while loading cog '%s'", cog)

    async with bot:
        await bot.start(os.environ["DBOT_TOKEN"])


asyncio.run(main())
