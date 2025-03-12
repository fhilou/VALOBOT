from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne!"

def run():
    # Utiliser le port dynamique attribué par Render ou 8080 par défaut
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
