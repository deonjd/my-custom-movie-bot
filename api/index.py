import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Secure configurations loaded dynamically from Vercel env
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_gui_message(chat_id, text, reply_markup):
    """Sends a formatted layout message containing the interactive inline keyboard GUI"""
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
    except Exception as e:
        print(f"Telegram transmission failure: {e}")

def discover_media_omdb(query):
    """
    Queries the open OMDb API using your free key.
    Fetches the closest title search match and exposes its true IMDb ID tag.
    """
    if not OMDB_API_KEY:
        print("Error: OMDB_API_KEY configuration variable is missing on Vercel.")
        return None
        
    url = "http://www.omdbapi.com/"
    # We query using the 's' parameter (Search) to pull the absolute closest target match
    params = {
        "apikey": OMDB_API_KEY,
        "s": query
    }
    
    try:
        response = requests.get(url, params=params, timeout=5).json()
        if response.get("Response") == "True" and response.get("Search"):
            # Target the first match in the metadata cluster
            top_match = response["Search"][0]
            return {
                "title": top_match.get("Title"),
                "year": top_match.get("Year"),
                "imdb_id": top_match.get("imdbID"),
                "type": top_match.get("Type", "movie"),
                "search_title": top_match.get("Title").replace(" ", "+")
            }
    except Exception as e:
        print(f"OMDb backend fetching failure: {e}")
    return None

@app.route('/', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"].strip()
        
        if user_text.startswith("/start"):
            welcome = (
                "🤖 *Welcome to the OMDb Media Keyboard Bot!*\n\n"
                "Send me a cinema or web series title. I will parse OMDb "
                "to instantly construct active player links and download indices."
            )
            send_gui_message(chat_id, welcome, {"inline_keyboard": []})
            
        else:
            send_gui_message(chat_id, f"🔍 *Parsing OMDb catalogs for:* `{user_text}`...", {"inline_keyboard": []})
            
            media = discover_media_omdb(user_text)
            
            if media:
                imdb_id = media["imdb_id"]
                title_url = media["search_title"]
                media_type = media["type"]  # Can return 'movie' or 'series'
                
                # Header layout that mirrors the file database search designs
                header_text = (
                    f"🍿 *What I Found In My Database for Your Query* 👇\n\n"
                    f"🎬 *Name:* {media['title']} ({media['year']})\n"
                    f"📌 *Type:* {media_type.upper()}\n\n"
                    f"👇 _Select an automated server path below:_ "
                )
                
                inline_keyboard = []
                
                # Build standard streaming player nodes based on the verified IMDb identifier
                if media_type == "movie":
                    inline_keyboard.append([{"text": "🌐 Server Alpha (VidSrc 1080p Stream)", "url": f"https://vidsrc.cc/v2/embed/movie/{imdb_id}"}])
                    inline_keyboard.append([{"text": "🌐 Server Beta (SmashyStream)", "url": f"https://player.smashy.stream/movie/{imdb_id}"}])
                    inline_keyboard.append([{"text": "💾 Torrent Indexes & Configurations (YTS)", "url": f"https://yts.mx/browse-movies/{title_url}"}])
                else:
                    # Web series stream template (Points default targeting to Season 1 Episode 1)
                    inline_keyboard.append([{"text": "🌐 Stream Series (S1:E1 Player)", "url": f"https://vidsrc.cc/v2/embed/tv/{imdb_id}/1/1"}])
                    inline_keyboard.append([{"text": "📁 Torrent Galaxy Directory Hub", "url": f"https://torrentgalaxy.to/torrents.php?search={imdb_id}"}])
                
                # Clean GUI interface footer navigation mapping
                inline_keyboard.append([
                    {"text": "⏮️ BACK", "url": "https://t.me/"}, 
                    {"text": "NEXT ⏭️", "url": "https://t.me/"}
                ])
                
                send_gui_message(chat_id, header_text, {"inline_keyboard": inline_keyboard})
            else:
                send_gui_message(chat_id, "❌ *Error:* Could not identify any asset matches in the OMDb registry.", {"inline_keyboard": []})
                
    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
def health_check():
    return "OMDb Pipeline Active", 200
