# Modification pour bot.py

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from keep_alive import keep_alive
from api import fetch_elo
import importlib.util
import sys

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction pour importer manuellement un module depuis un chemin de fichier
def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        print(f"Impossible de charger le module {module_name} depuis {file_path}")
        return None
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        print(f"Module {module_name} chargé avec succès!")
        return module
    except Exception as e:
        print(f"Erreur lors du chargement de {module_name}: {e}")
        return None

# Charger manuellement chaque module de commande
current_dir = os.path.dirname(os.path.abspath(__file__))
cmds_dir = os.path.join(current_dir, "cmds")

print(f"Répertoire des commandes: {cmds_dir}")
print(f"Le répertoire existe: {os.path.exists(cmds_dir)}")

if os.path.exists(cmds_dir):
    print(f"Contenu du répertoire des commandes: {os.listdir(cmds_dir)}")
    
    # Charger le module elo
    elo_module = import_module_from_file("elo_module", os.path.join(cmds_dir, "elo.py"))
    if elo_module and hasattr(elo_module, "Elo"):
        bot.add_cog(elo_module.Elo(bot))
    
    # Charger le module recap
    recap_module = import_module_from_file("recap_module", os.path.join(cmds_dir, "recap.py"))
    if recap_module and hasattr(recap_module, "Recap"):
        bot.add_cog(recap_module.Recap(bot))
    
    # Charger le module test
    test_module = import_module_from_file("test_module", os.path.join(cmds_dir, "test.py"))
    if test_module and hasattr(test_module, "Test"):
        bot.add_cog(test_module.Test(bot))
    
    # Charger le module help
    help_module = import_module_from_file("help_module", os.path.join(cmds_dir, "help.py"))
    if help_module and hasattr(help_module, "Help"):
        bot.add_cog(help_module.Help(bot))
else:
    print("Le dossier des commandes n'existe pas!")

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    # Afficher les commandes chargées
    print("Commandes chargées:")
    for command in bot.commands:
        print(f"- {command.name}")

# Garder le bot en vie et le lancer
keep_alive()
bot.run(TOKEN)
