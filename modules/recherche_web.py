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
            message = "🔍 J'ai trouvé ça pour vous :\n\n"
            for i, resultat in enumerate(resultats[:3]):  # Limite à 3 résultats
                titre = resultat.find("h2").get_text(strip=True) if resultat.find("h2") else "Titre indisponible"
                lien = resultat.find("a")["href"] if resultat.find("a") and resultat.find("a").has_attr("href") else "Lien indisponible"
                message += f"{i+1}. 📌 {titre}\n🔗 {lien}\n\n"

            return message.strip()

        return "🤷 Je n'ai pas trouvé d'information claire, mais vous pouvez reformuler ou être plus spécifique."

    except Exception as e:
        return f"❌ Erreur pendant la recherche web Bing : {e}"


def recherche_web_google(question: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://www.google.com/search?q={question.replace(' ', '+')}"
        response = requests.get(url, headers=headers, timeout=5)
        
        soup = BeautifulSoup(response.text, "html.parser")
        resultats = soup.find_all("h3")

        if resultats:
            message = "🔍 J'ai trouvé ça pour vous :\n\n"
            for i, resultat in enumerate(resultats[:3]):  # Limite à 3 résultats
                titre = resultat.get_text(strip=True)
                message += f"{i+1}. 📌 {titre}\n"

            return message.strip()

        return "🤷 Je n'ai pas trouvé d'information claire, mais vous pouvez reformuler ou être plus spécifique."

    except Exception as e:
        return f"❌ Erreur pendant la recherche web Google : {e}"


def recherche_web_universelle(question: str) -> str:
    # 🌐 Priorité 1 : Bing
    print("✅ Recherche avec Bing en priorité.")
    result_bing = recherche_web_bing(question)
    if "🤷" not in result_bing and "❌" not in result_bing:
        return result_bing

    # 🌐 Si Bing échoue, basculer sur Google
    print("✅ Bing a échoué, tentative avec Google.")
    result_google = recherche_web_google(question)
    if "🤷" not in result_google and "❌" not in result_google:
        return result_google

    # ❌ Si les deux échouent
    return "🤷 Je n'ai pas trouvé d'information claire, mais vous pouvez reformuler ou être plus spécifique."
