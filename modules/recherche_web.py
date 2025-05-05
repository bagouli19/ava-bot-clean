import requests
from .recherche_wikipedia import recherche_wikipedia  # si les modules sont séparés

def recherche_web_duckduckgo(question: str) -> str:
    params = {
        "q": question,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1
    }

    try:
        response = requests.get("https://api.duckduckgo.com/", params=params)
        data = response.json()
        abstract = data.get("AbstractText", "").strip()
        url = data.get("AbstractURL", "").strip()

        # 🔍 Si pas de vraie réponse → Wikipédia
        if not abstract or len(abstract) < 30:
            return recherche_wikipedia(question)

        return f"🌐 Résultat web : {abstract}\n\n🔗 [En savoir plus]({url})" if url else f"🌐 Résultat web : {abstract}"

    except Exception as e:
        return f"❌ Erreur pendant la recherche DuckDuckGo : {e}"
