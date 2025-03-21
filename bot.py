import discord
import os
import json
import requests
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
import pytz
from keep_alive import keep_alive
from dotenv import load_dotenv

# Charger les variables d'environnement d'abord
dotenv_path = ".env"
load_dotenv(dotenv_path)

# Ensuite, définir les variables d'environnement
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Maintenant, vous pouvez vérifier si la clé est présente
if HENRIKDEV_API_KEY:
    print("✓ HENRIKDEV_API_KEY trouvée")
else:
    print("⚠️ HENRIKDEV_API_KEY non trouvée! Les requêtes API pourraient échouer.")

# Configuration du bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Nécessaire pour les commandes Discord récentes

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # Supprimer la commande help par défaut

# Fichier pour stocker les données d'elo
import os
import tempfile
import json

# Définir un chemin de fichier dans un répertoire temporaire accessible
temp_dir = tempfile.gettempdir()
ELO_FILE = "elo_data.json"

# Vérifier si le répertoire temporaire est accessible en écriture
try:
    os.access(temp_dir, os.W_OK)
    print(f"✓ Répertoire temporaire accessible: {temp_dir}")
except Exception as e:
    print(f"⚠️ Problème d'accès au répertoire temporaire: {str(e)}")
    # Fallback à /tmp si disponible
    if os.path.exists("/tmp") and os.access("/tmp", os.W_OK):
        temp_dir = "/tmp"
        ELO_FILE = os.path.join(temp_dir, "elo_data.json")
        print(f"✓ Utilisation du répertoire /tmp comme alternative")

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

# Dictionnaire pour les noms de rang
RANK_NAMES = {
    0: "Unranked",
    1: "Unranked",
    2: "Unranked",
    3: "Iron 1",
    4: "Iron 2",
    5: "Iron 3",
    6: "Bronze 1",
    7: "Bronze 2",
    8: "Bronze 3",
    9: "Silver 1",
    10: "Silver 2",
    11: "Silver 3",
    12: "Gold 1",
    13: "Gold 2",
    14: "Gold 3",
    15: "Platinum 1",
    16: "Platinum 2",
    17: "Platinum 3",
    18: "Diamond 1",
    19: "Diamond 2",
    20: "Diamond 3",
    21: "Ascendant 1",
    22: "Ascendant 2",
    23: "Ascendant 3",
    24: "Immortal 1",
    25: "Immortal 2",
    26: "Immortal 3",
    27: "Radiant"
}

# Fonction pour récupérer l'elo et le rang d'un joueur
def fetch_elo(username, tag):
    """Récupère l'elo et le rang d'un joueur via l'API HenrikDev"""
    try:
        # Nettoyer les données d'entrée
        username = username.strip()
        tag = tag.strip()
        
        # Gérer les noms spéciaux (pour Valorant, certains noms peuvent avoir des espaces)
        if tag.lower() == "euw":
            # Pour les joueurs avec le tag "EUW", utiliser un format différent
            full_username = username
            region = "eu"
        else:
            # Pour les autres joueurs, utiliser le format standard
            full_username = username
            region = "eu"  # Supposons que tous les joueurs sont sur la région EU
            
        print(f"Tentative de récupération de l'elo pour {username}#{tag}")
            
        # Utiliser l'endpoint v1 plus stable
        url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{username}/{tag}"
        
        # Configurer les headers correctement
        headers = {}
        if HENRIKDEV_API_KEY:
            headers["Authorization"] = HENRIKDEV_API_KEY
        
        print(f"URL de l'API: {url}")
        
        # Ajouter un timeout pour éviter des attentes infinies
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Réponse API pour {username}#{tag}: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Imprimer la réponse complète pour le débogage
            print(f"Structure de la réponse JSON: {json.dumps(data, indent=2)}")
            
            # Vérifier la structure de la réponse v1
            if "data" in data:
                # Récupérer les informations de rang et d'elo
                rank_info = {}
                
                if "currenttier" in data["data"]:
                    rank_tier = data["data"]["currenttier"]
                    rank_name = RANK_NAMES.get(rank_tier, "Inconnu")
                    rank_info["tier"] = rank_tier
                    rank_info["name"] = rank_name
                    
                    # Récupérer les RR de la réponse
                    if "ranking_in_tier" in data["data"]:
                        elo = data["data"]["ranking_in_tier"]
                        rank_info["elo"] = elo
                        print(f"Rang trouvé: {rank_name}, Elo: {elo} RR")
                        return rank_info
                    else:
                        print("Données de ranking_in_tier manquantes")
                        return None
                else:
                    print("Données currenttier manquantes")
                    return None
            else:
                print("Données manquantes dans la réponse")
                return None
                
        elif response.status_code == 401:
            print("Erreur d'authentification API. Vérifiez votre HENRIKDEV_API_KEY.")
        elif response.status_code == 404:
            print(f"Joueur non trouvé: {username}#{tag}")
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
    
    # Démarrer les tâches automatiques après que le bot soit prêt
    send_morning_message.start()
    auto_init_elo_at_midnight.start()

