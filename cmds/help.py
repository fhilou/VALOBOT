import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Affiche la liste des commandes disponibles"""
        help_message = (
            "**Liste des commandes :**\n"
            "`!elo <username> <tag>` - Affiche l'elo d'un joueur spécifique.\n"
            "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
            "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
            "`!help` - Affiche cette aide."
        )
        await ctx.send(help_message)
