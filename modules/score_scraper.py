import requests
from bs4 import BeautifulSoup
import re

def obtenir_score_bing(equipe: str) -> str:
    try:
        query = f"{equipe} score"
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # Recherche dans les résumés visibles
        cards = soup.find_all("li", class_="b_algo")
        for card in cards:
            texte = card.get_text(separator="\n")
            lignes = texte.split("\n")
            for ligne in lignes:
                if re.search(r"\b\d{1,2}\s*-\s*\d{1,2}\b", ligne):
                    return f"📊 Score détecté : {ligne.strip()}"

        return f"❌ Aucun score lisible détecté pour {equipe.capitalize()}."
    except Exception as e:
        return f"❌ Erreur (bing_scraper) : {e}"


