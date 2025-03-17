# Supprimez la commande reload actuelle
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
            current_elo = fetch_elo(username, tag)
            
            if current_elo is not None:
                if username not in elo_data:
                    elo_data[username] = {"tag": tag, "start": current_elo, "current": current_elo}
                else:
                    # Mettre à jour seulement la valeur actuelle, pas la valeur de départ
                    elo_data[username]["current"] = current_elo
                success_count += 1
        
        save_elo_data(elo_data)
        
        await ctx.send(f"✅ Données d'elo rechargées pour {success_count}/{len(TRACKED_PLAYERS)} joueurs.")
    except Exception as e:
        await ctx.send(f"❌ Erreur lors du rechargement : {e}")

# Modification du système de stockage JSON
# Remplacez le code actuel par ceci:

# Définir un chemin de fichier plus stable
ELO_FILE = "elo_data.json"

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

# Modifiez la fonction fetch_elo pour corriger les problèmes d'API
def fetch_elo(username, tag):
    """Récupère l'elo d'un joueur via l'API HenrikDev"""
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
                if "currenttier" in data["data"]:
                    # Récupérer les RR de la réponse
                    if "ranking_in_tier" in data["data"]:
                        elo = data["data"]["ranking_in_tier"]
                        print(f"Elo trouvé: {elo} RR")
                        return elo
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
