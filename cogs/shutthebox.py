import random
import asyncio
import discord
from discord.ext import commands

BOX_REACTIONS = [
    '1\N{COMBINING ENCLOSING KEYCAP}',
    '2\N{COMBINING ENCLOSING KEYCAP}',
    '3\N{COMBINING ENCLOSING KEYCAP}',
    '4\N{COMBINING ENCLOSING KEYCAP}',
    '5\N{COMBINING ENCLOSING KEYCAP}',
    '6\N{COMBINING ENCLOSING KEYCAP}',
    '7\N{COMBINING ENCLOSING KEYCAP}',
    '8\N{COMBINING ENCLOSING KEYCAP}',
]

NOMOVE_REACTION = '\U0000274E'


class ShutTheBoxGame:
    def __init__(self, bot, players, message):
        self._bot = bot
        self._players = players
        self._msg = message
        self._boxes = [False] * len(BOX_REACTIONS)
        self._points = [0] * len(self._players)
        self._round = 1

    @classmethod
    def _dice(cls):
        return random.randint(1, 6)

    async def _show_turn_overview(self, player, d1, d2):
        text = f"Round {self._round}, {player.mention}'s turn:\n\n"

        text += f"You have rolled the following dice: **{d1}** and **{d2}**\n\n"

        # Boxes
        for i in range(len(self._boxes)):
            if i == len(self._boxes) / 2:
                text += "\n\n"

            text += ":red_circle:\t" if self._boxes[i] else ":white_check_mark:\t"

        text += "\n\n"

        # Player points
        for i in range(len(self._players)):
            text += f"**{self._players[i]}**'s points: {self._points[i]}\n"

        await self._msg.edit(content=text)

    def _get_open_boxes(self):
        return [i for i in range(len(self._boxes)) if not self._boxes[i]]

    @classmethod
    def _get_reactions_for_boxes(cls, open_boxes):
        return [BOX_REACTIONS[i] for i in open_boxes] + [NOMOVE_REACTION]

    async def _ask_for_box(self, player, reactions):
        p = await self._bot.wait_for('raw_reaction_add',
                                     check=lambda p: p.user_id == player.id and p.emoji.name in reactions,
                                     timeout=60)

        await self._msg.remove_reaction(p.emoji.name, player)

        return p.emoji.name

    async def _play_player_round(self, i):
        d1 = self._dice()
        d2 = self._dice()
        await self._show_turn_overview(self._players[i], d1, d2)

        open_boxes = self._get_open_boxes()
        reactions = self._get_reactions_for_boxes(open_boxes)

        while True:
            reaction = await self._ask_for_box(self._players[i], reactions)

            # Player aborted the move?
            if reaction == NOMOVE_REACTION:
                self._points[i] += sum([i + 1 for i in range(len(self._boxes)) if not self._boxes[i]])
                return False

            box1 = open_boxes[reactions.index(reaction)]

            reaction = await self._ask_for_box(self._players[i], filter(lambda x: x != reaction, reactions))

            # Player aborted the move?
            if reaction == NOMOVE_REACTION:
                self._points[i] += sum([i + 1 for i in range(len(self._boxes)) if not self._boxes[i]])
                return False

            box2 = open_boxes[reactions.index(reaction)]

            # Can't close the same two boxes
            if box1 == box2:
                continue

            # Make sure that boxes match up
            if box1 + box2 + 2 != d1 + d2:
                continue

            # Close boxes
            self._boxes[box1] = True
            self._boxes[box2] = True

            # Remove reactions
            await self._msg.clear_reaction(BOX_REACTIONS[box1])
            await self._msg.clear_reaction(BOX_REACTIONS[box2])

            # Check for win
            if False in self._boxes:
                return

            await self._msg.edit(content=f"**{self._players[i]}** closed all boxes and wins!")
            return True

    async def _play_round(self):
        for i in range(len(self._players)):
            if await self._play_player_round(i):
                return True

    async def run(self):
        # Reset reactions
        for r in BOX_REACTIONS + [NOMOVE_REACTION]:
            await self._msg.add_reaction(r)

        while self._round <= 8:
            if await self._play_round():
                return

            self._round += 1

        if self._points[0] == self._points[1]:
            await self._msg.edit(content="Draw! Nobody wins. Or both?")
            return

        if self._points[0] < self._points[1]:
            text = f"**{self._players[0]}** wins by points!\n\n"
        else:
            text = f"**{self._players[1]}** wins by points!\n\n"

        for i in range(len(self._players)):
            text += f"**{self._players[i]}**'s points: {self._points[i]}\n"

        await self._msg.edit(content=text)


class ShutTheBox(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        self._running_games = []

    @commands.command()
    async def challenge(self, ctx, p2: discord.Member):
        """Challange another player to a game of 'Shut the Box'"""

        p1 = ctx.author

        if p1.id is p2.id or p2.bot:
            await ctx.send("Don't you have any driends that you can play with? :(")
            return

        if p1.id in self._running_games:
            await ctx.send(f"A game for {p1.mention} is already active!")
            return

        if p2.id in self._running_games:
            await ctx.send(f"A game for {p2.mention} is already active!")
            return

        message = await ctx.send(f"{p2.mention}, you have been challenged to a round of 'Shut the Box'! "
                                 "React with \U00002705 to accept the challenge.")
        await message.add_reaction('\U00002705')

        await self._bot.wait_for('raw_reaction_add',
                                 check=lambda p: p.user_id == p2.id and p.emoji.name == '\U00002705',
                                 timeout=60)

        await message.clear_reactions()

        game = ShutTheBoxGame(self._bot, [p1, p2], message)

        self._running_games.append(p1.id)

        await game.run()

        self._running_games.remove(p1.id)

    @challenge.error
    async def challenge_error(self, ctx, error):
        error = getattr(error, 'original', error)

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You can't play without any opponents :(")
            return

        if isinstance(error, asyncio.TimeoutError):
            await ctx.send("Game timed out after 60s! Try typing a little faster next time!")
            self._running_games.remove(ctx.author.id)
            return

        await self._bot.get_cog('ErrorHandler').on_command_error(ctx, error, force=True)


def setup(bot):
    bot.add_cog(ShutTheBox(bot))
