import discord
import os
import json
import asyncio
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive
from datetime import datetime, time, timedelta

# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ELO_FILE = "elo_data.json"

# Décalage horaire France (UTC+1 en hiver, UTC+2 en été)
OFFSET_FRANCE = 1  # À ajuster si nécessaire

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

# Configuration du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_elo(username, tag):
    """Récupère l'elo d'un joueur via l'API HenrikDev"""
    url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{tag}/{username}"
    headers = {"Authorization": f"Bearer {HENRIKDEV_API_KEY}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data["data"].get("current_data", {}).get("elo", 0)  # Retourne l'elo actuel du joueur
    return None

@bot.command()
async def test(ctx):
    """Envoie le message du jour avec l'élo actuel des joueurs."""
    message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        elo = fetch_elo(username, player["tag"])
        if elo is None:
            message += f"{username}: Élo introuvable 🚫\n"
        else:
            message += f"{username}: {elo} RR\n"
    await ctx.send(message)

@bot.command()
async def elo(ctx, user_input: str = None):
    """Affiche l'élo actuel d'un joueur."""
    
    # Si aucun pseudo n'est donné, afficher un message d'erreur
    if user_input is None:
        await ctx.send("❌ Utilisation correcte : `!elo pseudo#tag` (ex: `!elo JokyJokSsj#EUW`)")
        return
    
    # Vérifier que le format est bien "pseudo#tag"
    if "#" not in user_input:
        await ctx.send("❌ Format invalide ! Utilise `pseudo#tag` (ex: `!elo JokyJokSsj#EUW`)")
        return
    
    username, tag = user_input.split("#", 1)  # Séparer le pseudo du tag

    elo = fetch_elo(username, tag)
    if elo is not None:
        await ctx.send(f"**{username}** a actuellement **{elo} RR**.")
    else:
        await ctx.send(f"🚫 Impossible de récupérer l'élo de **{username}** avec le tag **{tag}**.")

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

keep_alive()
bot.run(TOKEN)

