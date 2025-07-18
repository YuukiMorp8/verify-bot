from flask import Flask, redirect, request, render_template
import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
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
    return redirect(
        f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}"
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
        "scope": SCOPE,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")

    user_response = requests.get(f"{API_BASE_URL}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    user_response.raise_for_status()
    user_data = user_response.json()

    # Salvar dados do usuário no MongoDB
    users.update_one(
        {"user_id": user_data["id"]},
        {"$set": {
            "user_id": user_data["id"],
            "username": f'{user_data["username"]}#{user_data["discriminator"]}',
            "avatar": user_data.get("avatar"),
        }},
        upsert=True
    )

    return render_template("success.html", username=f'{user_data["username"]}#{user_data["discriminator"]}')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
