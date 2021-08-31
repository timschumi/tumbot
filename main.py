#!/usr/bin/env python3

import os

from discord import Intents
from discord.ext.commands.errors import ExtensionError
from basedbot import DBot


bot = DBot(intents=Intents.all())

bot.add_cog_path('cogs')
bot.add_cog_path('cogs/legacy')

bot.db.add_sql_path('sql/guild', scope='guild')
bot.db.add_sql_path('sql/global', scope='global')

# Load all modules
for cog in bot.find_all_cogs():
    try:
        bot.load_extension(cog)
    except ExtensionError as e:
        print(e)

bot.run(os.environ['DBOT_TOKEN'])
