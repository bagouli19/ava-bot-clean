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

        # Recherche dans les titres de liens de résultats classiques
        result_links = soup.find_all("h3")
        for link in result_links:
            texte = link.get_text()
            if " - " in texte and any(char.isdigit() for char in texte):
                return f"📊 Dernier score détecté : {texte.strip()}"

        return f"❌ Aucun score détecté pour {equipe.capitalize()} sur Google."
    except Exception as e:
        return f"❌ Erreur (score_scraper) : {e}"
