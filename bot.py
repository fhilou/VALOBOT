import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from keep_alive import keep_alive

# Charger les variables d'environnement depuis .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Initialiser le bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Connecté en tant que {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.lower() == "ping":
        await message.channel.send("Pong!")

keep_alive() 

# Lancer le bot
client.run(TOKEN)