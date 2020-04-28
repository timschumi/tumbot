import random as r
import asyncio
import discord
from discord.ext import commands


class ShutTheBox(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.running_games = []

    @commands.command()
    async def challenge(self, ctx, opponent: discord.Member):
        channel = ctx.channel
        player1 = ctx.author
        player2 = opponent
        playerpkt = [0, 0]
        boxes = [0, 0, 0, 0, 0, 0, 0, 0]
        runde = 1

        def checkboxes():
            sumtemp = 0
            for box in range(len(boxes)):
                if boxes[box] == 0:
                    sumtemp = sumtemp + box + 1
            return sumtemp

        def dice():
            return r.randint(1, 6)

        async def boxesmsg(rundenzahl, boxen):
            boxesmsggg = f"**Runde {rundenzahl}**\n"
            for var in range(len(boxen)):
                if boxen[var] == 0:
                    boxesmsggg = boxesmsggg + ":white_check_mark:\t\t"
                else:
                    boxesmsggg = boxesmsggg + ":red_circle:\t\t"
                if var + 1 == len(boxen) / 2:
                    boxesmsggg = boxesmsggg + "\n\n"
            await ctx.send(boxesmsggg)

        async def close_boxes(box1, box2, summe, player):
            if box1 == 0 or box2 == 0:
                oldpkt = playerpkt[player]
                for box in range(len(boxes)):
                    if boxes[box] == 0:
                        playerpkt[player] = playerpkt[player] + box + 1
                await ctx.send(f'Dir wurden **{playerpkt[player] - oldpkt}** auf dein Konto hinzugefügt.')
                return True
            elif box1 > 0 and box2 > 0 and summe == box1 + box2 and box1 != box2 \
                    and boxes[box1 - 1] == 0 and boxes[box2 - 1] == 0:
                boxes[box1 - 1] = 1
                boxes[box2 - 1] = 1
                await ctx.send(f"{box1} und {box2} erfolgreich geschlossen.")
                return True
            else:
                await ctx.send(f"{box1} und {box2} sind keine gültigen Eingaben. Überprüfe ob die Summe der Boxen mit "
                               f"deiner Summe übereinstimmt, und ob du Boxen auswählst die noch offen sind.")
                return False

        async def spielstand_ausgeben():
            if playerpkt[0] < playerpkt[1]:
                await ctx.send(f'{player1} gewinnt mit {playerpkt[0]} gegen {player2} mit {playerpkt[1]}.')
            elif playerpkt[0] > playerpkt[1]:
                await ctx.send(f'{player2} gewinnt mit {playerpkt[1]} gegen {player1} mit {playerpkt[0]}.')
            elif playerpkt[0] == playerpkt[1]:
                await ctx.send(f'Unentschieden beide Spieler haben {playerpkt[0]}')
            else:
                await ctx.send("Unerwarteter Fehler bei der Ausgabe kontaktiere bitte den Botbesitzer")

        if player1.id is player2.id:
            await channel.send("Hast du keine Freunde mit denen du spielen kannst? :(")
            return

        if player2.bot:
            await ctx.send(f"{player2.mention} gewinnt, da er die beste Strategie bereits vorberechnet hat!")
            return

        if player1.id in self.running_games:
            await ctx.send("Ein Spiel ist bereits aktiv!")
            return

        self.running_games.append(player1.id)

        await ctx.send("Hey " + opponent.mention + ' du wurdest herausgefordert zu ShuttheBox! Schreibe "accept" '
                                                      'um die Challegenge zu akzeptieren')
        await self.client.wait_for('message', check=lambda message: message.author == player2 and message.content == "accept", timeout=60)
        await channel.send(f"Spieler {player2.mention} hat die Herausforderung angenommen! \n Challenge startet!")
        # Runde starten
        while runde <= 8:
            await boxesmsg(runde, boxes)
            dice1 = dice()
            dice2 = dice()
            await ctx.send(f'{player1} hat folgende zwei Zahlen gewürfelt: **{dice1}** und **{dice2}**')
            while True:
                await ctx.send("Bitte gebe eine Box zum schließen ein")
                box1 = await self.client.wait_for('message', check=lambda message: message.author == player1,
                                                  timeout=60)
                box1 = str(box1.content)
                await ctx.send("Bitte gebe eine zweite Box zum schließen ein")
                box2 = await self.client.wait_for('message', check=lambda message: message.author == player1,
                                                  timeout=60)
                box2 = str(box2.content)
                if box1.isdigit() and box2.isdigit():
                    checker1 = await close_boxes(int(box1), int(box2), summe=dice1 + dice2, player=0)
                    if checker1 is True:
                        break
                else:
                    await ctx.send(f'Ungültige Eingabe!')
            if checkboxes() == 0:
                await ctx.send(f'{player1} hat gewonnen!')
                self.running_games.remove(ctx.author.id)
                return

            await boxesmsg(runde, boxes)
            dice1 = dice()
            dice2 = dice()
            await ctx.send(f'{player2} hat folgende zwei Zahlen gewürfelt: **{dice1}** und **{dice2}**')
            while True:
                await ctx.send("Bitte gebe eine Box zum schließen ein")
                box1 = await self.client.wait_for('message', check=lambda message: message.author == player2,
                                                  timeout=60)
                box1 = str(box1.content)
                await ctx.send("Bitte gebe eine zweite Box zum schließen ein")
                box2 = await self.client.wait_for('message', check=lambda message: message.author == player2,
                                                  timeout=60)
                box2 = str(box2.content)
                if box1.isdigit() and box2.isdigit():
                    checker2 = await close_boxes(int(box1), int(box2), summe=dice1 + dice2, player=1)
                    if checker2 is True:
                        break
                else:
                    await ctx.send(f'Ungültige Eingabe!')
            if checkboxes() == 0:
                await ctx.send(f'{player2} hat gewonnen!')
                self.running_games.remove(ctx.author.id)
                return

            runde += 1
        await spielstand_ausgeben()
        self.running_games.remove(ctx.author.id)


    @challenge.error
    async def challenge_error(self, ctx, error):
        error = getattr(error, 'original', error)

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Ohne Gegner kannst du nicht spielen :(")
            return

        if isinstance(error, asyncio.TimeoutError):
            await ctx.send("Game timed out after 60s! Try typing a little faster next time!")
            self.running_games.remove(ctx.author.id)
            return

        await self.client.get_cog('ErrorHandler').on_command_error(ctx, error, force=True)


def setup(client):
    client.add_cog(ShutTheBox(client))
