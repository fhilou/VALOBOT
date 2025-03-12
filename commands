# all_commands.py - Regroupement de toutes les commandes

import discord
import json
import os
from discord.ext import commands
from api import fetch_elo
from datetime import datetime

ELO_FILE = "elo_data.json"

# Liste des joueurs suivis
TRACKED_PLAYERS = [
    {"username": "JokyJokSsj", "tag": "EUW"},
    {"username": "HUNGRYCHARLY", "tag": "EUW"},
    {"username": "igosano", "tag": "24863"},
    {"username": "Irû", "tag": "3004"},
    {"username": "EmilyInTheRift", "tag": "2107A"},  
    {"username": "ANEMONIA", "tag": "EUW"},
    {"username": "Hartware", "tag": "EUW"},
]

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

class Recap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def load_elo_data(self):
        """Charge les données d'elo enregistrées."""
        if os.path.exists(ELO_FILE):
            with open(ELO_FILE, "r") as file:
                return json.load(file)
        return {}
    
    def save_elo_data(self, data):
        """Sauvegarde les nouvelles valeurs d'elo."""
        with open(ELO_FILE, "w") as file:
            json.dump(data, file, indent=4)
    
    @commands.command()
    async def recap(self, ctx):
        """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
        elo_data = self.load_elo_data()
        message = "**Récapitulatif des gains/pertes d'elo aujourd'hui :**\n"
        
        for player in elo_data.keys():
            old_elo = elo_data[player]["start"]
            new_elo = fetch_elo(player, elo_data[player]["tag"])
            
            if new_elo is not None:
                diff = new_elo - old_elo
                message += f"{player}: {'+' if diff >= 0 else ''}{diff} RR\n"
                elo_data[player]["current"] = new_elo
            else:
                message += f"{player}: 0 RR (pas de parties jouées)\n"
        self.save_elo_data(elo_data)
        await ctx.send(message)

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

# Fonction pour ajouter toutes les commandes au bot
def setup_commands(bot):
    bot.add_cog(Elo(bot))
    bot.add_cog(Recap(bot))
    bot.add_cog(Test(bot))
    bot.add_cog(Help(bot))
    return True
