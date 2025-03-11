import discord
import os
import json
import asyncio
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive
from datetime import datetime, time

# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
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
    target_time = time(10, 0)  # Heure de l'envoi (9h00 du matin)
    if now.hour == target_time.hour and now.minute == target_time.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            elo_data = load_elo_data()
            message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
            for player in TRACKED_PLAYERS:
                username = player["username"]
                new_elo = fetch_elo(username, player["tag"])
                if new_elo is not None:
                    message += f"{username}: {new_elo} RR\n"
            await channel.send(message)

@bot.command()
async def recap(ctx):
    """Affiche le récapitulatif des changements d'elo."""
    elo_data = load_elo_data()
    message = "**Récapitulatif des gains/pertes d'elo aujourd'hui :**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        old_elo = elo_data.get(username, 0)
        new_elo = fetch_elo(username, player["tag"])
        if new_elo is not None:
            diff = new_elo - old_elo
            message += f"{username}: {'+' if diff >= 0 else ''}{diff} RR\n"
            elo_data[username] = new_elo  # Mettre à jour l'elo après le calcul
    save_elo_data(elo_data)
    await ctx.send(message)

@bot.command()
async def test(ctx):
    """Envoie le message du jour avec l'élo actuel des joueurs."""
    elo_data = load_elo_data()
    message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        new_elo = fetch_elo(username, player["tag"])
        if new_elo is not None:
            message += f"{username}: {new_elo} RR\n"
    await ctx.send(message)

@bot.command()
async def help(ctx):
    """Affiche la liste des commandes disponibles."""
    help_message = (
        "**Liste des commandes :**\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
        "`!help` - Affiche cette aide."
    )
    await ctx.send(help_message)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    scheduled_message.start()  # Démarrer l'envoi programmé

keep_alive()
bot.run(TOKEN)


