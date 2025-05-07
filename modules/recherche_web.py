import requests
from bs4 import BeautifulSoup

def recherche_web_bing(question: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://www.bing.com/search?q={question.replace(' ', '+')}"
        response = requests.get(url, headers=headers, timeout=5)
        
        soup = BeautifulSoup(response.text, "html.parser")
        resultats = soup.find_all("li", class_="b_algo")

        if resultats:
            message = "🔍 J'ai trouvé ça pour vous (Bing) :\n\n"
            for i, resultat in enumerate(resultats[:3]):
                titre = resultat.find("h2").get_text(strip=True) if resultat.find("h2") else "Titre indisponible"
                lien = resultat.find("a")["href"] if resultat.find("a") else "Lien indisponible"
                message += f"{i+1}. 📌 {titre}\n🔗 {lien}\n\n"

            return message.strip()

        return "🤷 Je n'ai pas trouvé d'information claire sur Bing."

    except Exception as e:
        return f"❌ Erreur pendant la recherche web Bing : {e}"


def recherche_web_google_news(question: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://news.google.com/search?q={question.replace(' ', '+')}&hl=fr"
        response = requests.get(url, headers=headers, timeout=5)
        
        soup = BeautifulSoup(response.text, "html.parser")
        resultats = soup.find_all("article", limit=3)

        if resultats:
            message = "📰 J'ai trouvé des actualités pour vous (Google News) :\n\n"
            for i, article in enumerate(resultats):
                titre = article.find("h3").get_text(strip=True) if article.find("h3") else "Titre indisponible"
                lien = "https://news.google.com" + article.find("a")["href"][1:] if article.find("a") else "Lien indisponible"
                message += f"{i+1}. 📌 {titre}\n🔗 {lien}\n\n"

            return message.strip()

        return "🤷 Je n'ai pas trouvé d'actualités claires sur Google News."

    except Exception as e:
        return f"❌ Erreur pendant la recherche Google News : {e}"


def recherche_web_wikipedia(question: str) -> str:
    try:
        url = f"https://fr.wikipedia.org/wiki/{question.replace(' ', '_')}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return f"🌐 J'ai trouvé un article Wikipédia pour vous :\n🔗 {url}"
        else:
            return "🤷 Je n'ai pas trouvé de page Wikipédia correspondante."

    except Exception as e:
        return f"❌ Erreur pendant la recherche sur Wikipédia : {e}"

def recherche_score_football(equipe: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 🌐 Priorité 1 : Flashscore
        url_flashscore = f"https://www.flashscore.fr/recherche/?q={equipe.replace(' ', '+')}"
        response_flash = requests.get(url_flashscore, headers=headers, timeout=5)
        if response_flash.status_code == 200:
            return f"⚽ Résultats sur Flashscore :\n🔗 {url_flashscore}"

        # 🌐 Priorité 2 : Sofascore
        url_sofascore = f"https://www.sofascore.com/fr/recherche/{equipe.replace(' ', '-')}"
        response_sofa = requests.get(url_sofascore, headers=headers, timeout=5)
        if response_sofa.status_code == 200:
            return f"⚽ Résultats sur Sofascore :\n🔗 {url_sofascore}"

        # 🌐 Priorité 3 : Recherche Google si les deux échouent
        url_google = f"https://www.google.com/search?q=score+{equipe.replace(' ', '+')}"
        response_google = requests.get(url_google, headers=headers, timeout=5)
        if response_google.status_code == 200:
            return f"⚽ Résultats sur Google :\n🔗 {url_google}"

        return "🤷 Je n'ai pas trouvé d'information sur les scores de cette équipe."

    except Exception as e:
        return f"❌ Erreur pendant la recherche des scores : {e}"

def recherche_web_universelle(question: str) -> str:
    print("✅ Recherche universelle lancée :", question)

    # 🔎 Si la question concerne les actualités
    if any(mot in question.lower() for mot in ["nouvelles", "actualités", "dernier", "dernière", "récent", "récentes"]):
        print("✅ Recherche d'actualités détectée.")
        result_google_news = recherche_web_google_news(question)
        if "🤷" not in result_google_news and "❌" not in result_google_news:
            return result_google_news

    # 🌐 Priorité 1 : Bing pour les informations générales
    result_bing = recherche_web_bing(question)
    if "🤷" not in result_bing and "❌" not in result_bing:
        return result_bing

    # 🌐 Priorité 2 : Google si Bing échoue
    result_google = recherche_web_google(question)
    if "🤷" not in result_google and "❌" not in result_google:
        return result_google

    # 🌐 Priorité 3 : Wikipédia si Bing et Google échouent
    result_wikipedia = recherche_web_wikipedia(question)
    if "🤷" not in result_wikipedia and "❌" not in result_wikipedia:
        return result_wikipedia

    # ❌ Si les trois échouent
    return "🤷 Je n'ai pas trouvé d'information claire, mais vous pouvez reformuler ou être plus spécifique."
