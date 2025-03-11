import discord
import json
import os
from discord.ext import commands
from api import fetch_elo
from datetime import datetime

ELO_FILE = "elo_data.json"

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
