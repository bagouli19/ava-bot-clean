import requests
from bs4 import BeautifulSoup

def obtenir_score_bing(equipe: str) -> str:
    try:
        query = f"{equipe} score"
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # Recherche du score dans les résumés de Bing
        cards = soup.find_all("li", class_="b_algo")

        for card in cards:
            texte = card.get_text()
            if " - " in texte and any(char.isdigit() for char in texte):
                lignes = texte.split("\n")
                for ligne in lignes:
                    if " - " in ligne and any(char.isdigit() for char in ligne):
                        return f"📊 Résultat trouvé (Bing) : {ligne.strip()}"

        return f"❌ Aucun score détecté pour {equipe.capitalize()} sur Bing."
    except Exception as e:
        return f"❌ Erreur (bing_scraper) : {e}"

