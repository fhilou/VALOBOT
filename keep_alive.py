from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne!"

def run():
    # Utilisation du port dynamique de Render
    port = int(os.getenv("PORT", 8080))  # Utilise le port de l'environnement ou 8080 par défaut
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
