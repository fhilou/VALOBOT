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
        target_time = time(9, 0)  # 📌 Heure cible (9h00)

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
        target = datetime.combine(now.date(), time(11, 30), PARIS_TZ)

        if now >= target:
            target += timedelta(days=1)  # 📌 Si l'heure est passée, on vise demain

        wait_time = (target - now).total_seconds()
        await discord.utils.sleep_until(target)
        print(f"⏳ Message automatique programmé pour {target}.")


# ========================== #
# 📌 AJOUT DES COMMANDES     #
# ========================== #
def setup_commands(bot):
    bot.add_cog(Test(bot))  # 📌 Ajout de la commande + tâche auto
    print("✅ Commandes chargées avec succès !")
    return True

