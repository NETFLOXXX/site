"""
Gestionnaire de quota multi-clés ZenRows avec stockage JSON sur GitHub.

PRINCIPE
--------
- Un fichier JSON (ex: "zenrows_quota.json") vit dans un repo GitHub.
- Il contient, pour chaque clé, le quota restant et sa date de reset mensuelle.
- Chaque requête ZenRows coûte COST_PER_REQUEST (5 par défaut).
- Avant chaque requête : on vérifie si la date du jour == jour de reset de la clé
  (et qu'on n'a pas déjà reset ce mois-ci) -> on remet à MAX_QUOTA.
- On choisit automatiquement la première clé qui a encore assez de quota.
- Après la requête, on décrémente et on repousse le fichier sur GitHub.

NOTE : les clés ZenRows sont laissées en clair ci-dessous (KEYS_CONFIG) à la
demande explicite de l'utilisateur. Seul le token GitHub reste en variable
d'environnement, car il est indispensable pour authentifier les requêtes
vers l'API GitHub (il n'y a pas d'autre moyen de le fournir ici).

CONFIGURATION REQUISE (variable d'environnement)
---------------------------------------------------
GITHUB_TOKEN   -> token GitHub avec droit "repo" (contents: read/write)

À ADAPTER
---------
REPO       -> "ton-user/ton-repo"
FILE_PATH  -> chemin du fichier json dans le repo
BRANCH     -> branche cible
"""

import base64
import datetime
import json
import os

import requests

# ----------------------- CONFIG À ADAPTER -----------------------

REPO = "NETFLOXXX/site"
FILE_PATH = "zenrows_quota.json"
BRANCH = "main"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

COST_PER_REQUEST = 5
MAX_QUOTA = 5000

# id interne -> clé ZenRows, jour du mois de reset
KEYS_CONFIG = [
    {"id": "key1", "key": "b8f3a46268194200fe9c486a3e2d98708932765a", "reset_day": 12},
    {"id": "key2", "key": "44d5a34feacecfa26ada3b13ea4586d707d6a215", "reset_day": 13},
    {"id": "key3", "key": "7bee8a361426c7fef0459197adf108bdd4ff285a", "reset_day": 13},
]

# ------------------------------------------------------------------


def _github_headers():
    if not GITHUB_TOKEN:
        raise RuntimeError("La variable d'environnement GITHUB_TOKEN n'est pas définie.")
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def _default_content():
    today = datetime.date.today().isoformat()
    return {
        k["id"]: {
            "remaining": MAX_QUOTA,
            "reset_day": k["reset_day"],
            "last_reset": today,
        }
        for k in KEYS_CONFIG
    }


def get_file():
    """Récupère le contenu JSON actuel + son sha (nécessaire pour l'update GitHub)."""
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    r = requests.get(url, headers=_github_headers(), params={"ref": BRANCH})

    if r.status_code == 200:
        data = r.json()
        content = json.loads(base64.b64decode(data["content"]).decode("utf-8"))
        return content, data["sha"]

    if r.status_code == 404:
        # Le fichier n'existe pas encore sur le repo -> on l'initialise
        return _default_content(), None

    r.raise_for_status()


def save_file(content, sha, message):
    """Pousse le contenu JSON mis à jour sur GitHub (create ou update selon sha)."""
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    payload = {
        "message": message,
        "content": base64.b64encode(
            json.dumps(content, indent=2, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8"),
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=_github_headers(), json=payload)
    r.raise_for_status()
    return r.json()["content"]["sha"]


def check_resets(content):
    """Remet à MAX_QUOTA les clés dont le jour de reset mensuel est atteint."""
    today = datetime.date.today()
    changed = False

    for k in KEYS_CONFIG:
        entry = content.setdefault(
            k["id"],
            {"remaining": MAX_QUOTA, "reset_day": k["reset_day"], "last_reset": today.isoformat()},
        )
        last_reset = datetime.date.fromisoformat(entry["last_reset"])

        already_reset_this_month = (last_reset.year, last_reset.month) == (today.year, today.month) \
            and last_reset.day >= k["reset_day"]

        if today.day >= k["reset_day"] and not already_reset_this_month:
            entry["remaining"] = MAX_QUOTA
            entry["last_reset"] = today.isoformat()
            changed = True

    return changed


def get_available_key(content):
    """Retourne (id, clé) de la première clé qui a encore assez de quota."""
    for k in KEYS_CONFIG:
        entry = content[k["id"]]
        if entry["remaining"] >= COST_PER_REQUEST:
            return k["id"], k["key"]
    return None, None


def zenrows_request(target_url, **zenrows_params):
    """
    Fait une requête ZenRows en choisissant automatiquement une clé disponible,
    décrémente son quota de COST_PER_REQUEST, et pousse le JSON à jour sur GitHub.
    """
    content, sha = get_file()
    check_resets(content)

    key_id, api_key = get_available_key(content)
    if not api_key:
        # on sauvegarde quand même l'état (au cas où un reset vient d'avoir lieu)
        save_file(content, sha, "check quota (no key available)")
        raise RuntimeError("Aucune clé ZenRows disponible : quota épuisé sur les 3 clés.")

    params = {"url": target_url, "apikey": api_key, **zenrows_params}
    response = requests.get("https://api.zenrows.com/v1/", params=params)

    content[key_id]["remaining"] -= COST_PER_REQUEST
    save_file(content, sha, f"quota: -{COST_PER_REQUEST} sur {key_id} ({content[key_id]['remaining']} restants)")

    return response


def print_status():
    content, _ = get_file()
    check_resets(content)
    for k in KEYS_CONFIG:
        entry = content[k["id"]]
        print(f"{k['id']} (reset le {entry['reset_day']} du mois) : {entry['remaining']} / {MAX_QUOTA}")


if __name__ == "__main__":
    # Exemple d'utilisation
    print_status()
    # resp = zenrows_request("https://example.com")
    # print(resp.status_code)
