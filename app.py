from flask import Flask, request, jsonify
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")


def load_keywords():
    with open("keywords.json", "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"🔍 mode={mode} | token_recibido={token} | VERIFY_TOKEN={VERIFY_TOKEN}")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado por Meta")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()

    if data.get("object") == "instagram":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "comments":
                    comment_data = change.get("value", {})
                    handle_comment(comment_data)

    return "OK", 200


def handle_comment(comment_data):
    comment_text = comment_data.get("text", "").lower()
    comment_id = comment_data.get("id")
    commenter_id = comment_data.get("from", {}).get("id")

    print(f"💬 Comentario recibido: '{comment_text}'")

    keywords = load_keywords()

    for keyword, config in keywords.items():
        if keyword.lower() in comment_text:
            print(f"🎯 Palabra clave detectada: '{keyword}'")
            reply_to_comment(comment_id, config["reply"])
            send_dm(commenter_id, config["dm"])
            break


def reply_to_comment(comment_id, message):
    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    result = response.json()
    print(f"📩 Respuesta a comentario: {result}")
    return result


def send_dm(user_id, message):
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message},
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    result = response.json()
    print(f"📨 DM enviado: {result}")
    return result


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Servidor iniciado en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
