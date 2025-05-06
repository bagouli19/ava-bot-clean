import requests
from modules.wikipedia_fallback import recherche_wikipedia  # Si tu utilises un fallback, sinon retire cette ligne

def recherche_web_duckduckgo(question: str) -> str:
    try:
        params = {
            "q": question,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        response = requests.get("https://api.duckduckgo.com/", params=params)
        data = response.json()

        abstract = data.get("AbstractText", "").strip()
        url = data.get("AbstractURL", "").strip()

        if abstract and len(abstract) > 30:
            return f"🔍 J’ai trouvé ça pour vous :\n\n{abstract}\n\n🔗 {url}" if url else f"🔍 J’ai trouvé ça pour vous :\n\n{abstract}"

        # Si trop court ou vide → utiliser Wikipédia si dispo
        return recherche_wikipedia(question)

    except Exception as e:
        return f"❌ Erreur pendant la recherche DuckDuckGo : {e}"



