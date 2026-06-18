import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Secure configurations loaded dynamically from Vercel env
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_gui_message(chat_id, text, reply_markup=None):
    """Sends a formatted layout message using HTML mode to prevent parsing crashes"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Telegram response: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Telegram transmission failure: {e}")

def discover_media_omdb(query):
    """Queries the open OMDb API using your active free key"""
    if not OMDB_API_KEY:
        print("Error: OMDB_API_KEY configuration variable is missing on Vercel.")
        return None
        
    url = "http://www.omdbapi.com/"
    params = {
        "apikey": OMDB_API_KEY,
        "s": query
    }
    
    try:
        response = requests.get(url, params=params, timeout=5).json()
        if response.get("Response") == "True" and response.get("Search"):
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

# Listens to both the root and the /api subfolder endpoint automatically
@app.route('/', methods=['POST'])
@app.route('/api', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"].strip()
        
        if user_text.startswith("/start"):
            welcome = (
                "🤖 <b>Welcome to the OMDb Media Keyboard Bot!</b>\n\n"
                "Send me a cinema or web series title. I will parse OMDb "
                "to instantly construct active player links."
            )
            send_gui_message(chat_id, welcome)
            
        else:
            send_gui_message(chat_id, f"🔍 <b>Parsing OMDb catalogs for:</b> <code>{user_text}</code>...")
            
            media = discover_media_omdb(user_text)
            
            if media:
                imdb_id = media["imdb_id"]
                title_url = media["search_title"]
                media_type = media["type"]
                
                header_text = (
                    f"🍿 <b>What I Found In My Database</b> 👇\n\n"
                    f"🎬 <b>Name:</b> {media['title']} ({media['year']})\n"
                    f"📌 <b>Type:</b> {media_type.upper()}\n\n"
                    f"👇 <i>Select an automated server path below:</i>"
                )
                
                inline_keyboard = []
                
                if media_type == "movie":
                    inline_keyboard.append([{"text": "🌐 Server Alpha (VidSrc Stream)", "url": f"https://vidsrc.cc/v2/embed/movie/{imdb_id}"}])
                    inline_keyboard.append([{"text": "🌐 Server Beta (SmashyStream)", "url": f"https://player.smashy.stream/movie/{imdb_id}"}])
                    inline_keyboard.append([{"text": "💾 Torrent Indexes (YTS)", "url": f"https://yts.mx/browse-movies/{title_url}"}])
                else:
                    inline_keyboard.append([{"text": "🌐 Stream Series (S1:E1 Player)", "url": f"https://vidsrc.cc/v2/embed/tv/{imdb_id}/1/1"}])
                    inline_keyboard.append([{"text": "📁 Torrent Galaxy Hub", "url": f"https://torrentgalaxy.to/torrents.php?search={imdb_id}"}])
                
                send_gui_message(chat_id, header_text, {"inline_keyboard": inline_keyboard})
            else:
                send_gui_message(chat_id, "❌ <b>Error:</b> Could not identify any asset matches in the OMDb registry.")
                
    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
def health_check():
    return "OMDb HTML Pipeline Active", 200
