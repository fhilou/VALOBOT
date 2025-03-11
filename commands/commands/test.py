import discord
from discord.ext import commands
from api import fetch_elo

TRACKED_PLAYERS = [
    {"username": "JokyJokSsj", "tag": "EUW"},
    {"username": "HUNGRYCHARLY", "tag": "EUW"},
    {"username": "igosano", "tag": "24863"},
    {"username": "Irû", "tag": "3004"},
    {"username": "EmilyInTheRift", "tag": "2107A"},  
    {"username": "ANEMONIA", "tag": "EUW"},
    {"username": "Hartware", "tag": "EUW"},
]

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        """Envoie le message du matin avec l'elo des joueurs"""
        message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
        for player in TRACKED_PLAYERS:
            username = player["username"]
            tag = player["tag"]
            elo = fetch_elo(username, tag)
            message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"

        await ctx.send(message)
