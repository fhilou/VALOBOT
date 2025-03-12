import discord
import os
import json
from discord.ext import commands, tasks
from api import fetch_elo
from datetime import datetime, time, timedelta
import pytz
from keep_alive import keep_alive

# Configuration du bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # Supprimer la commande help par défaut

# Fichier pour stocker les données d'elo
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

# Définition du fuseau horaire de Paris
PARIS_TZ = pytz.timezone("Europe/Paris")

# Événements du bot
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    print("🚀 Bot prêt à l'emploi !")

@bot.event
async def on_command_error(ctx, error):
    """Gère les erreurs de commandes."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Commande inconnue. Tape `!help` pour voir les commandes disponibles.")
    else:
        await ctx.send(f"⚠️ Une erreur est survenue : {error}")
        print(f"Erreur : {error}")

@bot.command(name="help")
async def help_command(ctx):
    """Affiche la liste des commandes disponibles"""
    help_message = (
        "**Liste des commandes :**\n"
        "`!elo <username> <tag>` - Affiche l'elo d'un joueur spécifique.\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
        "`!help` - Affiche cette aide."
    )
    await ctx.send(help_message)

# Commande !elo
@bot.command()
async def elo(ctx, username: str, tag: str):
    """Affiche l'elo d'un joueur spécifique"""
    elo = fetch_elo(username, tag)
    if elo is not None:
        await ctx.send(f"**{username}#{tag}** a un elo de **{elo} RR**.")
    else:
        await ctx.send(f"Impossible de récupérer l'élo de **{username}#{tag}**.")

# Commande !recap
@bot.command()
async def recap(ctx):
    """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
    elo_data = {}
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, "r") as file:
            elo_data = json.load(file)
    
    message = "**Récapitulatif des gains/pertes d'elo aujourd'hui :**\n"
    
    for player in elo_data.keys():
        old_elo = elo_data[player]["start"]
        new_elo = fetch_elo(player, elo_data[player]["tag"])
        
        if new_elo is not None:
            diff = new_elo - old_elo
            message += f"{player}: {'+' if diff >= 0 else ''}{diff} RR\n"
            elo_data[player]["current"] = new_elo
        else:
            message += f"{player}: 0 RR (pas de parties jouées)\n"

    with open(ELO_FILE, "w") as file:
        json.dump(elo_data, file, indent=4)
    
    await ctx.send(message)

# Variables pour le message automatique
morning_channel_id = None

# Commande !test
@bot.command()
async def test(ctx):
    """Envoie le message du matin avec l'elo des joueurs"""
    message = "**🎯 Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        tag = player["tag"]
        elo = fetch_elo(username, tag)
        message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"

    await ctx.send(message)

# Remplacer la variable morning_channel_id et la commande setchannel
# par une récupération directe depuis les variables d'environnement
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))  # 0 sera utilisé si la variable n'existe pas

@tasks.loop(minutes=1)
async def send_morning_message():
    """Envoie automatiquement le message tous les jours à 9h heure de Paris"""
    if CHANNEL_ID == 0:
        print("⚠️ Aucun canal défini pour le message automatique")
        return
    
    now = datetime.now(PARIS_TZ).time()
    target_time = time(9, 0)
    
    if now.hour == target_time.hour and now.minute == target_time.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            message = "**🎯 Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
            for player in TRACKED_PLAYERS:
                username = player["username"]
                tag = player["tag"]
                elo = fetch_elo(username, tag)
                message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"
            
            await channel.send(message)
        else:
            print(f"⚠️ Impossible de trouver le canal ID: {CHANNEL_ID}")

# Tâche automatique pour envoyer le message du matin
@tasks.loop(minutes=1)
async def send_morning_message():
    """Envoie automatiquement le message tous les jours à 9h heure de Paris"""
    global morning_channel_id
    if morning_channel_id is None:
        return
    
    now = datetime.now(PARIS_TZ).time()
    target_time = time(9, 0)
    
    if now.hour == target_time.hour and now.minute == target_time.minute:
        channel = bot.get_channel(morning_channel_id)
        if channel:
            message = "**🎯 Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
            for player in TRACKED_PLAYERS:
                username = player["username"]
                tag = player["tag"]
                elo = fetch_elo(username, tag)
                message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"
            
            await channel.send(message)
        else:
            print("⚠️ Impossible de trouver le canal enregistré.")

@send_morning_message.before_loop
async def before_morning_message():
    """Attendre le bon moment avant de démarrer la boucle"""
    await bot.wait_until_ready()
    print("⏳ Message automatique initialisé.")

# Démarrer la tâche automatique
send_morning_message.start()

# Lancer le service web et le bot
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Erreur : Le token du bot est manquant !")
