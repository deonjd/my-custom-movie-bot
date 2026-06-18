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
                "search_title": top_match.get("
