import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_gui_message(chat_id, text, reply_markup):
    """Sends a message containing the interactive inline keyboard GUI"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup,
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"GUI transmission failure: {e}")

def fetch_tmdb_metadata(query):
    """Fetches high-accuracy content metadata using the verified TMDB link"""
    if not TMDB_API_KEY:
        return None
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query}
    try:
        res = requests.get(search_url, params=params, timeout=5).json()
        if res.get("results"):
            top_match = res["results"][0]
            # Fetch secondary layer to secure the internal IMDb ID tracking metric
            details_url = f"https://api.themoviedb.org/3/movie/{top_match['id']}"
            details = requests.get(details_url, params={"api_key": TMDB_API_KEY}, timeout=5).json()
            return {
                "id": top_match["id"],
                "imdb_id": details.get("imdb_id"),
                "title": top_match["title"],
                "year": top_match.get("release_date", "0000")[:4],
                "rating": top_match.get("vote_average", "N/A")
            }
    except Exception as e:
        print(f"Metadata routing error: {e}")
    return None

@app.route('/', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"].strip()
        
        if user_text.startswith("/start"):
            welcome = (
                "🤖 *Welcome to the Advanced Media GUI Bot!*\n\n"
                "Send me any movie name, and I will generate an interactive "
                "control display containing alternative server links and download indices."
            )
            # Empty markup for start command
            send_gui_message(chat_id, welcome, {"inline_keyboard": []})
            
        else:
            movie = fetch_tmdb_metadata(user_text)
            
            if movie:
                tmdb_id = movie["id"]
                imdb_id = movie["imdb_id"]
                encoded_title = movie["title"].replace(" ", "+")
                
                # Header layout mimicking the structure in file 5db8e766-35f4-49ce-b58d-5c663b550d9b
                header_text = (
                    f"🔍 *What I Found In My Database For Your Query* 👇\n\n"
                    f"🎬 *Name:* {movie['title']} ({movie['year']})\n"
                    f"⭐ *Rating:* {movie['rating']}/10\n\n"
                    f"👇 _Select a streaming link or file index target below:_ "
                )
                
                # Build the interactive button matrix
                inline_keyboard = [
                    # Row 1: Player Stream Servers
                    [
                        {"text": "🌐 Server Alpha (VidSrc)", "url": f"https://vidsrc.cc/v2/embed/movie/{tmdb_id}"},
                    ],
                    # Row 2: Secondary Player Stream
                    [
                        {"text": "🌐 Server Beta (2Embed)", "url": f"https://www.2embed.cc/embed/{tmdb_id}"}
                    ],
                    # Row 3: Download Index targets (mimicking quality variations)
                    [
                        {"text": "💾 1080p / 720p File Indexes (YTS)", "url": f"https://yts.mx/browse-movies/{encoded_title}"}
                    ]
                ]
                
                # If an IMDb ID exists, append an alternative tracker source button
                if imdb_id:
                    inline_keyboard.append([
                        {"text": "📁 HQ Untouched Formats (Galaxy)", "url": f"https://torrentgalaxy.to/torrents.php?search={imdb_id}"}
                    ])
                
                # Row 5: Navigation cluster mapping the design from your screenshot
                inline_keyboard.append([
                    {"text": "⏮️ BACK", "url": "https://t.me/"}, 
                    {"text": "NEXT ⏭️", "url": "https://t.me/"}
                ])
                
                reply_markup = {"inline_keyboard": inline_keyboard}
                send_gui_message(chat_id, header_text, reply_markup)
                
            else:
                send_gui_message(chat_id, "❌ *Error:* Title not found in active metadata registry.", {"inline_keyboard": []})
                
    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
def health_check():
    return "GUI Core Operational", 200
