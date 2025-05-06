import requests
from bs4 import BeautifulSoup

def obtenir_resultat_match_web(equipe: str) -> str:
    try:
        requete = f"{equipe} score"
        url = f"https://duckduckgo.com/html/?q={requete}"
        headers = {"User-Agent": "Mozilla/5.0"}

        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")

        # Recherche d'un extrait pertinent (résultat rapide affiché en haut)
        liens = soup.find_all("a", class_="result__a", limit=5)
        for lien in liens:
            texte = lien.get_text().lower()
            if " - " in texte and equipe.lower() in texte:
                return f"Résultat trouvé : {texte.strip()}"

        return "Je n’ai pas trouvé de résultat récent pour cette équipe."
    except Exception as e:
        return "Erreur lors de la récupération des résultats de match."
