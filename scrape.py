import requests
import re
import json
from datetime import datetime, timezone

URL = "https://t.me/s/movix_site"
PATTERN = r'(https?://[^\s"\'<]*movix[^\s"\'<]*|\bmovix\.[a-z]{2,10}\b)'

def get_latest_movix_url():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    messages = re.findall(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL
    )

    for message in reversed(messages):
        matches = re.findall(PATTERN, message, re.IGNORECASE)
        if matches:
            url = matches[0]
            if not url.startswith("http"):
                url = "https://" + url
            else:
                url = url.replace("http://", "https://")
            return url

    return None

def main():
    latest = get_latest_movix_url()
    data = {
        "url": latest,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    with open("latest.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()