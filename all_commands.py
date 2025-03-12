# all_commands.py - Regroupement de toutes les commandes

import discord
import json
import os
from discord.ext import commands, tasks
from api import fetch_elo
from datetime import datetime, time, timedelta
import pytz  # 📌 Permet de gérer le fuseau horaire

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


# ========================== #
# 📌 COMMANDE !test + AUTO  #
# ========================== #
class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = None  # 📌 ID du canal où envoyer le message du matin
        self.send_morning_message.start()  # 📌 Lance la boucle automatique

    @commands.command()
    async def test(self, ctx):
        """Envoie le message du matin avec l'elo des joueurs"""
        message = self.generate_message()
        await ctx.send(message)

    @commands.command()
    async def setchannel(self, ctx):
        """Définit ce canal comme celui pour le message automatique"""
        self.channel_id = ctx.channel.id
        await ctx.send("✅ Ce canal a été enregistré pour le message du matin.")

    def generate_message(self):
        """Génère le message avec l'élo des joueurs"""
        message = "**🎯 Réveillez-vous les loosers, c'est l'heure de VALO !**\n"
        for player in TRACKED_PLAYERS:
            username = player["username"]
            tag = player["tag"]
            elo = fetch_elo(username, tag)
            message += f"{username}: {elo if elo is not None else 'N/A'} RR\n"
        return message

    @tasks.loop(minutes=1)
    async def send_morning_message(self):
        """Envoie automatiquement le message tous les jours à 9h heure de Paris"""
        if self.channel_id is None:
            return  # 📌 Pas de canal défini, on ne fait rien

        now = datetime.now(PARIS_TZ).time()  # 📌 Heure actuelle à Paris
        target_time = time(12, 0)  # 📌 Heure cible (9h00)

        if now.hour == target_time.hour and now.minute == target_time.minute:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(self.generate_message())
            else:
                print("⚠️ Impossible de trouver le canal enregistré.")

    @send_morning_message.before_loop
    async def before_morning_message(self):
        """Attendre le bon moment avant de démarrer la boucle"""
        await self.bot.wait_until_ready()
        now = datetime.now(PARIS_TZ)
        target = datetime.combine(now.date(), time(12, 0), PARIS_TZ)  # Uniformiser à 9h00

        if now >= target:
            target += timedelta(days=1)  # 📌 Si l'heure est passée, on vise demain

        wait_time = (target - now).total_seconds()
        print(f"⏳ Message automatique programmé pour {target}.")


# ========================== #
# 📌 COMMANDE !elo          #
# ========================== #
class Elo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def elo(self, ctx, username: str, tag: str):
        """Affiche l'elo d'un joueur spécifique"""
        elo = fetch_elo(username, tag)
        if elo is not None:
            await ctx.send(f"**{username}#{tag}** a un elo de **{elo} RR**.")
        else:
            await ctx.send(f"Impossible de récupérer l'élo de **{username}#{tag}**.")


# ========================== #
# 📌 COMMANDE !help         #
# ========================== #
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Affiche la liste des commandes disponibles"""
        help_message = (
            "**Liste des commandes :**\n"
            "`!elo <username> <tag>` - Affiche l'elo d'un joueur spécifique.\n"
            "`!recap` - Affiche les gains/pertes d'elo de la journée.\n"
            "`!test` - Envoie le message du jour avec l'élo actuel des joueurs.\n"
            "`!setchannel` - Définit le canal pour le message automatique du matin.\n"
            "`!help` - Affiche cette aide."
        )
        await ctx.send(help_message)


# ========================== #
# 📌 COMMANDE !recap        #
# ========================== #
class Recap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_elo_data(self):
        """Charge les données d'elo enregistrées."""
        if os.path.exists(ELO_FILE):
            with open(ELO_FILE, "r") as file:
                return json.load(file)
        return {}

    def save_elo_data(self, data):
        """Sauvegarde les nouvelles valeurs d'elo."""
        with open(ELO_FILE, "w") as file:
            json.dump(data, file, indent=4)

    @commands.command()
    async def recap(self, ctx):
        """Affiche le récapitulatif des gains/pertes d'elo aujourd'hui"""
        elo_data = self.load_elo_data()
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

        self.save_elo_data(elo_data)
        await ctx.send(message)


# ========================== #
# 📌 AJOUT DES COMMANDES     #
# ========================== #
def setup_commands(bot):
    # Ajout de toutes les classes de commandes
    bot.add_cog(Test(bot))
    bot.add_cog(Elo(bot))
    bot.add_cog(Help(bot))
    bot.add_cog(Recap(bot))
    
    print("✅ Commandes chargées avec succès !")
    return True
