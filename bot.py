import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from api import fetch_elo
import commands.elo
import commands.recap
import commands.test
import commands.help


# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Ajouter les commandes
bot.add_cog(commands.elo.Elo(bot))
bot.add_cog(commands.recap.Recap(bot))
bot.add_cog(commands.test.Test(bot))
bot.add_cog(commands.help.Help(bot))

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

# Garder le bot en vie et le lancer
keep_alive()
bot.run(TOKEN)

