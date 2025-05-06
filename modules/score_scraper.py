import requests
from bs4 import BeautifulSoup

def obtenir_score_google(equipe: str) -> str:
    try:
        query = f"{equipe} score"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # Recherche dans les blocs d'infos Google
        score_bloc = soup.find_all("div", class_="BNeawe deIvCb AP7Wnd")
        if score_bloc:
            for bloc in score_bloc:
                texte = bloc.get_text()
                if " - " in texte and any(c.isdigit() for c in texte):
                    return f"📊 Dernier résultat trouvé : {texte.strip()}"

        return "Je n’ai pas trouvé de score récent pour cette équipe sur Google."
    except Exception as e:
        return "❌ Erreur lors de la récupération du score depuis Google."
