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
    url = f"https://api.henrikdev.xyz/valorant/v2/mmr/{tag}/{username}"
    headers = {"Authorization": f"Bearer {HENRIKDEV_API_KEY}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["data"].get("elo", 0)  # Retourne l'elo actuel du joueur
    return None

def fetch_daily_games(username, tag):
    """Récupère les parties jouées depuis minuit heure française"""
    url = f"https://api.henrikdev.xyz/valorant/v3/matches/{tag}/{username}?filter=competitive"
    headers = {"Authorization": f"Bearer {HENRIKDEV_API_KEY}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        games = data.get("data", [])

        # Calculer l'heure de minuit en France en UTC
        france_now = datetime.utcnow() + timedelta(hours=OFFSET_FRANCE)
        midnight_france = datetime(france_now.year, france_now.month, france_now.day, 0, 0)
        midnight_utc = midnight_france - timedelta(hours=OFFSET_FRANCE)

        daily_games = [g for g in games if datetime.strptime(g["metadata"]["game_start_patched"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None) >= midnight_utc]
        return daily_games
    return []

def calculate_daily_rr(username, tag):
    """Calcule l'elo gagné/perdu aujourd'hui"""
    games = fetch_daily_games(username, tag)
    total_rr = sum(g["players"]["all_players"][0]["currenttier_patched"] for g in games)
    return total_rr if games else 0

def load_elo_data():
    """Charge les données d'elo enregistrées."""
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, "r") as file:
            return json.load(file)
    return {}

def save_elo_data(data):
    """Sauvegarde les nouvelles valeurs d'elo."""
    with open(ELO_FILE, "w") as file:
        json.dump(data, file, indent=4)

@tasks.loop(minutes=1)
async def scheduled_message():
    """Envoie un message à une heure précise."""
    now = datetime.now().time()
    target_time = time(9, 0)  # Heure de l'envoi (9h00 du matin)
    if now.hour == target_time.hour and now.minute == target_time.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
            for player in TRACKED_PLAYERS:
                username = player["username"]
                elo = fetch_elo(username, player["tag"])
                message += f"{username}: {elo} RR\n"
            await channel.send(message)

@bot.command()
async def recap(ctx):
    """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui."""
    message = "**Récapitulatif des gains/pertes d'elo aujourd'hui :**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        rr_today = calculate_daily_rr(username, player["tag"])
        message += f"{username}: {'+' if rr_today > 0 else ''}{rr_today} RR\n"
    await ctx.send(message)

@bot.command()
async def elo(ctx, username: str = None, tag: str = None):
    """Affiche l'élo actuel d'un joueur."""
    if username is None:
        username = ctx.author.name  # Utiliser le pseudo Discord de l'utilisateur si pas de pseudo donné
        tag = "EUW"  # Mettre par défaut EUW

    elo = fetch_elo(username, tag)
    if elo is not None:
        await ctx.send(f"**{username}** a actuellement **{elo} RR**.")
    else:
        await ctx.send(f"Impossible de récupérer l'élo de {username}.")

@bot.command(name="aide")
async def aide(ctx):
    """Affiche la liste des commandes disponibles."""
    help_message = (
        "**Liste des commandes :**\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
        "`!elo [pseudo] [tag]` - Affiche l'élo d'un joueur (ex: `!elo JokyJokSsj EUW`).\n"
        "`!aide` - Affiche cette aide."
    )
    await ctx.send(help_message)

@bot.command()
async def test(ctx):
    """Envoie le message du jour avec l'élo actuel des joueurs."""
    message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        elo = fetch_elo(username, player["tag"])
        message += f"{username}: {elo} RR\n"
    await ctx.send(message)

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    scheduled_message.start()  # Démarrer l'envoi programmé

# Garder le bot en vie sur Render
keep_alive()
bot.run(TOKEN)