@bot.event
async def on_command_error(ctx, error):
    """Gère les erreurs de commandes."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Commande inconnue. Tape `!help` pour voir les commandes disponibles.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant: {error.param.name}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")
    else:
        await ctx.send(f"⚠️ Une erreur est survenue : {error}")
        print(f"Erreur détaillée : {type(error).__name__}: {error}")

# Commande !help
@bot.command(name="help")
async def help_command(ctx):
    """Affiche la liste des commandes disponibles"""
    help_message = (
        "**Liste des commandes :**\n"
        "`!elo <joueur>` ou `!elo <joueur#tag>` - Affiche l'elo et le rang d'un joueur spécifique.\n"
        "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
        "`!test` - Envoie le message du jour avec le rang et l'élo actuel des joueurs.\n"
        "`!help` - Affiche cette aide."
    )
    await ctx.send(help_message)

# Commande !elo
@bot.command()
async def elo(ctx, *, player_info: str = None):
    """
    Affiche l'elo et le rang d'un joueur spécifique
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
            
        # Message d'attente pour indiquer que le bot travaille
        loading_msg = await ctx.send(f"🔍 Recherche de l'elo pour **{username}#{tag}**...")
            
        # Récupérer l'elo et le rang
        rank_info = fetch_elo(username, tag)
        if rank_info is not None:
            rank_name = rank_info["name"]
            elo = rank_info["elo"]
            await loading_msg.edit(content=f"**{username}#{tag}** est **{rank_name}** avec **{elo} RR**.")
        else:
            await loading_msg.edit(content=f"Impossible de récupérer les informations de **{username}#{tag}**. Vérifiez le nom d'utilisateur et le tag.")
            
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération de l'elo: {str(e)}")

# Fonction pour charger les données d'elo
def load_elo_data():
    """Charge les données d'elo enregistrées."""
    try:
        if os.path.exists(ELO_FILE):
            with open(ELO_FILE, "r") as file:
                data = json.load(file)
                print(f"✓ Données d'elo chargées avec succès: {len(data)} joueurs")
                return data
        else:
            print(f"ℹ️ Fichier d'elo non trouvé, retour d'un dictionnaire vide")
            return {}
    except json.JSONDecodeError as e:
        print(f"⚠️ Erreur lors du chargement du fichier d'elo: {str(e)}")
        # Créer une sauvegarde du fichier corrompu
        if os.path.exists(ELO_FILE):
            backup_file = f"{ELO_FILE}.bak.{int(datetime.now().timestamp())}"
            os.rename(ELO_FILE, backup_file)
            print(f"⚠️ Fichier corrompu sauvegardé sous {backup_file}")
        return {}
    except Exception as e:
        print(f"⚠️ Erreur inattendue lors du chargement du fichier d'elo: {str(e)}")
        return {}

