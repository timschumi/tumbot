#!/usr/bin/env python3

import os
import discord
from bot import Bot

bot = Bot(command_prefix='!')
bot.load_extension('plugins.quotes')
bot.load_extension('plugins.mensa')
bot.load_extension('plugins.status')
bot.run(os.environ['TUMBOT_TOKEN'])