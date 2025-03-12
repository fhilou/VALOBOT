import discord
import json
import os
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from api import fetch_elo

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot avec intents pour lire les messages
intents = discord.Intents.default()
intents.message_content = True  # Important pour les commandes avec préfixe !
bot = commands.Bot(command_prefix="!", intents=intents)

# Constantes
ELO_FILE = "elo_data.json"
TRACKED_PLAYERS = [
    {"username": "JokyJokSsj", "tag": "EUW"},
    {"username": "HUNGRYCHARLY", "tag": "EUW"},
    {"username": "igosano", "tag": "24863"},
    {"username": "Irû", "tag": "3004"},
    {"username": "EmilyInTheRift", "tag": "2107A"},
    {"username": "ANEMONIA", "tag": "EUW"},
    {"username": "Hartware", "tag": "EUW"},
]

# Définition des commandes directement avec des décorateurs
@bot.command(name="ping")
async def ping(ctx):
    """Commande de test simple"""
    await ctx.send("Pong!")

@bot.command(name="elo")
async def elo_command(ctx, username: str, tag: str):
    """Affiche l'elo d'un joueur spécifique"""
    elo = fetch_elo(username, tag)
    if elo is not None:
        await ctx.send(f"**{username}#{tag}** a un elo de **{elo} RR**.")
    else:
        await ctx.send(f"Impossible de récupérer l'élo de **{username}#{tag}**.")

@bot.command(name="recap")
async def recap_command(ctx):
    """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, "r") as file:
            elo_data = json.load(file)
    else:
        elo_data = {}
        
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

@bot.command(name="test")
async def test_command(ctx):
    """Envoie le message du matin avec l'elo des joueurs"""
    message = "**Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        tag = player["tag"]
        elo = fetch_elo(username, tag)
        message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"
    await ctx.send(message)

@bot.command(name="help")
async def help_command(ctx):
    """Affiche la liste des commandes disponibles"""
    help_message = (
        "**Liste des commandes :**\n"
        "`!elo <username> <tag>` - Affiche l'elo d'un joueur spécifique.\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
        "`!ping` - Vérifie si le bot est en ligne.\n"
        "`!help` - Affiche cette aide."
    )
    await ctx.send(help_message)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    print("Commandes disponibles:")
    for command in bot.commands:
        print(f"- {command.name}")

# Fonction appelée lorsqu'une commande n'est pas trouvée
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Commande non reconnue. Tapez `!help` pour voir la liste des commandes disponibles.")
        print(f"Erreur de commande: {error}")
    else:
        print(f"Erreur: {error}")

# Garder le bot en vie et le lancer
keep_alive()
bot.run(TOKEN)
