#!/usr/bin/env python3

import asyncio
import discord
import logging
import os

from discord import Intents
from discord.ext.commands.errors import ExtensionError
from basedbot import DBot


async def main():
    # pylint: disable=missing-function-docstring
    bot = DBot(intents=Intents.all())

    bot.add_cog_path('cogs')
    bot.add_cog_path('cogs/legacy')

    bot.db.add_sql_path('sql/guild', scope='guild')
    bot.db.add_sql_path('sql/global', scope='global')

    discord.utils.setup_logging()

    for cog in bot.find_all_cogs():
        try:
            await bot.load_extension(cog)
        except ExtensionError:
            logging.exception("Exception while loading cog '%s'", cog)

    async with bot:
        await bot.start(os.environ['DBOT_TOKEN'])

asyncio.run(main())
