from flask import Flask, redirect, request, render_template
import requests
import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TARGET_GUILD_ID = os.getenv("TARGET_GUILD_ID")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["verifybot"]
users = db["users"]

API_BASE_URL = "https://discord.com/api"
SCOPE = "identify guilds guilds.join"

@app.route("/")
def index():
    return redirect("/login")

@app.route("/login")
def login():
    SCOPE = "identify guilds guilds.join"
    return redirect(
        f"https://discord.com/api/oauth2/authorize?"
        f"client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPE}"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Erro: código não encontrado", 400

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": "identify guilds guilds.join",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    token_response.raise_for_status()
    tokens = token_response.json()
    access_token = tokens.get("access_token")

    user_response = requests.get(f"{API_BASE_URL}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    user_response.raise_for_status()
    user_data = user_response.json()

    users.update_one(
        {"user_id": user_data["id"]},
        {"$set": {
            "user_id": user_data["id"],
            "username": f'{user_data["username"]}#{user_data["discriminator"]}',
            "avatar": user_data.get("avatar"),
            "access_token": access_token,
        }},
        upsert=True
    )

    return render_template("success.html", username=f'{user_data["username"]}#{user_data["discriminator"]}')

@app.route("/puxar_usuarios")
def puxar_usuarios():
    @app.route("/puxar_usuarios")
def puxar_usuarios():
    senha = request.args.get("senha")
    if senha != "MORFEUSBOTDEV12":
        return "Senha inválida", 403

    # Exemplo: simulação de retorno de usuários autorizados
    return jsonify([
        {"id": "123", "username": "Exemplo#0001"},
        {"id": "456", "username": "Teste#1234"}
    ])

    return "✅ Rota ativa!"

    if not DISCORD_BOT_TOKEN or not TARGET_GUILD_ID:
        return "Bot Token ou Guild ID não configurado", 500

    resultados = []
    for user in users.find():
        user_id = user.get("user_id")
        access_token = user.get("access_token")
        if not user_id or not access_token:
            continue

        response = requests.put(
            f"{API_BASE_URL}/guilds/{TARGET_GUILD_ID}/members/{user_id}",
            headers={
                "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"access_token": access_token}
        )

        if response.status_code in (201, 204):
            resultados.append(f"{user_id}: ✅ Adicionado")
        else:
            resultados.append(f"{user_id}: ❌ Erro {response.status_code} - {response.text}")

        time.sleep(1)

    return "<br>".join(resultados)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
