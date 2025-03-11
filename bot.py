# Dans bot.py, ajoutez ces lignes de débogage au début
import sys
import os

# Afficher le répertoire de travail actuel
current_dir = os.getcwd()
print(f"Répertoire de travail actuel: {current_dir}")

# Afficher le contenu du répertoire
print(f"Contenu du répertoire: {os.listdir(current_dir)}")

# Chemin du dossier cmds
cmds_path = os.path.join(os.path.dirname(__file__), "cmds")
print(f"Chemin des commandes calculé: {cmds_path}")

# Vérifier si le dossier existe
if os.path.exists(cmds_path):
    print(f"Le dossier cmds existe. Contenu: {os.listdir(cmds_path)}")
else:
    print(f"ERREUR: Le dossier cmds n'existe PAS!")

sys.path.append(cmds_path)

# Ajout du chemin du dossier cmds (ex-commands)
cmds_path = os.path.join(os.path.dirname(__file__), "cmds")
sys.path.append(cmds_path)
print("Chemin des commandes ajouté :", cmds_path)

# Importation des modules
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from api import fetch_elo  # Si ce fichier existe
import cmds.elo
import cmds.recap
import cmds.test
import cmds.help

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Ajouter les commandes
bot.add_cog(cmds.elo.Elo(bot))
bot.add_cog(cmds.recap.Recap(bot))
bot.add_cog(cmds.test.Test(bot))
bot.add_cog(cmds.help.Help(bot))

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

# Garder le bot en vie et le lancer
keep_alive()
bot.run(TOKEN)


