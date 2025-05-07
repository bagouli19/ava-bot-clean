import requests

def recherche_google(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_SEARCH_ENGINE_ID,
        "q": query,
        "num": 5  # Nombre de résultats que tu souhaites afficher
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "items" in data:
            results = data["items"]
            response_text = ""
            for result in results:
                title = result.get("title", "Titre indisponible")
                link = result.get("link", "Lien indisponible")
                response_text += f"🔎 {title}\n➡️ {link}\n\n"
            return response_text.strip()
        else:
            return "Désolé, je n'ai pas trouvé de résultats pertinents sur Google."
    except Exception as e:
        return f"Erreur lors de la recherche Google : {str(e)}"
