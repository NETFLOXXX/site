import requests
import re
import json
from datetime import datetime, timezone

MOVIX_URL = "https://t.me/s/movix_site"
STREAMFLIX_URL = "https://t.me/s/streamflixoff"
KWEFLIX_CONFIG_URL = "https://kweflix.com/config.js?v=4"
CINEPULSE_CONFIG_URL = "https://cinepulse.wiki/site.js?v=7"

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


def get_kweflix_url():
    """
    Kweflix affiche son domaine actif via un fichier de config JS
    (config.js), chargé dynamiquement en JS sur la page d'accueil.
    On va donc chercher directement dedans plutôt que de parser le HTML.
    """
    try:
        resp = requests.get(KWEFLIX_CONFIG_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        text = resp.text

        # Vérifie le statut du site (online / down)
        status_match = re.search(r"STATUS\s*:\s*'([^']+)'", text)
        status = status_match.group(1) if status_match else None
        if status and status.lower() != "online":
            print(f"Kweflix: statut = {status} (site hors ligne)")
            return None

        # Priorité à SITE_URL, sinon on retombe sur DOMAIN
        site_url_match = re.search(r"SITE_URL\s*:\s*'([^']+)'", text)
        if site_url_match:
            return normalize_https(site_url_match.group(1))

        domain_match = re.search(r"DOMAIN\s*:\s*'([^']+)'", text)
        if domain_match:
            return normalize_https(domain_match.group(1))

    except Exception as e:
        print(f"Erreur Kweflix: {e}")
    return None


def get_cinepulse_url():
    """
    CinePulse affiche son domaine actif directement dans site.js
    sous la forme : const SITE_DOMAIN = "domaine.tld";
    """
    try:
        resp = requests.get(
            CINEPULSE_CONFIG_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        resp.raise_for_status()
        text = resp.text

        domain_match = re.search(
            r'const\s+SITE_DOMAIN\s*=\s*["\']([^"\']+)["\']',
            text
        )

        if domain_match:
            return normalize_https(domain_match.group(1))

    except Exception as e:
        print(f"Erreur CinePulse: {e}")
    return None


def main():
    data = {
        "movix_url": get_movix_url(),
        "streamflix_url": get_streamflix_bio_url(),
        "kweflix_url": get_kweflix_url(),
        "cinepulse_url": get_cinepulse_url(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
