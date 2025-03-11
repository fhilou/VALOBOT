import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from api import fetch_elo
from commands.elo import Elo
from commands.recap import Recap
from commands.test import Test
from commands.help import Help

# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Ajouter les commandes
bot.add_cog(Elo(bot))
bot.add_cog(Recap(bot))
bot.add_cog(Test(bot))
bot.add_cog(Help(bot))

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

# Garder le bot en vie et le lancer
keep_alive()
bot.run(TOKEN)

