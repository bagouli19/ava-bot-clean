import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_TOKEN = os.getenv("FOOTBALL_API_TOKEN")

HEADERS = {
    "X-Auth-Token": API_FOOTBALL_TOKEN
}

# Exemple : PSG = 524 ; compétition Ligue 1 = FL1
def obtenir_score_api(nom_equipe="Paris SG", competition="FL1") -> str:
    try:
        url = f"https://api.football-data.org/v4/competitions/{competition}/matches?status=FINISHED&limit=5"
        response = requests.get(url, headers=HEADERS, timeout=5)
        data = response.json()

        for match in reversed(data.get("matches", [])):  # du plus ancien au plus récent
            equipe_home = match["homeTeam"]["name"]
            equipe_away = match["awayTeam"]["name"]
            score_home = match["score"]["fullTime"]["home"]
            score_away = match["score"]["fullTime"]["away"]
            date = match["utcDate"][:10]

            if nom_equipe.lower() in equipe_home.lower() or nom_equipe.lower() in equipe_away.lower():
                return f"📆 {date} — ⚽ {equipe_home} {score_home} - {score_away} {equipe_away}"

        return f"❌ Aucun match récent trouvé pour {nom_equipe} dans {competition}."
    except Exception as e:
        return f"❌ Erreur Football API : {e}"



