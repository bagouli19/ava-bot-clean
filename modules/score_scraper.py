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

        score_blocks = soup.find_all("div", class_="BNeawe tAd8D AP7Wnd")

        for block in score_blocks:
            texte = block.get_text()
            if " - " in texte and any(char.isdigit() for char in texte):
                return f"📊 Résultat trouvé : {texte.strip()}"

        titles = soup.find_all("div", class_="BNeawe s3v9rd AP7Wnd")
        for title in titles:
            texte = title.get_text()
            if " - " in texte and any(char.isdigit() for char in texte):
                return f"📊 Résultat (titre) : {texte.strip()}"

        return f"❌ Aucun score récent trouvé pour {equipe.capitalize()}."
    except Exception as e:
        return f"❌ Erreur (score_scraper) : {e}"