# Fonction pour sauvegarder les données d'elo
def save_elo_data(data):
    """Sauvegarde les nouvelles valeurs d'elo."""
    try:
        with open(ELO_FILE, "w") as file:
            json.dump(data, file, indent=4)
            print(f"✓ Données d'elo sauvegardées avec succès: {len(data)} joueurs")
        return True
    except Exception as e:
        print(f"⚠️ Erreur lors de la sauvegarde des données d'elo: {str(e)}")
        return False

# Fonction pour initialiser automatiquement les données d'elo
async def initialize_elo_data():
    """Initialise les données d'elo pour les joueurs suivis"""
    try:
        print("⏳ Initialisation automatique des données d'elo...")
        
        elo_data = {}
        success_count = 0
        
        for player in TRACKED_PLAYERS:
            username = player["username"]
            tag = player["tag"]
            rank_info = fetch_elo(username, tag)
            
            if rank_info is not None:
                elo_data[username] = {
                    "tag": tag,
                    "start": rank_info["elo"],
                    "current": rank_info["elo"],
                    "rank": rank_info["name"]
                }
                success_count += 1
        
        save_elo_data(elo_data)
        print(f"✅ Données d'elo initialisées pour {success_count}/{len(TRACKED_PLAYERS)} joueurs.")
        
        # Envoyer un message dans le canal si configuré
        if CHANNEL_ID != 0:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                message = f"✅ Données d'elo initialisées pour {success_count}/{len(TRACKED_PLAYERS)} joueurs."
                await channel.send(message)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation des données d'elo: {str(e)}")

# Commande !recap
@bot.command()
async def recap(ctx):
    """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
    elo_data = load_elo_data()
    
    if not elo_data:
        await ctx.send("**Récapitulatif des gains/pertes d'elo aujourd'hui :** Aucune donnée disponible. L'initialisation automatique se fera à minuit.")
        return
        
    # Message d'attente
    loading_msg = await ctx.send("⏳ Calcul des gains/pertes d'elo en cours...")
        
    message = "**Récapitulatif des gains/pertes d'elo aujourd'hui :**\n"
    
    for player in list(elo_data.keys()):
        old_elo = elo_data[player]["start"]
        tag = elo_data[player]["tag"]
        rank_info = fetch_elo(player, tag)
        
        if rank_info is not None:
            new_elo = rank_info["elo"]
            rank_name = rank_info["name"]
            diff = new_elo - old_elo
            message += f"{player} ({rank_name}): {'+' if diff >= 0 else ''}{diff} RR\n"
            elo_data[player]["current"] = new_elo
            elo_data[player]["rank"] = rank_name
        else:
            message += f"{player}: Données indisponibles\n"
            
    save_elo_data(elo_data)
    await loading_msg.edit(content=message)

# Commande !test
@bot.command()
async def test(ctx):
    """Envoie le message du matin avec l'elo des joueurs"""
    loading_msg = await ctx.send("⏳ Génération du message du matin...")
    try:
        message = await generate_morning_message()
        await loading_msg.edit(content=message)
    except Exception as e:
        await loading_msg.edit(content=f"❌ Erreur lors de la génération du message: {str(e)}")

# Fonction pour générer le message du matin
async def generate_morning_message():
    """Génère le message avec l'élo et le rang des joueurs"""
    message = "**🎯 Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
    for player in TRACKED_PLAYERS:
        username = player["username"]
        tag = player["tag"]
        rank_info = fetch_elo(username, tag)
        
        if rank_info is not None:
            rank_name = rank_info["name"]
            elo = rank_info["elo"]
            message += f"{username}: {rank_name} ({elo} RR)\n"
        else:
            message += f"{username}: N/A\n"
    return message

