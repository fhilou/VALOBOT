import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 🔹 Chargement dynamique des commandes
for filename in os.listdir("./commands"):
    if filename.endswith(".py") and filename != "__init__.py":
        bot.load_extension(f"commands.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")

# Garder le bot actif et le lancer
keep_alive()
bot.run(TOKEN)

