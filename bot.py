import discord
import os
import json
from discord.ext import commands, tasks
from api import fetch_elo
from datetime import datetime, time, timedelta
import pytz
from keep_alive import keep_alive
import asyncio

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
    
    # Démarrer la tâche automatique après que le bot soit prêt
    send_morning_message.start()

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
        "`!elo <joueur>` ou `!elo <joueur#tag>` - Affiche l'elo d'un joueur spécifique.\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
        "`!initelo` - (Admin) Initialise le suivi d'elo pour la journée.\n"
        "`!help` - Affiche cette aide."
    )
    await ctx.send(help_message)

# Commande !elo améliorée
@bot.command()
async def elo(ctx, *, player_info: str):
    """
    Affiche l'elo d'un joueur spécifique
    Usage: !elo joueur#tag ou !elo joueur tag
    """
    try:
        # Vérifier si l'utilisateur a utilisé le format joueur#tag
        if "#" in player_info:
            parts = player_info.split("#", 1)
            username = parts[0].strip()
            tag = parts[1].strip()
        # Sinon, chercher le dernier espace pour séparer username et tag
        else:
            parts = player_info.rsplit(" ", 1)
            if len(parts) != 2:
                await ctx.send("❌ Format incorrect. Utilisez `!elo joueur#tag` ou `!elo joueur tag`")
                return
            username = parts[0].strip()
            tag = parts[1].strip()
            
        # Supprimer le # si l'utilisateur l'a mis au début du tag
        if tag.startswith("#"):
            tag = tag[1:]
            
        # Récupérer l'elo
        elo = fetch_elo(username, tag)
        if elo is not None:
            await ctx.send(f"**{username}#{tag}** a un elo de **{elo} RR**.")
        else:
            await ctx.send(f"Impossible de récupérer l'élo de **{username}#{tag}**.")
            
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération de l'elo: {str(e)}")

# Commande !recap améliorée
@bot.command()
async def recap(ctx):
    """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
    elo_data = {}
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, "r") as file:
            elo_data = json.load(file)
    
    if not elo_data:
        await ctx.send("**Récapitulatif des gains/pertes d'elo aujourd'hui :** Aucune donnée disponible.")
        return
    
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

# Nouvelle commande !initelo
@bot.command()
@commands.has_permissions(administrator=True)
async def initelo(ctx):
    """Initialise ou réinitialise les données d'elo pour les joueurs suivis (Admin uniquement)"""
    try:
        elo_data = {}
        
        for player in TRACKED_PLAYERS:
            username = player["username"]
            tag = player["tag"]
            current_elo = fetch_elo(username, tag)
            
            if current_elo is not None:
                elo_data[username] = {
                    "tag": tag,
                    "start": current_elo,
                    "current": current_elo
                }
        
        with open(ELO_FILE, "w") as file:
            json.dump(elo_data, file, indent=4)
        
        count = len(elo_data)
        await ctx.send(f"✅ Données d'elo initialisées pour {count} joueurs.")
        
        # Afficher les joueurs initialisés
        if count > 0:
            message = "**Joueurs suivis:**\n"
            for player, data in elo_data.items():
                message += f"{player}: {data['current']} RR\n"
            await ctx.send(message)
        
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de l'initialisation des données d'elo: {str(e)}")

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

# Utiliser la variable d'environnement pour le channel ID
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))  # 0 sera utilisé si la variable n'existe pas

# Commande pour définir le canal des messages automatiques
@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):
    """Définit le canal actuel comme canal pour les messages automatiques"""
    # Cette commande est uniquement destinée aux administrateurs
    try:
        # Ouvrir/créer le fichier .env
        env_file = ".env"
        env_vars = {}
        
        # Lire les variables d'environnement existantes
        if os.path.exists(env_file):
            with open(env_file, "r") as file:
                for line in file:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Mettre à jour la variable CHANNEL_ID
        env_vars["CHANNEL_ID"] = str(ctx.channel.id)
        
        # Réécrire le fichier .env
        with open(env_file, "w") as file:
            for key, value in env_vars.items():
                file.write(f"{key}={value}\n")
        
        # Mettre à jour la variable globale
        global CHANNEL_ID
        CHANNEL_ID = ctx.channel.id
        
        await ctx.send(f"✅ Canal `{ctx.channel.name}` défini pour les messages automatiques !")
        
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la définition du canal : {str(e)}")

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

@send_morning_message.before_loop
async def before_morning_message():
    """Attendre que le bot soit prêt avant de démarrer la boucle"""
    await bot.wait_until_ready()
    print("⏳ Message automatique initialisé.")

# Lancer le service web et le bot
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Erreur : Le token du bot est manquant !")
