import discord
import os
from discord.ext import commands
from all_commands import setup_commands  # 📌 Importation des commandes
from keep_alive import keep_alive  # 📌 Service web pour Render

# ========================== #
# 📌 CONFIGURATION DU BOT   #
# ========================== #

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Supprimer la commande `help` par défaut pour éviter les conflits
bot.remove_command("help")


# ========================== #
# 📌 ÉVÉNEMENTS DU BOT      #
# ========================== #

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    success = setup_commands(bot)  # Charger toutes les commandes
    
    # Afficher les commandes disponibles pour vérification
    commands_list = [command.name for command in bot.commands]
    print(f"📋 Commandes enregistrées : {commands_list}")
    
    print("🚀 Bot prêt à l'emploi !")

@bot.event
async def on_command_error(ctx, error):
    """Gère les erreurs de commandes."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Commande inconnue. Tape `!help` pour voir les commandes disponibles.")
    else:
        await ctx.send(f"⚠️ Une erreur est survenue : {error}")
        raise error  # Affiche l'erreur dans la console


# ========================== #
# 📌 DÉMARRAGE DU BOT      #
# ========================== #

keep_alive()  # 📌 Lance le service web pour garder le bot actif

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Erreur : Le token du bot est manquant !")
