import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")

def fetch_elo(username, tag):
    """Récupère l'elo d'un joueur via l'API HenrikDev"""
    url = f"https://api.henrikdev.xyz/valorant/v2/mmr/{tag}/{username}"
    headers = {"Authorization": f"Bearer {HENRIKDEV_API_KEY}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data["data"].get("elo", 0)  # Retourne l'elo actuel du joueur
    return None
