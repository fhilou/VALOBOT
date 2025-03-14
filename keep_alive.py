from flask import Flask
from threading import Thread
import os
import logging

# Configurer le logging pour Flask
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)  # Réduire le niveau de log pour éviter la pollution de la console

app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne!"

@app.route('/status')
def status():
    return {"status": "online", "message": "Le bot est en ligne!"}

def run():
    try:
        # Utiliser le port dynamique attribué par Render ou 8080 par défaut
        port = int(os.environ.get("PORT", 8080))
        # Mode debug désactivé pour éviter les redémarrages automatiques
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur web: {str(e)}")

def keep_alive():
    try:
        t = Thread(target=run)
        t.daemon = True  # Assurer que le thread se termine quand le programme principal se termine
        t.start()
        print("🌐 Serveur web démarré avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du thread keep_alive: {str(e)}")
