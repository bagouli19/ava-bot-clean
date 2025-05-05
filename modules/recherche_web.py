import requests
import wikipedia

wikipedia.set_lang("fr")

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

        # 🔁 Si réponse vide ou trop courte → Fallback Wikipédia
        if not abstract or len(abstract) < 30:
            resultats = wikipedia.search(question)
            if resultats:
                try:
                    page = wikipedia.page(resultats[0])
                    resume = wikipedia.summary(page.title, sentences=2)
                    return f"📚 Résumé Wikipédia : {resume}\n\n🔗 [Lire plus sur Wikipédia]({page.url})"
                except Exception as e:
                    return f"❌ Erreur Wikipédia : {e}"
            else:
                return "❌ Je n’ai trouvé aucune information pertinente sur ce sujet."

        return f"🌐 Résultat DuckDuckGo : {abstract}\n\n🔗 {url}" if url else f"🌐 Résultat DuckDuckGo : {abstract}"

    except Exception as e:
        return f"❌ Erreur pendant la recherche web : {e}"
