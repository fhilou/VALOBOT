import discord
import os
import asyncio
import schedule
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import requests

# Charger les variables d'environnement depuis .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Joueurs suivis
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
intents.message_content = True
client = discord.Client(intents=intents)

async def get_valorant_rank(username, tag):
    url = f"https://api.henrikdev.xyz/valorant/v1/mmr/eu/{username}/{tag}"
    headers = {"Authorization": HENRIKDEV_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data["status"] == 200:
            current_rank = data["data"]["currenttierpatched"]
            rank_progress = data["data"]["ranking_in_tier"]
            elo_change = data["data"].get("mmr_change_to_last_game", "N/A")
            
            elo_change_text = f"(+{elo_change} au dernier match)" if elo_change and elo_change > 0 else f"({elo_change} au dernier match)"
            return f"{username}#{tag} est **{current_rank}** avec {rank_progress} RR {elo_change_text}"
        else:
            return f"Impossible de récupérer les données de {username}#{tag}"
    except Exception as e:
        return f"Erreur lors de la récupération des données : {e}"

async def send_daily_message():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    
    if not channel:
        print("Erreur : Channel introuvable")
        return
    
    elo_messages = await asyncio.gather(
        *[get_valorant_rank(player["username"], player["tag"]) for player in TRACKED_PLAYERS]
    )
    
    message = "**Résumé quotidien des ELO :**\n" + "\n".join(elo_messages)
    await channel.send(message)
    print("Message quotidien envoyé !")

@client.event
async def on_ready():
    print(f'Connecté en tant que {client.user}')
    schedule.every().day.at("10:33").do(lambda: asyncio.create_task(send_daily_message()))
    
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.lower() == "ping":
        await message.channel.send("Pong!")
    elif message.content.startswith("!elo"):
        parts = message.content.split()
        if len(parts) == 2 and "#" in parts[1]:
            username, tag = parts[1].split("#")
            await message.channel.send(f"Recherche de l'ELO pour {username}#{tag}...")
            elo_info = await get_valorant_rank(username, tag)
            await message.channel.send(elo_info)
        else:
            await message.channel.send("Format invalide. Utilisez `!elo Nom#Tag`")

keep_alive()
client.run(TOKEN)
