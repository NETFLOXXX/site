import requests
import re
import json
from datetime import datetime, timezone

MOVIX_URL = "https://t.me/s/movix_site"
STREAMFLIX_URL = "https://t.me/s/streamflixoff"

MOVIX_PATTERN = r'(https?://[^\s"\'<]*movix[^\s"\'<]*|\bmovix\.[a-z]{2,10}\b)'
GENERIC_PATTERN = r'(https?://[^\s"\'<]+|\b[a-z0-9-]+\.[a-z]{2,10}\b)'

def normalize_https(url):
    url = url.rstrip('/')
    if not url.startswith("http"):
        return "https://" + url
    return url.replace("http://", "https://")

def get_movix_url():
    try:
        resp = requests.get(MOVIX_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        messages = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
        for message in reversed(messages):
            matches = re.findall(MOVIX_PATTERN, message, re.IGNORECASE)
            if matches:
                return normalize_https(matches[0])
    except Exception as e:
        print(f"Erreur Movix: {e}")
    return None

def get_streamflix_bio_url():
    try:
        resp = requests.get(STREAMFLIX_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        match = re.search(r'<div class="tgme_channel_info_description">(.*?)</div>', resp.text, re.DOTALL)
        if match:
            bio_text = re.sub(r'<[^>]+>', ' ', match.group(1))
            urls = re.findall(GENERIC_PATTERN, bio_text, re.IGNORECASE)
            if urls:
                return normalize_https(urls[0])
    except Exception as e:
        print(f"Erreur Streamflix: {e}")
    return None

def main():
    data = {
        "movix_url": get_movix_url(),
        "streamflix_url": get_streamflix_bio_url(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
    
