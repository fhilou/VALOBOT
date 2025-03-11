import discord
from discord.ext import commands
from api import fetch_elo

class Elo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def elo(self, ctx, username: str, tag: str):
        """Affiche l'elo d'un joueur spécifique"""
        elo = fetch_elo(username, tag)
        if elo is not None:
            await ctx.send(f"**{username}#{tag}** a un elo de **{elo} RR**.")
        else:
            await ctx.send(f"Impossible de récupérer l'élo de **{username}#{tag}**.")
