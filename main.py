#!/usr/bin/env python3

import os

from discord.ext.commands.errors import ExtensionError
from basedbot import DBot


bot = DBot()

# Load all modules
for cog in bot.find_all_cogs():
    try:
        bot.load_extension(cog)
    except ExtensionError as e:
        print(e)

bot.run(os.environ['DBOT_TOKEN'])