# Commande pour recharger le bot
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx):
    """Recharge toutes les commandes (Admin uniquement)"""
    try:
        await ctx.send("🔄 Rechargement des données d'elo...")
        
        # Recharger les données d'elo à partir de l'API
        success_count = 0
        elo_data = load_elo_data()  # Charger les données existantes
        
        for player in TRACKED_PLAYERS:
            username = player["username"]
            tag = player["tag"]
            rank_info = fetch_elo(username, tag)
            
            if rank_info is not None:
                if username not in elo_data:
                    elo_data[username] = {
                        "tag": tag, 
                        "start": rank_info["elo"], 
                        "current": rank_info["elo"],
                        "rank": rank_info["name"]
                    }
                else:
                    # Mettre à jour seulement la valeur actuelle, pas la valeur de départ
                    elo_data[username]["current"] = rank_info["elo"]
                    elo_data[username]["rank"] = rank_info["name"]
                success_count += 1
        
        save_elo_data(elo_data)
        
        await ctx.send(f"✅ Données d'elo rechargées pour {success_count}/{len(TRACKED_PLAYERS)} joueurs.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors du rechargement : {e}")
        
# Tâche automatique pour envoyer le message du matin
@tasks.loop(minutes=1)
async def send_morning_message():
    """Envoie automatiquement le message tous les jours à 9h heure de Paris"""
    try:
        if CHANNEL_ID == 0:
            print("⚠️ Aucun canal défini pour le message automatique")
            return
        
        now = datetime.now(PARIS_TZ).time()
        target_time = time(9, 0)  # 9h00 du matin
        
        # Vérifier si c'est l'heure d'envoyer le message
        if now.hour == target_time.hour and now.minute == target_time.minute:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                message = await generate_morning_message()
                await channel.send(message)
                print(f"✅ Message du matin envoyé dans le canal {channel.name}")
            else:
                print(f"⚠️ Impossible de trouver le canal ID: {CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Erreur dans la tâche send_morning_message: {str(e)}")

# Tâche automatique pour initialiser l'elo à minuit
@tasks.loop(minutes=1)
async def auto_init_elo_at_midnight():
    """Initialise automatiquement les données d'elo tous les jours à minuit heure de Paris"""
    try:
        now = datetime.now(PARIS_TZ).time()
        target_time = time(0, 0)  # Minuit
        
        # Vérifier si c'est minuit
        if now.hour == target_time.hour and now.minute == target_time.minute:
            print("🕛 Minuit : Initialisation automatique des données d'elo...")
            await initialize_elo_data()
    except Exception as e:
        print(f"❌ Erreur dans la tâche auto_init_elo_at_midnight: {str(e)}")

@send_morning_message.before_loop
async def before_morning_message():
    """Attendre que le bot soit prêt avant de démarrer la boucle"""
    await bot.wait_until_ready()
    print("⏳ Message automatique initialisé.")

@auto_init_elo_at_midnight.before_loop
async def before_auto_init_elo():
    """Attendre que le bot soit prêt avant de démarrer la boucle"""
    await bot.wait_until_ready()
    print("⏳ Initialisation automatique d'elo à minuit configurée.")

# Ajoutez ce code à votre bot.py existant, juste avant la section "if __name__ == "__main__":"

# Importation du module de suivi d'elo LoL
# Supposons que le fichier s'appelle lol_elo_tracker.py et est dans le même dossier
import lol_elo_tracker

# Liste des joueurs LoL suivis
LOL_TRACKED_PLAYERS = [
    {"username": "Faker", "region": "kr"},
    {"username": "Rekkles", "region": "euw"},
    {"username": "Caedrel", "region": "euw"},
    # Ajoutez vos joueurs ici
]

# Commande !lolelo
@bot.command()
async def lolelo(ctx, *, player_info: str = None):
    """
    Affiche l'elo et le rang d'un joueur LoL spécifique
    Usage: !lolelo joueur région
    """
    if player_info is None:
        await ctx.send("❌ Format incorrect. Utilisez `!lolelo joueur région` (par exemple: `!lolelo Faker kr`)")
        return
        
    try:
        # Séparer le nom d'utilisateur et la région
        parts = player_info.rsplit(" ", 1)
        if len(parts) != 2:
            await ctx.send("❌ Format incorrect. Utilisez `!lolelo joueur région` (par exemple: `!lolelo Faker kr`)")
            return
        
        username = parts[0].strip()
        region = parts[1].strip().lower()
            
        # Message d'attente pour indiquer que le bot travaille
        loading_msg = await ctx.send(f"🔍 Recherche de l'elo pour **{username}** ({region})...")
            
        # Récupérer l'elo et le rang
        rank_info = lol_elo_tracker.fetch_lol_elo(username, region)
        if rank_info is not None:
            rank_name = rank_info["name"]
            lp = rank_info["lp"]
            await loading_msg.edit(content=f"**{username}** ({region}) est **{rank_name}** avec **{lp} LP**.")
        else:
            await loading_msg.edit(content=f"Impossible de récupérer les informations de **{username}** ({region}). Vérifiez le nom d'utilisateur et la région.")
            
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération de l'elo: {str(e)}")

