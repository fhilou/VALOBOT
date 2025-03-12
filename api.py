import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
dotenv_path = ".env"
load_dotenv(dotenv_path)
HENRIKDEV_API_KEY = os.getenv("HENRIKDEV_API_KEY")

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
