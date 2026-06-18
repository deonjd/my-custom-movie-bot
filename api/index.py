import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Retrieve token from Vercel's hidden environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    """Sends a clean payload back to Telegram's official servers"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

@app.route('/', methods=['POST'])
def telegram_webhook():
    """Vercel triggers this function every time your bot gets a message"""
    update = request.get_json()
    
    # Verify the incoming JSON contains a valid text message
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"].strip()
        
        # Command: /start
        if user_text.startswith("/start"):
            welcome_msg = (
                "🍿 *Welcome to MovieBot!*\n\n"
                "Send me any movie or series title, and I will instantly "
                "generate a streaming and download link for you."
            )
            send_message(chat_id, welcome_msg)
            
        # Movie Queries
        else:
            send_message(chat_id, f"🔍 *Searching for:* `{user_text}`...")
            
            # Format the title for URL safety (e.g., "Inter Stellar" becomes "Inter+Stellar")
            formatted_query = user_text.replace(" ", "+")
            
            # Modern free API structure that serves active video player embeds automatically
            streaming_url = f"https://vidsrc.xyz/embed/movie?q={formatted_query}"
            
            reply = (
                f"🎬 *Result Found!*\n\n"
                f"🍿 *Title:* {user_text}\n"
                f"🔗 *Watch/Download Link:* [Click Here to Stream]({streaming_url})\n\n"
                f"_⚠️ Tip: Make sure to use an ad-blocker for a smooth viewing experience!_"
            )
            send_message(chat_id, reply)
            
    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
def health_check():
    """Allows you to test if your URL is alive using your web browser"""
    return "Movie Bot Engine is fully operational!", 200
