import requests

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

        return "🤷 Je n'ai pas trouvé d'information claire, reformulez si besoin."

    except Exception as e:
        return f"❌ Erreur DuckDuckGo : {e}"




