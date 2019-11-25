#!/usr/bin/env python3

import os
import discord
from bot import Bot

bot = Bot(command_prefix='!')
bot.load_extension('cogs.quotes')
bot.load_extension('cogs.mensa')
bot.load_extension('cogs.status')
bot.run(os.environ['TUMBOT_TOKEN'])
