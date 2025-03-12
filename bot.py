import discord
import os
import json
import requests
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
import pytz
from keep_alive import keep_alive
from dotenv import load_dotenv

# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Nécessaire pour les commandes Discord récentes

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # Supprimer la commande help par défaut

# Fichier pour stocker les données d'elo
ELO_FILE = "elo_data.json"

# Liste des joueurs suivis
TRACKED_PLAYERS = [
    {"username": "JokyJokSsj", "tag": "EUW"},
    {"username": "HUNGRYCHARLY", "tag": "EUW"},  # Vérifiez l'orthographe
    {"username": "igosano", "tag": "24863"},
    {"username": "Irû", "tag": "3004"},
    {"username": "EmilyInTheRift", "tag": "2107A"},  
    {"username": "ANEMONIA", "tag": "EUW"},
    {"username": "Hartware", "tag": "EUW"},
]

# Définition du fuseau horaire de Paris
PARIS_TZ = pytz.timezone("Europe/Paris")

# Tenter de charger le channel ID depuis les variables d'environnement
try:
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
except (ValueError, TypeError):
    CHANNEL_ID = 0

# Fonction pour récupérer l'elo d'un joueur
def fetch_elo(username, tag):
    """Récupère l'elo d'un joueur via l'API HenrikDev"""
    try:
        # Nettoyer les données d'entrée
        username = username.strip()
        tag = tag.strip()
        
        # Supprimer le # si présent dans le tag
        if tag.startswith("#"):
            tag = tag[1:]
            
        print(f"Tentative de récupération de l'elo pour {username}#{tag}")
            
        url = f"https://api.henrikdev.xyz/valorant/v2/mmr/{tag}/{username}"
        headers = {"Authorization": f"Bearer {HENRIKDEV_API_KEY}"}
        
        print(f"URL de l'API: {url}")
        response = requests.get(url, headers=headers)
        
        print(f"Réponse API pour {username}#{tag}: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "elo" in data["data"]:
                print(f"Elo trouvé: {data['data']['elo']}")
                return data["data"]["elo"]  # Retourne l'elo actuel du joueur
            else:
                print(f"Données manquantes dans la réponse: {data}")
        else:
            print(f"Erreur API: {response.status_code}, {response.text}")
        return None
    except Exception as e:
        print(f"Exception lors de la récupération de l'elo: {str(e)}")
        return None

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
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant: {error.param.name}")
    else:
        await ctx.send(f"⚠️ Une erreur est survenue : {error}")
        print(f"Erreur détaillée : {type(error).__name__}: {error}")

# Commande !help
@bot.command(name="help")
async def help_command(ctx):
    """Affiche la liste des commandes disponibles"""
    help_message = (
        "**Liste des commandes :**\n"
        "`!elo <joueur>` ou `!elo <joueur#tag>` - Affiche l'elo d'un joueur spécifique.\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
        "`!setchannel` - Définit le canal pour le message automatique du matin.\n"
        "`!initelo` - (Admin) Initialise le suivi d'elo pour la journée.\n"
        "`!help` - Affiche cette aide."
    )
    await ctx.send(help_message)

# Commande !elo
@bot.command()
async def elo(ctx, *, player_info: str = None):
    """
    Affiche l'elo d'un joueur spécifique
    Usage: !elo joueur#tag ou !elo joueur tag
    """
    if player_info is None:
        await ctx.send("❌ Format incorrect. Utilisez `!elo joueur#tag` ou `!elo joueur tag`")
        return
        
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
            
        # Récupérer l'elo
        elo = fetch_elo(username, tag)
        if elo is not None:
            await ctx.send(f"**{username}#{tag}** a un elo de **{elo} RR**.")
        else:
            await ctx.send(f"Impossible de récupérer l'élo de **{username}#{tag}**.")
            
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération de l'elo: {str(e)}")

# Fonction pour charger les données d'elo
def load_elo_data():
    """Charge les données d'elo enregistrées."""
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, "r") as file:
            return json.load(file)
    return {}

# Fonction pour sauvegarder les données d'elo
def save_elo_data(data):
    """Sauvegarde les nouvelles valeurs d'elo."""
    with open(ELO_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Commande !recap
@bot.command()
async def recap(ctx):
    """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
    elo_data = load_elo_data()
    
    if not elo_data:
        await ctx.send("**Récapitulatif des gains/pertes d'elo aujourd'hui :** Aucune donnée disponible. Utilisez `!initelo` pour initialiser les données.")
        return
        
    message = "**Récapitulatif des gains/pertes d'elo aujourd'hui :**\n"
    
    for player in elo_data.keys():
        old_elo = elo_data[player]["start"]
        tag = elo_data[player]["tag"]
        new_elo = fetch_elo(player, tag)
        
        if new_elo is not None:
            diff = new_elo - old_elo
            message += f"{player}: {'+' if diff >= 0 else ''}{diff} RR\n"
            elo_data[player]["current"] = new_elo
        else:
            message += f"{player}: 0 RR (pas de parties jouées ou données indisponibles)\n"

    save_elo_data(elo_data)
    await ctx.send(message)

# Commande !initelo
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
        
        save_elo_data(elo_data)
        
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
    message = generate_morning_message()
    await ctx.send(message)

# Fonction pour générer le message du matin
def generate_morning_message():
    """Génère le message avec l'élo des joueurs"""
    message = "**🎯 Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        tag = player["tag"]
        elo = fetch_elo(username, tag)
        message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"
    return message

# Commande pour définir le canal
@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):
    """Définit le canal actuel comme canal pour les messages automatiques"""
    global CHANNEL_ID
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
        CHANNEL_ID = ctx.channel.id
        
        await ctx.send(f"✅ Canal `{ctx.channel.name}` défini pour les messages automatiques !")
        
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la définition du canal : {str(e)}")

# Commande pour recharger le bot
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx):
    """Recharge toutes les commandes (Admin uniquement)"""
    try:
        await ctx.send("🔄 Rechargement du bot en cours...")
        # Redémarrer le bot correctement n'est pas possible directement
        # Cette commande devrait être gérée par un script externe
        await ctx.send("✅ Commande de rechargement reçue. Veuillez redémarrer le bot manuellement.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors du rechargement : {e}")

# Tâche automatique pour envoyer le message du matin
@tasks.loop(minutes=1)
async def send_morning_message():
    """Envoie automatiquement le message tous les jours à 9h heure de Paris"""
    if CHANNEL_ID == 0:
        print("⚠️ Aucun canal défini pour le message automatique")
        return
    
    now = datetime.now(PARIS_TZ).time()
    target_time = time(9, 0)  # 9h00 du matin
    
    if now.hour == target_time.hour and now.minute == target_time.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            message = generate_morning_message()
            await channel.send(message)
            print(f"✅ Message du matin envoyé dans le canal {channel.name}")
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
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ Erreur : Le token du bot est manquant !")
