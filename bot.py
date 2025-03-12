import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from keep_alive import keep_alive
from api import fetch_elo
from all_commands import setup_commands

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True  # Important pour les commandes avec préfixe !
bot = commands.Bot(command_prefix="!", intents=intents)

# Configurer les commandes
setup_commands(bot)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    print("Commandes chargées:")
    for command in bot.commands:
        print(f"- {command.name}")

# Garder le bot en vie et le lancer
keep_alive()
bot.run(TOKEN)
