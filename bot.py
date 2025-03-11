import discord
import os
import asyncio
import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests
from flask import Flask
from threading import Thread

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

daily_rr = {}

async def get_valorant_rank(username, tag):
    url = f"https://api.henrikdev.xyz/valorant/v2/mmr/eu/{username}/{tag}"
    headers = {"Authorization": HENRIKDEV_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            current_rank = data["data"]["currenttierpatched"]
            rank_progress = data["data"]["ranking_in_tier"]
            elo_change = data["data"].get("mmr_change_to_last_game", "N/A")
            
            elo_change_text = f"(+{elo_change} au dernier match)" if isinstance(elo_change, int) and elo_change > 0 else f"({elo_change} au dernier match)"
            return {
                "rank": f"{username}#{tag} est **{current_rank}** avec {rank_progress} RR {elo_change_text}",
                "rr": data["data"]["mmr"]
            }
        else:
            return None
    except Exception as e:
        return f"Erreur lors de la récupération des données : {e}"

@tasks.loop(time=datetime.time(0, 0))  # Minuit
async def save_daily_rr():
    global daily_rr
    daily_rr = {}

    for player in TRACKED_PLAYERS:
        rank_data = await get_valorant_rank(player["username"], player["tag"])
        if rank_data:
            daily_rr[f"{player['username']}#{player['tag']}"] = rank_data["rr"]

@tasks.loop(time=datetime.time(10, 30))  # Envoi du récap à 10h30
async def send_daily_message():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print("Erreur : Channel introuvable")
        return
    
    elo_messages = await asyncio.gather(
        *[get_valorant_rank(player["username"], player["tag"]) for player in TRACKED_PLAYERS]
    )
    
    message = "**Résumé quotidien des ELO :**\n" + "\n".join([msg["rank"] for msg in elo_messages if msg])
    await channel.send(message)
    print("Message quotidien envoyé !")

@bot.command(name="elo")
async def elo(ctx, player_tag: str):
    if "#" not in player_tag:
        await ctx.send("Format invalide. Utilisez `/elo Nom#Tag`")
        return
    
    username, tag = player_tag.split("#")
    await ctx.send(f"Recherche de l'ELO pour {username}#{tag}...")
    elo_info = await get_valorant_rank(username, tag)
    await ctx.send(elo_info["rank"] if elo_info else "Erreur lors de la récupération des données.")

@bot.command(name="recap")
async def recap(ctx):
    if not daily_rr:
        await ctx.send("Aucun RR n'a été enregistré aujourd'hui.")
        return
    
    recap_message = "**📊 Récapitulatif de la journée :**\n\n"
    
    # Boucle sur les joueurs et leurs RR initialement enregistrés
    for player in TRACKED_PLAYERS:
        username_tag = f"{player['username']}#{player['tag']}"
        initial_rr = daily_rr.get(username_tag)

        if initial_rr is None:
            recap_message += f"**{username_tag}** : Aucune donnée RR trouvée ❌\n"
            continue

        rank_data = await get_valorant_rank(player["username"], player["tag"])
        if rank_data:
            current_rr = rank_data["rr"]
            rr_change = current_rr - initial_rr
            elo = rank_data["rank"]
            recap_message += f"**{username_tag}** : **{elo}** | {initial_rr} ➝ {current_rr} ({'+' if rr_change >= 0 else ''}{rr_change})\n"
        else:
            recap_message += f"**{username_tag}** : Erreur lors de la récupération des données ❌\n"
    
    await ctx.send(recap_message)

# Code Flask pour garder le bot en ligne
app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

save_daily_rr.start()
send_daily_message.start()

# Garder le bot en ligne via Flask
keep_alive()

bot.run(TOKEN)


