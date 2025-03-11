import discord
import os
import asyncio
import schedule
import datetime
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Charger les variables d'environnement
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
bot = commands.Bot(command_prefix="/", intents=intents)

daily_rr = {}

# Fonction pour récupérer le RR d'un joueur
def get_player_rr(username: str, tag: str):
    url = f"https://api.henrikdev.xyz/valorant/v2/mmr/eu/{username}/{tag}"
    headers = {"Authorization": HENRIKDEV_API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["ranking_in_tier"]
    else:
        return None

# Tâche quotidienne pour sauvegarder les RR initiaux
@tasks.loop(time=datetime.time(0, 0))
async def save_daily_rr():
    global daily_rr
    daily_rr = {}
    for player in TRACKED_PLAYERS:
        rr = get_player_rr(player["username"], player["tag"])
        if rr is not None:
            daily_rr[f"{player['username']}#{player['tag']}"] = rr

# Commande pour afficher le récapitulatif
@bot.command(name="recap")
async def recap(ctx):
    if not daily_rr:
        await ctx.send("Aucune donnée enregistrée pour aujourd'hui. Attendez le prochain reset !")
        return
    
    recap_message = "**📊 Récapitulatif de la journée :**\n\n"
    
    for username_tag in daily_rr.keys():
        initial_rr = daily_rr[username_tag]
        username, tag = username_tag.split("#")
        current_rr = get_player_rr(username, tag)

        if current_rr is not None:
            diff = current_rr - initial_rr
            emoji = "🔼" if diff > 0 else "🔽"
            recap_message += f"**{username_tag}** : {initial_rr} ➝ {current_rr} ({emoji} {abs(diff)} RR)\n"
        else:
            recap_message += f"**{username_tag}** : Erreur lors de la récupération des données ❌\n"

    await ctx.send(recap_message)

# Commande pour récupérer l'ELO d'un joueur spécifique
@bot.command(name="elo")
async def elo(ctx, arg):
    if "#" in arg:
        username, tag = arg.split("#")
        await ctx.send(f"Recherche de l'ELO pour {username}#{tag}...")
        elo_info = get_player_rr(username, tag)
        if elo_info is not None:
            await ctx.send(f"{username}#{tag} a actuellement {elo_info} RR")
        else:
            await ctx.send("Impossible de récupérer les données.")
    else:
        await ctx.send("Format invalide. Utilisez `/elo Nom#Tag`")

# Commande help
@bot.command(name="help")
async def help_command(ctx):
    help_message = """**Commandes disponibles :**\n
    `/elo Nom#Tag` - Affiche le rang et le RR actuel du joueur\n    `/recap` - Montre l'évolution du RR des joueurs suivis\n    `/help` - Affiche cette aide\n    """
    await ctx.send(help_message)

# Envoi du message quotidien dans un salon spécifique
async def send_daily_message():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Erreur : Channel introuvable")
        return
    
    elo_messages = [f"{player['username']}#{player['tag']} : {get_player_rr(player['username'], player['tag'])} RR" for player in TRACKED_PLAYERS]
    message = "**Résumé quotidien des ELO :**\n" + "\n".join(elo_messages)
    await channel.send(message)
    print("Message quotidien envoyé !")

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')
    save_daily_rr.start()
    schedule.every().day.at("10:33").do(lambda: asyncio.create_task(send_daily_message()))
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

bot.run(TOKEN)
