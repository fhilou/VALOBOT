import discord
import os
import asyncio
import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

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

# Initialiser le bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Stocker les RR initiaux
daily_rr = {}

async def get_valorant_rank(username, tag):
    url = f"https://api.henrikdev.xyz/valorant/v2/mmr/eu/{username}/{tag}"
    headers = {"Authorization": HENRIKDEV_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if response.status_code == 200 and "data" in data and "currenttierpatched" in data["data"]:
            current_rank = data["data"]["currenttierpatched"]
            rank_progress = data["data"]["ranking_in_tier"]
            elo_change = data["data"].get("mmr_change_to_last_game", 0)
            
            return {"rank": current_rank, "rr": rank_progress, "elo_change": elo_change}
        else:
            return None
    except Exception as e:
        print(f"Erreur API pour {username}#{tag} : {e}")
        return None

@tasks.loop(time=datetime.time(0, 0))  # Minuit
async def save_daily_rr():
    global daily_rr
    daily_rr = {}
    
    for player in TRACKED_PLAYERS:
        rank_info = await get_valorant_rank(player["username"], player["tag"])
        if rank_info:
            daily_rr[f"{player['username']}#{player['tag']}"] = rank_info["rr"]
    print("📌 Données RR sauvegardées à minuit.")

@tasks.loop(time=datetime.time(12, 25))  # Envoi du récap à 10h30
async def send_daily_message():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print("Erreur : Channel introuvable")
        return
    
    recap_message = "**📊 Récapitulatif de la journée :**\n\n"
    
    for player in TRACKED_PLAYERS:
        username_tag = f"{player['username']}#{player['tag']}"
        old_rr = daily_rr.get(username_tag, 0)
        rank_info = await get_valorant_rank(player["username"], player["tag"])
        
        if rank_info:
            new_rr = rank_info["rr"]
            rr_change = new_rr - old_rr
            recap_message += f"**{username_tag}** : {old_rr} RR ➝ {new_rr} RR ({'+' if rr_change >= 0 else ''}{rr_change} RR)\n"
        else:
            recap_message += f"**{username_tag}** : Erreur lors de la récupération des données ❌\n"
    
    await channel.send(recap_message)
    print("📊 Récapitulatif envoyé !")

@bot.command(name="elo")
async def elo(ctx, player_tag: str):
    if "#" not in player_tag:
        await ctx.send("Format invalide. Utilisez `/elo Nom#Tag`")
        return
    
    username, tag = player_tag.split("#")
    await ctx.send(f"Recherche de l'ELO pour {username}#{tag}...")
    rank_info = await get_valorant_rank(username, tag)
    
    if rank_info:
        response = f"{username}#{tag} est **{rank_info['rank']}** avec {rank_info['rr']} RR"
    else:
        response = f"Impossible de récupérer les données de {username}#{tag}"
    
    await ctx.send(response)

@bot.command(name="recap")
async def recap(ctx):
    recap_message = "**📊 Récapitulatif de la journée :**\n\n"
    
    for player in TRACKED_PLAYERS:
        username_tag = f"{player['username']}#{player['tag']}"
        old_rr = daily_rr.get(username_tag, 0)
        rank_info = await get_valorant_rank(player["username"], player["tag"])
        
        if rank_info:
            new_rr = rank_info["rr"]
            rr_change = new_rr - old_rr
            recap_message += f"**{username_tag}** : {old_rr} RR ➝ {new_rr} RR ({'+' if rr_change >= 0 else ''}{rr_change} RR)\n"
        else:
            recap_message += f"**{username_tag}** : Erreur lors de la récupération des données ❌\n"
    
    await ctx.send(recap_message)

@bot.command(name="test_recap")
async def test_recap(ctx):
    await send_daily_message()
    await ctx.send("📊 Test du récapitulatif envoyé !")

save_daily_rr.start()
send_daily_message.start()
bot.run(TOKEN)