# Commande !lolrecap
@bot.command()
async def lolrecap(ctx):
    """Affiche le récapitulatif des gains/pertes de LP aujourd'hui"""
    elo_data = lol_elo_tracker.load_elo_data()
    
    if not elo_data:
        await ctx.send("**Récapitulatif des gains/pertes de LP aujourd'hui :** Aucune donnée disponible. L'initialisation automatique se fera à minuit.")
        return
        
    # Message d'attente
    loading_msg = await ctx.send("⏳ Calcul des gains/pertes de LP en cours...")
        
    message = "**Récapitulatif des gains/pertes de LP aujourd'hui :**\n"
    
    for player in list(elo_data.keys()):
        region = elo_data[player]["region"]
        old_lp = elo_data[player]["start"]["lp"]
        old_tier = elo_data[player]["start"]["tier"]
        old_division = elo_data[player]["start"]["division"]
        
        rank_info = lol_elo_tracker.fetch_lol_elo(player, region)
        
        if rank_info is not None:
            new_lp = rank_info["lp"]
            new_tier = rank_info["tier"]
            new_division = rank_info["division"]
            rank_name = rank_info["name"]
            
            diff = lol_elo_tracker.calculate_lp_diff(
                old_lp, old_tier, old_division,
                new_lp, new_tier, new_division
            )
            
            message += f"{player} ({rank_name}): {'+' if diff >= 0 else ''}{diff} LP\n"
            
            # Mettre à jour les données actuelles
            elo_data[player]["current"]["lp"] = new_lp
            elo_data[player]["current"]["tier"] = new_tier
            elo_data[player]["current"]["division"] = new_division
            elo_data[player]["rank"] = rank_name
        else:
            message += f"{player}: Données indisponibles\n"
            
    lol_elo_tracker.save_elo_data(elo_data)
    await loading_msg.edit(content=message)

# Fonction pour initialiser automatiquement les données d'elo LoL
async def initialize_lol_elo_data():
    """Initialise les données d'elo pour les joueurs LoL suivis"""
    try:
        print("⏳ Initialisation automatique des données d'elo LoL...")
        
        elo_data = lol_elo_tracker.load_elo_data()
        success_count = 0
        
        for player in LOL_TRACKED_PLAYERS:
            username = player["username"]
            region = player["region"]
            rank_info = lol_elo_tracker.fetch_lol_elo(username, region)
            
            if rank_info is not None:
                elo_data[username] = {
                    "region": region,
                    "start": {
                        "lp": rank_info["lp"],
                        "tier": rank_info["tier"],
                        "division": rank_info["division"]
                    },
                    "current": {
                        "lp": rank_info["lp"],
                        "tier": rank_info["tier"],
                        "division": rank_info["division"]
                    },
                    "rank": rank_info["name"]
                }
                success_count += 1
        
        lol_elo_tracker.save_elo_data(elo_data)
        print(f"✅ Données d'elo LoL initialisées pour {success_count}/{len(LOL_TRACKED_PLAYERS)} joueurs.")
        
        # Envoyer un message dans le canal si configuré
        if CHANNEL_ID != 0:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                message = f"✅ Données d'elo LoL initialisées pour {success_count}/{len(LOL_TRACKED_PLAYERS)} joueurs."
                await channel.send(message)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation des données d'elo LoL: {str(e)}")

