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
