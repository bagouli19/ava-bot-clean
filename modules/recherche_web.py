import requests
import wikipedia

wikipedia.set_lang("fr")

def recherche_wikipedia(question: str) -> str:
    try:
        resultats = wikipedia.search(question)
        if not resultats:
            return "🔍 Wikipédia n’a trouvé aucun résultat pertinent."
        page = wikipedia.page(resultats[0])
        resume = wikipedia.summary(page.title, sentences=2)
        return f"📚 Résumé Wikipédia : {resume}\n\n🔗 [Lire plus sur Wikipédia]({page.url})"
    except Exception as e:
        return f"❌ Erreur Wikipédia : {e}"

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

        # Si la réponse est vide ou trop courte, on bascule vers Wikipédia
        if not abstract or len(abstract) < 30:
            return recherche_wikipedia(question)

        return f"🔎 Résultat web : {abstract}\n\n🔗 [Source]({url})" if url else f"🔎 Résultat web : {abstract}"
    except Exception as e:
        return f"❌ Erreur pendant la recherche web : {e}"