# Commande !loltest
@bot.command()
async def loltest(ctx):
    """Envoie le message du matin avec l'elo des joueurs LoL"""
    loading_msg = await ctx.send("⏳ Génération du message du matin pour LoL...")
    try:
        message = await generate_lol_morning_message()
        await loading_msg.edit(content=message)
    except Exception as e:
        await loading_msg.edit(content=f"❌ Erreur lors de la génération du message: {str(e)}")

# Fonction pour générer le message du matin pour LoL
async def generate_lol_morning_message():
    """Génère le message avec l'élo et le rang des joueurs LoL"""
    message = "**🎮 C'est l'heure de LoL, champions ! Voici vos rangs actuels :**\n"
    for player in LOL_TRACKED_PLAYERS:
        username = player["username"]
        region = player["region"]
        rank_info = lol_elo_tracker.fetch_lol_elo(username, region)
        
        if rank_info is not None:
            rank_name = rank_info["name"]
            lp = rank_info["lp"]
            message += f"{username}: {rank_name} ({lp} LP)\n"
        else:
            message += f"{username}: N/A\n"
    return message

# Ajouter la tâche d'initialisation de l'elo LoL à minuit
@tasks.loop(minutes=1)
async def auto_init_lol_elo_at_midnight():
    """Initialise automatiquement les données d'elo LoL tous les jours à minuit heure de Paris"""
    try:
        now = datetime.now(PARIS_TZ).time()
        target_time = time(0, 0)  # Minuit
        
        # Vérifier si c'est minuit
        if now.hour == target_time.hour and now.minute == target_time.minute:
            print("🕛 Minuit : Initialisation automatique des données d'elo LoL...")
            await initialize_lol_elo_data()
    except Exception as e:
        print(f"❌ Erreur dans la tâche auto_init_lol_elo_at_midnight: {str(e)}")

# Ajouter la tâche d'envoi de message LoL
@tasks.loop(minutes=1)
async def send_lol_morning_message():
    """Envoie automatiquement le message LoL tous les jours à 9h30 heure de Paris"""
    try:
        if CHANNEL_ID == 0:
            print("⚠️ Aucun canal défini pour le message automatique")
            return
        
        now = datetime.now(PARIS_TZ).time()
        target_time = time(9, 30)  # 9h30 du matin
        
        # Vérifier si c'est l'heure d'envoyer le message
        if now.hour == target_time.hour and now.minute == target_time.minute:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                message = await generate_lol_morning_message()
                await channel.send(message)
                print(f"✅ Message du matin LoL envoyé dans le canal {channel.name}")
            else:
                print(f"⚠️ Impossible de trouver le canal ID: {CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Erreur dans la tâche send_lol_morning_message: {str(e)}")

# Initialiser les tâches automatiques
@send_lol_morning_message.before_loop
async def before_lol_morning_message():
    """Attendre que le bot soit prêt avant de démarrer la boucle"""
    await bot.wait_until_ready()
    print("⏳ Message automatique LoL initialisé.")

@auto_init_lol_elo_at_midnight.before_loop
async def before_auto_init_lol_elo():
    """Attendre que le bot soit prêt avant de démarrer la boucle"""
    await bot.wait_until_ready()
    print("⏳ Initialisation automatique d'elo LoL à minuit configurée.")

# Dans la fonction on_ready, ajoutez ces lignes pour démarrer les nouvelles tâches :
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    print("🚀 Bot prêt à l'emploi !")
    
    # Démarrer les tâches automatiques après que le bot soit prêt
    send_morning_message.start()
    auto_init_elo_at_midnight.start()
    # Nouvelles tâches pour LoL
    send_lol_morning_message.start()
    auto_init_lol_elo_at_midnight.start()

# Lancer le service web et le bot
if __name__ == "__main__":
    try:
        keep_alive()
        if DISCORD_TOKEN:
            bot.run(DISCORD_TOKEN)
        else:
            print("❌ Erreur : Le token du bot est manquant !")
    except discord.errors.LoginFailure:
        print("❌ Erreur : Token Discord invalide ou expiré !")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du bot : {str(e)}")
               
