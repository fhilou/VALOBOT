import requests
import json
import os
from datetime import datetime

# Constantes
ELO_FILE = "lol_elo_data.json"

# Fonction pour récupérer l'elo d'un joueur via l'API OP.GG
def fetch_lol_elo(username, region="euw"):
    """Récupère l'elo et le rang d'un joueur LoL via l'API non-officielle d'OP.GG"""
    try:
        # Nettoyer et encoder le nom d'utilisateur pour l'URL
        username = username.strip().replace(' ', '%20')
        region = region.lower().strip()
        
        print(f"Tentative de récupération de l'elo pour {username} ({region})")
            
        # Construire l'URL de l'API OP.GG
        url = f"https://op.gg/api/v1.0/summoners/{region}/name/{username}"
        
        # Ajouter un User-Agent pour éviter les blocages
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"URL de l'API: {url}")
        
        # Ajouter un timeout pour éviter des attentes infinies
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Réponse API pour {username} ({region}): Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Imprimer la structure pour le débogage
            print(f"Structure de la réponse JSON obtenue")
            
            # Récupérer les informations de rang
            rank_info = {}
            
            # Vérifier si les données de ranked solo sont disponibles
            if "league_stats" in data and data["league_stats"]:
                # Chercher les statistiques de ranked solo
                for queue in data["league_stats"]:
                    if queue.get("queue_info", {}).get("game_type") == "SOLORANKED":
                        tier = queue.get("tier_info", {}).get("tier", "Unranked")
                        division = queue.get("tier_info", {}).get("division", "")
                        lp = queue.get("tier_info", {}).get("lp", 0)
                        
                        # Construire les informations de rang
                        rank_name = f"{tier} {division}".strip() if division else tier
                        rank_info["name"] = rank_name
                        rank_info["tier"] = tier
                        rank_info["division"] = division
                        rank_info["lp"] = lp
                        
                        print(f"Rang trouvé: {rank_name}, LP: {lp}")
                        return rank_info
            
            # Si aucune donnée ranked solo n'a été trouvée
            print("Données de ranked solo non trouvées ou joueur non classé")
            rank_info["name"] = "Unranked"
            rank_info["tier"] = "Unranked"
            rank_info["division"] = ""
            rank_info["lp"] = 0
            return rank_info
                
        elif response.status_code == 404:
            print(f"Joueur non trouvé: {username} ({region})")
        else:
            print(f"Erreur API: {response.status_code}, {response.text}")
        return None
    except Exception as e:
        print(f"Exception lors de la récupération de l'elo: {str(e)}")
        return None

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

# Fonction pour calculer la différence de LP
def calculate_lp_diff(old_lp, old_tier, old_division, new_lp, new_tier, new_division):
    """Calcule la différence de LP en tenant compte des changements de division/tier"""
    # Définir les tiers dans l'ordre
    tiers = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
    divisions = ["IV", "III", "II", "I"]
    
    # Si le joueur était ou est non classé, la différence est incalculable
    if old_tier == "Unranked" or new_tier == "Unranked":
        return 0
    
    # Si les tiers sont les mêmes
    if old_tier == new_tier:
        # Si les divisions sont les mêmes, c'est une simple différence de LP
        if old_division == new_division:
            return new_lp - old_lp
        else:
            # Différence entre divisions (par exemple Gold IV à Gold III)
            old_div_index = divisions.index(old_division)
            new_div_index = divisions.index(new_division)
            # Chaque division = 100 LP
            div_diff = new_div_index - old_div_index
            return div_diff * 100 + new_lp - old_lp
    else:
        # Différence entre tiers (complexe)
        # Pour simplifier, nous supposons +100 LP pour chaque changement de niveau
        # Cette approximation n'est pas parfaite pour les rangs supérieurs
        try:
            old_tier_index = tiers.index(old_tier)
            new_tier_index = tiers.index(new_tier)
            tier_diff = new_tier_index - old_tier_index
            
            # Si old_tier < MASTER, tenir compte des divisions
            if old_tier_index < tiers.index("MASTER"):
                old_div_points = (divisions.index(old_division) + 1) * 100 - old_lp
            else:
                old_div_points = 0
                
            # Si new_tier < MASTER, tenir compte des divisions
            if new_tier_index < tiers.index("MASTER"):
                new_div_points = (divisions.index(new_division) + 1) * 100 - new_lp
            else:
                new_div_points = 0
                
            # Chaque tier a 4 divisions (sauf Master+)
            return tier_diff * 400 - old_div_points + new_div_points
        except ValueError:
            # Si un des tiers n'est pas reconnu
            return 0

# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple de joueurs à suivre
    TRACKED_PLAYERS = [
        {"username": "Faker", "region": "kr"},
        {"username": "irù", "region": "euw"},
        {"username": "fhilou", "region": "euw"},
        {"username": "igosano", "region": "euw"},
        {"username": "Anemonia", "region": "euw"},
        {"username": "Hartware", "region": "euw"},
        {"username": "JokyJokSsj", "region": "euw"},
    ]  
    
    # Initialiser ou charger les données
    elo_data = load_elo_data()
    
    # Mettre à jour les données pour chaque joueur
    for player in TRACKED_PLAYERS:
        username = player["username"]
        region = player["region"]
        rank_info = fetch_lol_elo(username, region)
        
        # Si les données sont récupérées avec succès
        if rank_info:
            # Initialiser l'entrée du joueur si elle n'existe pas
            if username not in elo_data:
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
                print(f"Joueur {username} initialisé: {rank_info['name']} {rank_info['lp']} LP")
            else:
                # Calculer la différence de LP
                old_lp = elo_data[username]["current"]["lp"]
                old_tier = elo_data[username]["current"]["tier"]
                old_division = elo_data[username]["current"]["division"]
                
                lp_diff = calculate_lp_diff(
                    old_lp, old_tier, old_division,
                    rank_info["lp"], rank_info["tier"], rank_info["division"]
                )
                
                # Mettre à jour les données
                elo_data[username]["current"]["lp"] = rank_info["lp"]
                elo_data[username]["current"]["tier"] = rank_info["tier"]
                elo_data[username]["current"]["division"] = rank_info["division"]
                elo_data[username]["rank"] = rank_info["name"]
                
                print(f"Joueur {username} mis à jour: {rank_info['name']} {rank_info['lp']} LP (Diff: {'+' if lp_diff >= 0 else ''}{lp_diff} LP)")
    
    # Sauvegarder les données
    save_elo_data(elo_data)
