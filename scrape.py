import requests
import re
import json
from datetime import datetime, timezone

MOVIX_URL = "https://t.me/s/movix_site"
STREAMFLIX_URL = "https://t.me/s/streamflixoff"

MOVIX_PATTERN = r'(https?://[^\s"\'<]*movix[^\s"\'<]*|\bmovix\.[a-z]{2,10}\b)'
GENERIC_PATTERN = r'(https?://[^\s"\'<]+|\b[a-z0-9-]+\.[a-z]{2,10}\b)'


def normalize_https(url):
    if not url.startswith("http"):
        return "https://" + url
    return url.replace("http://", "https://")


def get_movix_url():
    resp = requests.get(MOVIX_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    messages = re.findall(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL
    )

    for message in reversed(messages):
        matches = re.findall(MOVIX_PATTERN, message, re.IGNORECASE)
        if matches:
            return normalize_https(matches[0])

    return None


def get_streamflix_bio_url():
    resp = requests.get(STREAMFLIX_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    match = re.search(
        r'<div class="tgme_channel_info_description">(.*?)</div>',
        html,
        re.DOTALL
    )

    if not match:
        return None

    bio_html = match.group(1)
    bio_text = re.sub(r'<[^>]+>', ' ', bio_html)

    urls = re.findall(GENERIC_PATTERN, bio_text, re.IGNORECASE)
    if not urls:
        return None

    return normalize_https(urls[0])


def main():
    data = {
        "movix_url": get_movix_url(),
        "streamflix_url": get_streamflix_bio_url(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    with open("latest.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
