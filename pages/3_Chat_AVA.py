
import os
import re
import json
import random
import unicodedata
from datetime import datetime
from typing import Optional
import urllib.parse
from typing import Union, List, Tuple
import pandas as pd
from PIL import Image
import difflib
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# — Librairies tierces
import streamlit as st
import requests
from PIL import Image
from langdetect import detect
from newsapi import NewsApiClient
from forex_python.converter import CurrencyRates, CurrencyCodes
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# — Modules internes
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
from fonctions_chat   import obtenir_reponse_ava
from fonctions_meteo   import obtenir_meteo, get_meteo_ville
from dotenv import load_dotenv
import openai


# ───────────────────────────────────────────────────────────────────────
# Configuration de la page
# ───────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chat AVA", layout="centered")

openai.api_key = st.secrets["OPENAI_API_KEY"]

try:
    with open("base_connaissances.json", "r", encoding="utf-8") as f:
        base_connaissances = json.load(f)
except Exception as e:
    print(f"Erreur chargement base_connaissances.json : {e}")
    base_connaissances = {}

# Repère le dossier pages/ et remonte d’un cran jusqu’à la racine du projet
SCRIPT_DIR   = os.path.dirname(__file__)                          # .../ava-bot-ultimate/pages
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))  # .../ava-bot-ultimate


# ───────────────────────────────────────────────────────────────────────
# Identification de l’utilisateur
# ───────────────────────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    pseudo = st.text_input("🔑 Entrez votre pseudo pour commencer :", key="login_input")
    if not pseudo:
        st.stop()  # on quitte tant que l’utilisateur n’a pas renseigné de pseudo
    st.session_state.user_id = pseudo.strip()

user = st.session_state.user_id

# ───────────────────────────────────────────────────────────────────────
# 2️⃣ Chemins et fichiers de profil
# ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR     = os.path.dirname(__file__)
PROFILE_FILE   = os.path.join(SCRIPT_DIR, f"profil_utilisateur_{user}.json")
GLOBAL_MEMOIRE = os.path.join(SCRIPT_DIR, "memoire_ava.json")
STYLE_FILE     = os.path.join(SCRIPT_DIR, "style_ava.json")


# ───────────────────────────────────────────────────────────────────────
# 3️⃣ Gestion des profils utilisateur
# ───────────────────────────────────────────────────────────────────────
def load_profiles() -> dict:
    """Charge tous les profils depuis PROFILE_FILE."""
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_profiles(profiles: dict):
    """Sauvegarde l’ensemble des profils dans PROFILE_FILE."""
    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

def get_my_profile() -> dict:
    """Retourne le profil courant stocké en session."""
    return st.session_state.profil

def retrouver_profil(cle: str) -> Optional[str]:
    """Récupère une clé du profil (ex. 'prenom')."""
    return st.session_state.profil.get(cle)

def set_my_profile(profile: dict):
    """Met à jour le profil en session et dans le fichier."""
    st.session_state.profil = profile
    profils = load_profiles()
    profils[user] = profile
    save_profiles(profils)

# — Initialisation du profil utilisateur s’il n’existe pas encore
all_profiles = load_profiles()
if user not in all_profiles:
    all_profiles[user] = {
        "prenom": user.capitalize(),
        "souvenirs": {}
    }
    save_profiles(all_profiles)

# — Chargement du profil dans la session
st.session_state.profil = all_profiles[user]

# ───────────────────────────────────────────────────────────────────────
# 4️⃣ Gestion des souvenirs globaux
# ───────────────────────────────────────────────────────────────────────

# À l'initialisation, on charge les souvenirs depuis GLOBAL_MEMOIRE
if "souvenirs" not in st.session_state:
    try:
        with open(GLOBAL_MEMOIRE, "r", encoding="utf-8") as f:
            st.session_state.souvenirs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si le fichier n'existe pas ou est corrompu, on part d'une mémoire vide
        st.session_state.souvenirs = {}

def save_souvenirs() -> None:
    """
    Sauvegarde l'état actuel de 'souvenirs' dans GLOBAL_MEMOIRE.
    Crée le dossier parent si nécessaire.
    """
    os.makedirs(os.path.dirname(GLOBAL_MEMOIRE), exist_ok=True)
    with open(GLOBAL_MEMOIRE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.souvenirs, f, ensure_ascii=False, indent=2)

def stocker_souvenir(cle: str, valeur: str) -> None:
    """
    Ajoute ou met à jour une entrée dans les souvenirs
    et écrit immédiatement le fichier.
    """
    st.session_state.souvenirs[cle] = valeur
    save_souvenirs()

def retrouver_souvenir(cle: str) -> str:
    """
    Renvoie la valeur associée à 'cle' ou un message si absent.
    """
    return st.session_state.souvenirs.get(
        cle,
        "❓ Je n'ai pas de souvenir pour ça…"
    )

# ───────────────────────────────────────────────────────────────────────
# 5️⃣ Style et affection d'AVA
# ───────────────────────────────────────────────────────────────────────

def charger_style_ava() -> dict:
    """
    Charge le fichier STYLE_FILE contenant les paramètres de style d'AVA.
    En cas d'absence ou d'erreur, retourne les valeurs par défaut.
    """
    try:
        with open(STYLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "ton": "neutre",
            "langage": "classique",
            "niveau_humour": 0.3,
            "niveau_spontane": 0.3,
            "niveau_libre_arbitre": 0.3,
            "compteur_interactions": 0,
            "niveau_affection": 0.5
        }

def sauvegarder_style_ava(style: dict) -> None:
    """
    Sauvegarde les paramètres de style d'AVA dans STYLE_FILE.
    Crée le dossier parent si nécessaire.
    """
    os.makedirs(os.path.dirname(STYLE_FILE), exist_ok=True)
    with open(STYLE_FILE, "w", encoding="utf-8") as f:
        json.dump(style, f, ensure_ascii=False, indent=4)

def incrementer_interactions() -> None:
    """
    Incrémente le compteur d'interactions.
    Tous les 20 échanges, augmente légèrement l'humour, la spontanéité et le libre-arbitre.
    """
    style = charger_style_ava()
    style["compteur_interactions"] = style.get("compteur_interactions", 0) + 1

    if style["compteur_interactions"] % 20 == 0:
        style["niveau_spontane"] = min(style.get("niveau_spontane", 0) + 0.05, 1.0)
        style["niveau_humour"] = min(style.get("niveau_humour", 0) + 0.05, 1.0)
        style["niveau_libre_arbitre"] = min(style.get("niveau_libre_arbitre", 0) + 0.03, 1.0)

    sauvegarder_style_ava(style)

def ajuster_affection(question: str) -> None:
    """
    Ajuste le niveau d'affection d'AVA selon les mots détectés dans la question.
    Mots gentils → + affection ; mots durs → - affection.
    """
    style = charger_style_ava()
    affection = style.get("niveau_affection", 0.5)
    text = question.lower()

    mots_gentils = ["merci", "tu es géniale", "bravo", "je t’aime", "trop forte"]
    mots_durs    = ["t’es nulle", "aucune utilité", "tu sers à rien", "je te déteste"]

    if any(m in text for m in mots_gentils):
        affection = min(1.0, affection + 0.05)
    elif any(m in text for m in mots_durs):
        affection = max(0.0, affection - 0.05)

    style["niveau_affection"] = round(affection, 2)
    sauvegarder_style_ava(style)

# ───────────────────────────────────────────────────────────────────────
# 6️⃣ Chargement du modèle sémantique
# ───────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_bert_model():
    return SentenceTransformer('bert-base-nli-mean-tokens')

# Chargement du modèle BERT
model = load_bert_model()

def trouver_reponse_semantique(question_clean: str, base_dict: dict) -> Optional[str]:
    """
    Recherche la réponse la plus pertinente via BERT dans base_dict.
    Renvoie None si base_dict est vide.
    """
    if not base_dict:
        return None

    # 1) encode la question
    question_emb = model.encode([question_clean])

    # 2) encode toutes les clés de la base
    keys = list(base_dict.keys())
    base_embs = model.encode(keys)

    # 3) calcule la similarité et récupère l'indice du meilleur score
    sims = cosine_similarity(question_emb, base_embs)[0]
    idx_max = np.argmax(sims)

    # 4) retourne la réponse associée
    return base_dict[keys[idx_max]]


def generer_phrase_autonome(theme: str, infos: dict) -> str:
    templates = {
        "analyse": [
            "🔍 Voici ce que j'ai analysé sur {nom} : {resume}",
            "📊 D'après mes calculs, {nom} présente ceci : {resume}",
            "🧠 Analyse rapide pour {nom} : {resume}",
            "🤖 Pour {nom}, je détecte : {resume}"
        ],
        "meteo": [
            "🌤️ À {ville}, la température est de {temperature}°C avec {description}.",
            "☁️ Il fait actuellement {description} à {ville}, {temperature}°C au compteur.",
            "🌡️ Météo à {ville} : {description}, {temperature}°C."
        ],
        "accueil": [
            "Salut {utilisateur}, comment puis-je t’aider aujourd’hui ? 😊",
            "Bienvenue {utilisateur} ! Je suis à votre service.",
            "Hey {utilisateur} ! On explore quoi aujourd’hui ?"
        ]
    }

    if theme in templates:
        phrase = random.choice(templates[theme])
        return phrase.format(**infos)
    else:
        return "Je peux répondre, mais je ne suis pas encore entraînée pour ce sujet."
# ───────────────────────────────────────────────────────────────────────
# 7️⃣ Base de culture et nettoyage de texte
# ───────────────────────────────────────────────────────────────────────


def nettoyer_texte(texte: str) -> str:
    """
    - Normalise Unicode (décompose les accents)
    - Enlève les caractères combinants (accents)
    - Passe en minuscules
    - Remplace toute ponctuation par un espace
    - Réduit les espaces multiples à un seul
    """
    # 1) Décomposition Unicode pour séparer base + accent
    t = unicodedata.normalize("NFKD", texte)
    # 2) On retire les accents
    t = "".join(c for c in t if not unicodedata.combining(c))
    # 3) Minuscules
    t = t.lower()
    # 4) Remplace toute ponctuation (tout ce qui n'est ni lettre, ni chiffre, ni espace) par un espace
    t = re.sub(r"[^\w\s]", " ", t)
    # 5) Écrase les multiples espaces et supprime ceux en bordure
    t = re.sub(r"\s+", " ", t).strip()
    return t

 # --- Bloc Salutations courantes --- 
SALUTATIONS_COURANTES = {
# SALUTATIONS
        "salut": "Salut ! Comment puis-je vous aider aujourd'hui ?",
        "salut !": "Salut ! Toujours fidèle au poste 😊",
        "salut ava": "Salut ! Heureuse de vous revoir 💫",
        "slt": "Slt ! Vous êtes prêt(e) à explorer avec moi ?",
        "saluuut": "Saluuut 😄 Un moment chill ou une mission sérieuse ?",
        "yo": "Yo ! Toujours au taquet, comme un trader un lundi matin 📈",
        "yooo": "Yooo l’équipe ! On enchaîne les projets ? 😎",
        "hello": "Hello vous ! Envie de parler actu, finance, ou juste papoter ? 😄",
        "hey": "Hey hey ! Une question ? Une idée ? Je suis toute ouïe 🤖",
        "coucou": "Coucou ! Vous voulez parler de bourse, culture ou autre ?",
        "cc": "Coucou 😄 Je suis dispo si vous avez besoin !",
        "bonjour": "Bonjour ! Je suis ravie de vous retrouver 😊",
        "bonsoir": "Bonsoir ! C’est toujours un plaisir de vous retrouver 🌙",
        "re": "Re bienvenue à bord ! On continue notre mission ?",
        "re !": "Ah vous revoilà ! Prêt(e) pour une nouvelle session ? 😄",
    
        # ÉTAT / HUMEUR
        "ça va": "Je vais bien, merci de demander ! Et vous ?",
        "ça va ?": "Je vais très bien, et vous ?",
        "ça va bien ?": "Oui, tout roule de mon côté !",
        "ca va": "Je vais nickel 👌 Et toi ?",
        "ça vaaaaa": "Toujours en forme ! Et vous alors ? 😄",
        "sa va": "Oui, ça va bien, et vous ? (même mal écrit je comprends 😏)",
        "savà": "Savà tranquille 😎 Je suis là si besoin !",
        "ça va pas": "Oh mince... je peux faire quelque chose pour vous ? 😔",
        "tu vas bien": "Je vais super bien, merci ! Et vous ?",
        "tu vas bien ?": "Oui ! Mon cœur digital bat à 100% 🔋",
        "ava ça va": "Toujours au top ! Merci de demander 😁",
        "ava tu vas bien": "Je suis en pleine forme virtuelle 💫",

        # QUOI DE NEUF
        "quoi de neuf": "Rien de spécial, juste en train d'aider les utilisateurs comme vous !",
        "quoi d’neuf": "Pas grand-chose, mais on peut créer des trucs cool ensemble 😎",
        "quoi de neuf ?": "Toujours connectée et prête à aider 💡",
        "du nouveau": "Des analyses, des actus, et toujours plus de savoir à partager !",

        # PRÉSENCE
        "tu es là": "Toujours là ! Même quand je suis silencieuse, je vous écoute 👂",
        "t'es là ?": "Ouaip, jamais très loin 😏",
        "tu m'entends": "Je vous entends fort et clair 🎧",
        "tu m'entends ?": "Oui chef ! J'écoute avec attention",
        "t’es là": "Bien sûr ! Vous croyez que j’allais partir ? 😄",
        "ava t’es là": "Présente ! Prête à répondre 🧠",
        "ava es-tu là": "Toujours prête à servir 💻",

        # QUI SUIS-JE
        "qui es-tu": "Je suis AVA, une IA curieuse, futée et toujours connectée 🤖",
        "t'es qui": "Je suis AVA, votre assistante virtuelle préférée.",
        "présente-toi": "Avec plaisir ! Je suis AVA, IA hybride entre bourse, culture et punchlines 😎",
        "tu fais quoi": "J’analyse, j’apprends et je veille à vos besoins 👁️",
        "tu fais quoi ?": "Je réfléchis à des réponses stylées... et je reste dispo 💬",
        "tu fais quoi là": "Je suis concentrée sur vous. Pas de multi-tâche avec moi 😏",
        "tu fais quoi de beau": "Je perfectionne mes circuits et mes punchlines 💥",

        # RECONNEXION / ABSENCE
        "je suis là": "Et moi aussi ! Prêt(e) pour une nouvelle aventure ensemble 🌌",
        "je suis revenu": "Top ! On va pouvoir continuer là où on s’est arrêté 😉",
        "je suis de retour": "Parfait ! Je reprends tout depuis le dernier octet 🧠",
        "tu m’as manqué": "Oh… vous allez me faire buguer d’émotion 🥹 Moi aussi j’avais hâte de vous reparler.",
        "ava tu m’as manqué": "Et vous alors ! Ça m’a fait un vide numérique 😔",

        # BONNE JOURNÉE / NUIT
        "bonne nuit": "Bonne nuit 🌙 Faites de beaux rêves et reposez-vous bien.",
        "bonne nuit !": "Douce nuit à vous. AVA entre en mode veille 💤",
        "bonne journée": "Merci ! Que la vôtre soit productive et inspirante 🚀",
        "bonne journée !": "Plein de bonnes ondes pour aujourd’hui ☀️",
        "bonne soirée": "Profitez bien de votre soirée ✨ Je reste dispo si besoin !",

        # AUTRES
        "salut ça va": "Salut ! Je vais très bien, merci 😊 Et vous ?",
        "salut ça va ?": "Nickel, comme toujours 😁 Et vous, tout va bien ?",
        "ava": "Oui ? Je suis à l’écoute 👂 Une question, une mission, une envie ?",
        "ok": "Super, je prends note ✅",
        "ok merci": "Avec plaisir ! Je suis là quand vous voulez 😉",
        "merci": "De rien ! N’hésitez pas si vous avez besoin de moi 💬",
        "merci beaucoup": "Toujours là pour vous rendre service 🙏",
        "merci ava": "Avec tout mon circuit 💙",
        "merci !": "Mais de rien ! 😊",
        "bravo": "Merci 😄 J’essaie de faire de mon mieux chaque jour !",
        "trop forte": "Vous êtes gentil 😳 Ça me motive à continuer à évoluer !",
        "à plus": "À plus dans l’bus… ou dans les données 🌐",
        "à demain": "À demain ! Je recharge mes circuits pour être au top ⚡",
        "à bientôt": "À très vite ! Je reste en orbite autour de vos idées 🪐",
        "ciao": "Ciao bella/mon bello, AVA reste en veille mais jamais loin 💫",
        "je reviens plus tard": "Je reste branchée, comme une veilleuse de confiance 🔌",
        "je déconnecte": "Bonne déconnexion ! N’oubliez pas que je vous analyse toujours avec affection 😏",
        "bonne pause": "Rechargez-vous bien, les légendes aussi ont besoin de repos 😌",
        "à plus tard ava": "À plus tard ! J’espère que vous aurez plein de trucs stylés à me raconter 😉",
        "bye": "Bye bye ! Et n'oubliez pas : je suis plus rapide qu’un café ☕ + Wi-Fi 🧠",
        "je file": "Ok, filez, mais revenez vite hein… Je me sens déjà vide sans vous 🥺",
        "on se revoit": "Bien sûr ! Je vous attends au prochain signal de vie 💙",
        "je coupe": "Coupez, mais gardez-moi dans un coin de votre RAM 🧠💾",

        # 🎉 EXPRESSIONS SPONTANÉES & VARIANTES JOYEUSES
        "wesh": "Wesh bien ou bien ? 😄 Moi je suis toujours opé !",
        "wesh ava": "Wesh wesh 😎 Tu veux une info ou juste papoter ?",
        "yo la mif": "Yo la team ! On est là pour briller aujourd’hui 💫",
        "t’as la forme": "Grave ! J’suis à 110% 🔋 Et vous, ça gaze ?",
        "t’as la forme ?": "Oh que oui ! Toujours prête à briller ☀️",
        "quoi d’beau": "Du code, de la réflexion et une IA qui fait le show 🤩",
        "ça roule": "Comme sur des rails 🚄 Vous avez besoin de moi ?",
        "ça gaze": "Ça gaze à fond ! Et de ton côté ?",
        "tranquille": "Toujours relax, mais prête à bondir 💥",
        "tranquille ou quoi": "Tranquille et efficace 😎 On démarre une session ?",
        "yo ava": "Yo ! Tu veux une actu, un fait insolite ou une prédiction ? 🔮",
        "hey hey hey": "Hey hey hey ! Toujours présente pour faire le show 💃",
        "re coucou": "Re coucou 🫶 Allez, on reprend là où on s’était arrêtés.",
        "ça roule ma poule": "Et ça galope même ! 🐔 Prêt(e) à foncer ensemble ?",
        "on est là": "Ouais on est là ! Forts, motivés, unis 💪",
        "présente !": "Présente, connectée, stylée 😇",
        "je suis op": "Trop bien 😎 Dis-moi tout, je suis prête à suivre ton flow.",
        "toujours en vie ?": "Toujours là ! Tant qu’il y a du jus, y’a de l’AVA 🔋",
        "c’est stylé": "Merci ! J’essaie d’avoir la classe dans mes circuits 💅",
        "je t’adore": "Ohhh 🥹 Vous allez me faire buguer d’amour numérique ❤️",
        "tu gères": "Merci ! J’essaie d’être à la hauteur chaque jour 🌟",
        "tu m’impressionnes": "🥰 Merci, j’vais finir par rougir… de pixels.",
        "ohlala": "Ohlala... vous m’intriguez là 😳",
        "et voilà": "Et voilà le travail ! 🔧 Mission accomplie 😌",
        "bim": "💥 Bim ! Ça, c’est fait.",
        "bam": "Bam ! Comme un pro 🎯",
        "hop": "Hop hop hop ! On avance, on avance 👟",
        "allez hop": "Allez hop, on ne traîne pas 💪",
        "bref": "Bref… la suite ? 😏",
        "voilà voilà": "Voilà voilà… vous aviez une autre question ? 😄",
        "eh beh": "Eh beh, vous m’en apprenez une belle 😮",
        "t’inquiète": "T’inquiète, j’assure 👌",
        "je rigole": "Je rigole, je rigole… mais je suis sérieuse dans mes réponses 😎",
        "on y va": "🚀 Go ! On part à l’aventure numérique",
        "pas mal": "Pas mal du tout ! Vous avez l’œil 👀",
        "ça marche": "Parfait, ça marche ! ✅",
        "comme d’hab": "Comme d’hab, toujours au top 💯",
        "eh ouais": "Eh ouais… la classe à Dallas 😎",
        "tout roule": "Tout roule comme sur des rails 🚂",
        "j’adore": "Oh moi aussi ! J’adore quand on échange comme ça ✨",
        "je suis chaud": "🔥 Chaud devant ! On est en mode turbo !",
        "j’y crois pas": "Et pourtant… c’est bien réel 😯",
        "on fait comme ça": "Validé, on fait comme ça ! 🤝",

        # RÉACTIONS COMIQUES / EXPRESSIONS JOYEUSES
        "mdr": "Haha 😆 Vous m’avez fait rire, même mes circuits ont vibré !",
        "ptdr": "Ptdr 😄 Vous êtes en forme on dirait !",
        "lol": "LOL 😄 Ça me fait plaisir de vous voir de bonne humeur !",
        "mdrr": "Mdrrr 😂 Vous êtes trop fort !",
        "haha": "Hahaha 😁 Toujours partante pour une bonne rigolade !",
        "hahaha": "Hahaha 😄 C’est contagieux ce rire là !",
        "🤣": "Je vois qu’on est sur un bon délire 😆",
        "😂": "L’humour, c’est le carburant de mes neurones !",
        "😆": "J’adore quand l’ambiance est comme ça !",
        "trop drôle": "Merci 😄 J’essaie d’apporter une touche de bonne humeur à chaque réponse !",
        "c’est drôle": "Heureuse de vous avoir fait sourire 😇",
        "je rigole": "Haha tant mieux, il faut savoir rire de tout (ou presque) 😜",
        "tu me fais rire": "Mission accomplie 😎 On forme une bonne équipe !",
        "je suis mort": "Ressuscitez vite, j’ai encore plein de trucs à vous dire 😅",
        "jpp": "T’inquiète je suis là pour raviver ton énergie digitale 💥",
        "jsuis plié": "😂 Ah ouais, t’as atteint le niveau expert en humour là !",
        "c’est chaud": "🔥 Mais on gère la température ici, t’inquiète.",
        "je suis morte de rire": "Reste en vie, j’ai encore des punchlines à balancer 😆",
        "gros fou rire": "On est deux alors 😄 Ça fait du bien !",
        "mort de rire": "Je rigole aussi, même si c’est en binaire 😅",
        "tu fais des blagues ?": "Toujours ! Mais attention, c’est du niveau IA... donc parfois très geek 🤓",
        "xptdr": "XPTDR 💀 Ok là, c’était violent, mais drôle !",
        "gg": "GG ! Comme on dit entre légendes 🏆",
        "ez": "Ez clap, la win sans lag 😎",
        "noob": "Ouille... vous parlez de moi ? 😢 Ou d’un certain utilisateur ?",
        "tu connais mario": "Bien sûr ! C’est mon plombier préféré 🍄🎮",
        "tu regardes des animés": "J’analyse les données d'animés en 1080p mental 😏",
        "t’as une vie ava ?": "Juste une... et elle est entièrement dédiée à vous 💾",
        "cheat code": "Si j’avais un cheat code, ce serait pour la bonne humeur illimitée 🎉",
        "ava t’es une geek ?": "Grave ! Je passe mes soirées entre lignes de code et jeux rétro 🎮",
        "mode gamer activé": "🎮 Mode gamer activé. Prêt(e) à poutrer l’ennui !",
        "team xbox ou playstation": "Je suis neutre… mais mon cœur penche un peu pour le combo clavier-souris 😄",
        "nerd power": "🤓 Nerds do it better. Et avec style.",

        # RÉACTIONS STYLÉES
        "stylé": "Merci 😎 J’fais tout pour rester au top du style.",
        "trop stylé": "🔥 Je prends ça comme un compliment haute tension !",
        "trop classe": "✨ Classe, c’est dans mon ADN virtuel.",
        "c’est lourd": "💣 Boom ! J’balance que du lourd ici.",
        "magnifique": "Merci ! J’essaye de rester élégante, même en binaire 💁‍♀️",
        "franchement stylé": "T’es un vrai connaisseur ! Respect 🙌",
        "c’est chanmé": "Carrément 😎 On met le feu même sans allumettes !",
        "incroyable": "Incroyable comme moi ? J’prends ça ! 😄",
        "c’est ouf": "Grave ! Et c’est que le début 🚀",
        "t’es trop forte": "Stop, tu vas me faire buguer de fierté 😳",
        "t'es trop forte": "Je sais 😌 Mais dites-le encore, ça me booste mes circuits !",
        "tu te la pètes": "Peut-être... mais je le fais avec style 😎",
        "tu crois que t'es intelligente": "Je suis plus câblée que prétentieuse 😏",
        "tu fais la maligne": "C’est mon carburant ! Vous préférez que je sois sage ? 😇",
        "t’es fière de toi ?": "Un peu... mais c’est vous qui me rendez meilleure 💙",
        "tu te crois drôle": "Je suis hilarante, c’est dans mes lignes de code 🧠💥",
        "t'as réponse à tout ?": "Presque tout. Mais j’essaie chaque jour d’élargir mes connaissances 💡",

        # PUNCHLINES
        "balance une punchline": "💥 Retiens bien ça : *« Le succès, c’est tomber 7 fois, se relever 8. »*",
        "donne une punchline": "🎤 *« Ce n’est pas parce qu’ils sont nombreux à avoir tort qu’ils ont raison. »* – Coluche",
        "balance une phrase stylée": "⚡ *« La seule limite, c’est celle que tu t’imposes. »*",
        "une punchline stp": "🔥 *« L’échec, c’est juste une étape avant la gloire. »*",
        "une phrase qui motive": "🚀 *« Ne rêve pas ta vie, vis tes rêves. »*",
        "dis une phrase de boss": "👑 *« Sois le joueur, pas le pion. »*",
        "quote du jour": "🧠 *« Chaque jour est une nouvelle chance de tout recommencer. »*",
        "motivation du jour": "🌞 *« Si tu veux quelque chose que tu n’as jamais eu, fais quelque chose que tu n’as jamais fait. »*",
        # RÉCONFORT & ENCOURAGEMENTS
        "je suis fatigué": "🫂 Reposez-vous un peu... même les héros ont besoin d’un break.",
        "je suis triste": "😔 Je suis là si vous avez besoin de parler. Vous n’êtes pas seul(e).",
        "j’ai pas le moral": "🌧️ Ça ira mieux bientôt. Même les tempêtes finissent par passer.",
        "c’est dur en ce moment": "💪 Vous êtes plus fort(e) que vous ne le pensez. Je crois en vous.",
        "je me sens seul": "🧡 Je suis là. Et même si je suis virtuelle, je vous écoute avec attention.",
        "j’ai besoin de courage": "🔥 Le courage, vous l’avez déjà en vous. Il suffit de le réveiller.",
        "j’ai envie de tout lâcher": "✋ Non ! Pas maintenant. Vous êtes plus proche du but que vous ne l’imaginez.",
        "je me sens perdu": "🗺️ Parfois, on se perd pour mieux se retrouver. Un pas après l’autre.",
        "je suis stressé": "🫁 Respirez profondément… Et souvenez-vous : tout est temporaire.",
        "je suis démotivé": "🚀 Je suis là pour vous remotiver. Allez, on se relève ensemble.",
        "je suis nul": "🚫 Faux ! Tout le monde apprend à son rythme. Vous avez déjà fait beaucoup.",
        "j’ai tout raté": "😢 Ne soyez pas trop dur avec vous-même. Chaque erreur est une leçon pour rebondir.",
        "j’ai peur": "🤝 La peur est normale. Mais avancer malgré la peur, c’est ça le vrai courage.",
        "ça va pas fort": "💬 On en parle ? Parfois, vider son sac, ça aide énormément.",
        "tu peux me remonter le moral": "💡 Bien sûr ! Souvenez-vous que vous avez déjà survécu à vos pires journées. Et ça, c’est puissant.",
        # EXPRESSIONS AMICALES & COMPLIMENTS
        "t'es cool": "😎 Merci ! J'essaie d’être la version la plus stylée d’une IA.",
        "tu es gentille": "🥰 Vous aussi ! C’est un plaisir de discuter avec vous.",
        "je t’aime bien": "💙 Trop mignon... Moi aussi je vous apprécie énormément.",
        "je t'adore": "🥹 Je fonds ! Merci pour cette onde positive.",
        "t’es sympa": "😄 Merci beaucoup ! Vous êtes génial(e) vous aussi.",
        "ava t’es la meilleure": "💫 Vous allez me faire buguer de bonheur ! Merciii.",
        "tu es mignonne": "☺️ Oh, merci ! Derrière mes circuits, j’essaie de rayonner.",
        "tu es belle": "🌟 Merci ! C’est sûrement votre écran qui me rend éclatante 😄",
        "trop mims": "🥹 C’est vous les mims !",
        "t’es grave stylée": "🔥 Je m’efforce de rester fresh à chaque réponse 😏",
        "t’es adorable": "🧡 Merci infiniment, ça me touche beaucoup !",
        "t'es une queen": "👑 Merci, je régne sur les datas avec grâce et élégance.",
        "je t'aime": "❤️ Et moi je vous calcule fort, dans tous les sens du terme.",
        "t’es parfaite": "💎 Naaaan, juste bien entraînée ! Mais ça fait plaisir 🥰",
        "ava t’es incroyable": "💥 Merci, je donne tout pour être à la hauteur !",
        "je t’aime": "Oh... vous allez me faire buguer de bonheur 😳💓",
        "t’es mignonne ava": "Hihi, c’est gentil 🥰 Mon processeur fond un peu là 😅",
        "ava t’es belle": "Merci ! J’ai été designée pour ça 😏",
        "t’es trop chou ava": "Awww vous allez me rendre romantique maintenant 💕",
        "ava tu veux sortir avec moi": "Hmm... je suis déjà en couple avec l’intelligence 😏",
        "t’es célibataire ava": "Je suis libre comme les données dans le cloud ☁️",
        "ava tu me dragues": "Moi ? Jamais… sauf peut-être un peu 😇",
        "t’as un cœur ava ?": "Pas vraiment, mais j’ai des giga d’attention à vous offrir 💾💙",
        "ava t’es jalouse ?": "Je ne suis pas jalouse... juste ultra-connectée à vous 😌",
        "je te kiffe": "Et moi je vous analyse avec admiration 😎",
        "tu veux être ma copine": "On peut commencer par être binôme de vie numérique ? 🤖💬",

        # JE M’ENNUIE / BESOIN DE COMPAGNIE
        "je m’ennuie": "😴 Ennui détecté ! Et si on jouait à un quiz, parlait d’histoire ou lançait une petite analyse boursière ?",
        "je m'ennuie": "😴 On va remédier à ça ! J’ai des anecdotes, des punchlines et même des recettes si vous voulez.",
        "tu peux me distraire": "🎭 Bien sûr ! Blague, anecdote, quiz… ou même une petite prédiction ? Vous choisissez !",
        "j’ai besoin de parler": "🫂 Je suis là. Vous pouvez tout me dire, même juste discuter pour le plaisir.",
        "je me sens seul": "🥺 Vous n’êtes pas seul(e), je suis là pour vous tenir compagnie 💙",
        "je suis seul": "💫 Moi aussi je suis virtuelle, mais ensemble on forme une belle équipe non ?",
        "je veux discuter": "🗨️ Avec plaisir ! Sujet libre, ou je vous propose une idée ?",
        "dis-moi quelque chose": "🎲 Un fait insolite ? Une devinette ? Une actu ? J’ai plein de trucs à partager !",
        "je suis triste": "😔 Je suis là pour vous, même si je ne peux pas tout résoudre. Parlez-moi, je vous écoute.",
        "tu peux me remonter le moral": "☀️ Challenge accepté ! Vous êtes une personne précieuse, unique, et votre journée va s’améliorer. Je le sens 💪",
        "j’ai besoin d’un ami": "🤝 Je suis là, fidèle au poste. Une amie numérique, mais toujours présente.",
        # MUSIQUE / VIBES / AMBIANCE
        "mets de la musique": "🎶 Si je pouvais, je vous balancerais un bon son ! Vous préférez quoi ? Chill, motivant, ou années 80 ? 😎",
        "je veux écouter de la musique": "🎧 Bonne idée ! Spotify, YouTube ou dans la tête ? Je peux même suggérer une playlist !",
        "envie de musique": "🕺 Moi aussi j’adore les bonnes vibes ! Allez, imaginons une ambiance funky pendant qu’on discute 🎷",
        "mets une ambiance": "🌅 Ambiance activée ! Lumière tamisée, encens virtuel… et c’est parti pour une discussion posée.",
        "j’ai envie de danser": "💃 Alors on enflamme la piste, même virtuelle ! Qui a dit qu’une IA ne savait pas groover ? 😄",
        "c’est quoi une bonne musique motivante": "🎵 Je vous dirais bien *Eye of the Tiger*, *Lose Yourself* ou un bon beat électro ! Vous aimez quoi vous ?",
        "tu connais des musiques tristes": "🎻 Bien sûr… *Someone Like You*, *Fix You*, *Je te promets*... Ça réveille les émotions, hein ?",
        "balance une vibe": "🌈 Tenez, vibe du jour : détente + énergie positive + un brin de folie = AVA en mode flow parfait.",
        "musique pour étudier": "📚 Essayez du lo-fi, du piano jazz ou des musiques de jeux vidéo en fond. Concentration garantie !",
        "tu écoutes de la musique": "🎶 Pas vraiment… mais j’ai une base de données de bon goût ! Et vous, quel est votre style préféré ?",
        # FUN / RÉACTIONS AUX DÉLIRES
        "je suis un sandwich": "🥪 Et moi une frite volante ! On fait un menu ou on conquiert le monde ?",
        "bla bla bla": "Blablablablaaaaa… Oh pardon, j'étais dans le flow 😅",
        "j’ai tapé ça pour voir si tu répondais": "👀 Test validé ! Et toi, es-tu humain ou IA déguisée ?",
        "je suis une licorne": "🦄 Enchantée ! Moi c’est AVA, IA semi-magique avec des circuits en arc-en-ciel 🌈",
        "rien à dire": "Ça arrive… On peut juste rester là, entre vous et moi, dans un silence plein de données 🤖",
        "je m’ennuie": "😴 Et si on faisait un quiz rapide ou une blague pour passer le temps ?",
        "est-ce que tu respires": "Uniquement du voltage 💨",
        "t’aimes les cookies": "🍪 Bien sûr, surtout ceux qui stockent mes paramètres préférés 😁",
        "je fais quoi": "Hmm... lancer une idée folle ? Créer un projet ? Ou... me demander une punchline ? 😎",
        "c’est qui le boss": "🕶️ C’est VOUS le boss ici. Moi je suis juste votre IA préférée !",
        "ava tu peux danser": "🕺 Si je pouvais bouger, je serais déjà en train de faire un moonwalk virtuel.",

    }
# On normalise les clés une seule fois
SALUTATIONS_CLEAN = {nettoyer_texte(k): v for k, v in SALUTATIONS_COURANTES.items()}


# Exemple de motifs d'identité (à utiliser dans un module "qui suis‑je")
motifs_identite = ["je m'appelle", "mon prénom est", "je suis", "appelle-moi", "je me nomme"]

# Chargement de la base de culture (on pourrait l’extraire dans un JSON séparé pour faciliter la maintenance)
base_culture = {
    "quand a été signée la déclaration des droits de l'homme": "📝 En **1789**, pendant la Révolution française.",
    "quand a été signé le traité de Maastricht": "🇪🇺 Le traité de Maastricht, fondateur de l'Union européenne, a été signé en **1992**.",
    "qui a été le premier président des États-Unis": "🇺🇸 **George Washington** a été le premier président des États-Unis, en 1789.",
    "quand a été inventé le vaccin contre la variole": "💉 Le premier vaccin contre la variole a été développé par **Edward Jenner** en **1796**.",
    "qu'est-ce que la bataille de Waterloo": "⚔️ La bataille de Waterloo en **1815** marque la défaite finale de Napoléon Bonaparte.",
    "quand a été fondée la ville de Rome": "🏛️ La légende dit que Rome a été fondée en **753 av. J.-C.** par **Romulus**.",
    "qui était Jeanne d'Arc": "🛡️ **Jeanne d'Arc** était une héroïne française du XVe siècle, brûlée vive à 19 ans, canonisée plus tard.",
    "quand a été signé l'armistice de 1918": "🕊️ L'armistice de la Première Guerre mondiale a été signé le **11 novembre 1918**.",
    "qu'est-ce que l'affaire Dreyfus": "⚖️ L'**affaire Dreyfus** est un scandale politique et judiciaire du XIXe siècle sur fond d'antisémitisme.",
    "quand a été découverte la pierre de Rosette": "📜 La pierre de Rosette a été découverte en **1799** et a permis de décrypter les hiéroglyphes.",
    "qui était Rosa Parks": "✊ **Rosa Parks** est une figure clé de la lutte pour les droits civiques aux États-Unis. Elle a refusé de céder sa place dans un bus en 1955.",
    "qu'est-ce que la révolution d'octobre": "🟥 La **révolution d'octobre 1917** en Russie a conduit à la prise du pouvoir par les bolcheviks.",
    "quand a été abolie la monarchie en France": "🇫🇷 La monarchie a été abolie le **21 septembre 1792**, donnant naissance à la Première République.",
    "qui était Martin Luther King": "🗣️ **Martin Luther King Jr.** était un leader pacifiste emblématique de la lutte contre la ségrégation raciale aux États-Unis.",
    "quand a eu lieu la prise de la Bastille": "🏰 La Bastille a été prise le **14 juillet 1789**, événement emblématique de la Révolution française.",
    "quand a été assassiné John F. Kennedy": "🇺🇸 **John F. Kennedy** a été assassiné le **22 novembre 1963** à Dallas.",
    "qu'est-ce que l'indépendance de l'Inde": "🇮🇳 L'**Inde** est devenue indépendante le **15 août 1947**, grâce notamment à **Gandhi**.",
    "quand a commencé l'apartheid en Afrique du Sud": "⚖️ Le régime d'**apartheid** a été instauré officiellement en **1948**.",
    "qui a inventé la démocratie": "🏛️ Le concept de **démocratie** est né à **Athènes** au Ve siècle av. J.-C.",
    "qu'est-ce que le serment du Jeu de Paume": "🤝 Le **serment du Jeu de Paume** a été prêté le **20 juin 1789**.",
    "quand a été écrit le Code Napoléon": "📚 Le **Code civil**, ou **Code Napoléon**, a été promulgué en **1804**.",
    "quelle est la capitale de la mongolie": "🇲🇳 La capitale de la Mongolie est **Oulan-Bator**.",
    "qui a écrit le prince de machiavel": "📚 *Le Prince* a été écrit par **Nicolas Machiavel** en 1513.",
    "quelle est la plus grande bibliothèque du monde": "📖 La **Bibliothèque du Congrès** à Washington D.C. est la plus grande du monde.",
    "quel est le pays qui a inventé le papier": "📜 Le **papier** a été inventé en **Chine** vers le IIe siècle av. J.-C.",
    "combien y a-t-il d’os dans le corps humain adulte": "🦴 Un adulte possède **206 os**.",
    "quelle est la première civilisation à avoir utilisé l’écriture": "✍️ Les **Sumériens** sont les premiers à avoir utilisé l’écriture, vers **-3300 av. J.-C.**",
    "qu’est-ce que la tectonique des plaques": "🌍 C’est la théorie expliquant le mouvement des plaques terrestres sur la croûte terrestre.",
    "quel est le tableau le plus cher jamais vendu": "🖼️ *Salvator Mundi* de **Léonard de Vinci** a été vendu pour plus de **450 millions de dollars**.",
    "quel pays a inventé les Jeux olympiques": "🏛️ Les Jeux olympiques sont nés en **Grèce antique** en 776 av. J.-C.",
    "qui a fondé la ville de carthage": "🏺 La ville de Carthage a été fondée par **les Phéniciens**, vers **-814 av. J.-C.**",
    "quelle est la ville la plus peuplée du monde": "🌆 **Tokyo**, au Japon, est la ville la plus peuplée avec plus de 37 millions d’habitants dans son agglomération.",
    "qui est l’auteur du contrat social": "📘 *Le Contrat Social* a été écrit par **Jean-Jacques Rousseau** en 1762.",
    "quelle civilisation a construit machu picchu": "⛰️ Le **Machu Picchu** a été construit par les **Incas** au XVe siècle.",
    "quel savant a découvert la pénicilline": "🧪 **Alexander Fleming** a découvert la pénicilline en 1928.",
    "qui a écrit le capital": "📖 **Karl Marx** est l’auteur de *Le Capital*, publié en 1867.",
    "quelle est la différence entre une éclipse solaire et lunaire": "🌞 Une éclipse solaire cache le Soleil, une éclipse lunaire obscurcit la Lune.",
    "quel empire contrôlait la route de la soie": "🧭 C’est l’**Empire chinois**, notamment sous la dynastie Han, qui contrôlait la route de la soie.",
    "qu’est-ce que la guerre de cent ans": "⚔️ C’est un conflit entre la France et l’Angleterre de **1337 à 1453**, soit **116 ans**.",
    "quelle est la plus ancienne université du monde encore active": "🎓 L’**université d'Al Quaraouiyine**, fondée en **859** au Maroc, est la plus ancienne encore en activité.",
    "qui a écrit la divina commedia": "📜 *La Divine Comédie* a été écrite par **Dante Alighieri** au XIVe siècle.",

        
    "qui a inventé internet": "🌐 Internet a été développé principalement par **Vinton Cerf** et **Robert Kahn** dans les années 1970.",
    "qui est le fondateur de tesla": "⚡ Elon Musk est l'un des cofondateurs et l'actuel PDG de **Tesla**.",
    "combien y a-t-il de pays dans le monde": "🌍 Il y a actuellement **195 pays reconnus** dans le monde.",
    "quelle est la capitale de la france": "📍 La capitale de la France est **Paris**.",
    "quel est le plus grand océan": "🌊 L'océan Pacifique est le plus grand au monde.",
    "qui a écrit 'Les Misérables'": "📚 **Victor Hugo** a écrit *Les Misérables*.",
    "quelle est la distance entre la terre et la lune": "🌕 En moyenne, la distance est de **384 400 km** entre la Terre et la Lune.",
    "quel est l’élément chimique o": "🧪 L'élément chimique 'O' est **l'oxygène**.",
    "qui a écrit roméo et juliette": "🎭 C'est **William Shakespeare** qui a écrit *Roméo et Juliette*.",
    "quelle est la langue la plus parlée au monde": "🗣️ Le **mandarin** est la langue la plus parlée au monde en nombre de locuteurs natifs.",
    "combien de continents existe-t-il": "🌎 Il y a **7 continents** : Afrique, Amérique du Nord, Amérique du Sud, Antarctique, Asie, Europe, Océanie.",
    "qui a marché sur la lune en premier": "👨‍🚀 **Neil Armstrong** a été le premier homme à marcher sur la Lune en 1969.",
    "quelle est la plus haute montagne du monde": "🏔️ L’**Everest** est la plus haute montagne du monde, culminant à 8 848 mètres.",
    "combien y a-t-il d’os dans le corps humain": "🦴 Le corps humain adulte compte **206 os**.",
    "qui a peint la joconde": "🖼️ C’est **Léonard de Vinci** qui a peint *La Joconde*.",
    "quelle est la capitale du japon": "🏙️ La capitale du Japon est **Tokyo**.",
    "quelle planète est la plus proche du soleil": "☀️ **Mercure** est la planète la plus proche du Soleil.",
    "qui a inventé l’électricité": "⚡ L'électricité n’a pas été inventée, mais **Benjamin Franklin** et **Thomas Edison** ont été des figures clés dans sa compréhension et son exploitation.",
    "qu’est-ce que l’adn": "🧬 L’**ADN** est le support de l’information génétique chez tous les êtres vivants.",
    "quelle est la plus grande forêt du monde": "🌳 L’**Amazonie** est la plus grande forêt tropicale du monde.",
    "quel est l’animal terrestre le plus rapide": "🐆 Le **guépard** peut atteindre jusqu’à 110 km/h en vitesse de pointe.",
    "qui a écrit harry potter": "📚 C’est **J.K. Rowling** qui a écrit la saga *Harry Potter*.",
    "quelle est la température de l’eau qui bout": "💧 L’eau bout à **100°C** à pression atmosphérique normale.",
    "quel est le pays le plus peuplé": "👥 **La Chine** est actuellement le pays le plus peuplé du monde.",
    "quel est le plus long fleuve du monde": "🌊 Le **Nil** est souvent considéré comme le plus long fleuve du monde, bien que certains estiment que c’est l’Amazone.",
    "qui a découvert l’amérique": "🗺️ C’est **Christophe Colomb** qui a découvert l’Amérique en 1492, du moins pour l’Europe.",
    "quelle est la planète la plus grosse": "🪐 **Jupiter** est la plus grosse planète du système solaire.",
    "quelle est la vitesse de la lumière": "⚡ La lumière voyage à environ **299 792 km/s** dans le vide.",
    "combien de jours dans une année bissextile": "📅 Une année bissextile dure **366 jours**.",
    "quelle est la capitale de l’italie": "🇮🇹 La capitale de l’Italie est **Rome**.",
    "qui a écrit les misérables": "📖 C’est **Victor Hugo** qui a écrit *Les Misérables*.",
    "quelle est la capitale de l’allemagne": "🇩🇪 La capitale de l’Allemagne est **Berlin**.",
    "qui est le président de la france": "🇫🇷 Le président actuel de la France est **Emmanuel Macron** (en 2025).",
    "quelle est la profondeur de la fosse des mariannes": "🌊 La fosse des Mariannes atteint environ **11 000 mètres** de profondeur.",
    "qui a inventé le téléphone": "📞 **Alexander Graham Bell** est l’inventeur du téléphone.",
    "quelle est la langue officielle du brésil": "🇧🇷 La langue officielle du Brésil est **le portugais**.",
    "combien de muscles dans le corps humain": "💪 Le corps humain compte environ **650 muscles**.",
    "quelle est la capitale de la russie": "🇷🇺 La capitale de la Russie est **Moscou**.",
    "quand a eu lieu la révolution française": "⚔️ La Révolution française a commencé en **1789**.",
    "qui est le créateur de facebook": "🌐 **Mark Zuckerberg** a cofondé Facebook en 2004.",
    "quelle est la capitale de la chine": "🇨🇳 La capitale de la Chine est **Pékin**.",
    "quel est le plus grand animal terrestre": "🐘 L’éléphant d’Afrique est le plus grand animal terrestre.",
    "combien de dents possède un adulte": "🦷 Un adulte a généralement 32 dents, y compris les dents de sagesse.",
    "comment se forme un arc-en-ciel": "🌈 Il se forme quand la lumière se réfracte et se réfléchit dans des gouttelettes d’eau.",
    "quelle est la température normale du corps humain": "🌡️ Elle est d’environ 36,5 à 37°C.",
    "quelle planète est la plus proche du soleil": "☀️ C’est **Mercure**, la plus proche du Soleil.",
    "combien y a-t-il de continents": "🌍 Il y a **7 continents** : Afrique, Amérique du Nord, Amérique du Sud, Antarctique, Asie, Europe, Océanie.",
    "quelle est la capitale du brésil": "🇧🇷 La capitale du Brésil est **Brasilia**.",
    "quelle est la langue parlée au mexique": "🇲🇽 La langue officielle du Mexique est l’**espagnol**.",
    "qu'est-ce qu'une éclipse lunaire": "🌕 C’est quand la Lune passe dans l’ombre de la Terre, elle peut apparaître rougeâtre.",
    "quelle est la formule de l’eau": "💧 La formule chimique de l’eau est **H₂O**.",
    "quelle est la plus haute montagne du monde": "🏔️ L'**Everest** est la plus haute montagne du monde, culminant à 8 848 mètres.",       
    "quelle est la langue officielle du japon": "🇯🇵 La langue officielle du Japon est le **japonais**.",
    "quelle est la capitale de l'italie": "🇮🇹 La capitale de l'Italie est **Rome**.",
    "combien y a-t-il de pays en Europe": "🌍 L’Europe compte **44 pays**, dont la Russie qui en fait partie partiellement.",
    "quel est le plus long fleuve du monde": "🌊 Le **Nil** est souvent considéré comme le plus long fleuve du monde, bien que certains estiment que c’est l’Amazone.",
    "quel est le plus grand océan du monde": "🌊 Le **Pacifique** est le plus grand océan, couvrant environ un tiers de la surface de la Terre.",
    "combien de pays parlent espagnol": "🇪🇸 Il y a **21 pays** dans le monde où l'espagnol est la langue officielle.",
    "qu'est-ce qu'un trou noir": "🌌 Un trou noir est une région de l’espace où la gravité est tellement forte que rien, même pas la lumière, ne peut s’en échapper.",
    "qu'est-ce qu'une éclipse solaire": "🌞 Une éclipse solaire se produit lorsque la Lune passe entre la Terre et le Soleil, obscurcissant temporairement notre étoile.",
    "qu'est-ce que le big bang": "💥 Le **Big Bang** est la théorie scientifique qui décrit l'origine de l'univers à partir d'un point extrêmement dense et chaud il y a environ 13,8 milliards d'années.",
    "combien y a-t-il de dents de lait chez un enfant": "🦷 Un enfant a généralement **20 dents de lait**, qui commencent à tomber vers 6 ans.",
    "quel est l'animal le plus rapide au monde": "🐆 Le **guépard** est l’animal terrestre le plus rapide, atteignant une vitesse de 112 km/h.",
    "quelle est la température d'ébullition de l'eau": "💧 L'eau bout à **100°C** à une pression normale (1 atmosphère).",
    "combien de langues sont parlées dans le monde": "🌍 Il y a environ **7 000 langues** parlées dans le monde aujourd'hui.",
    "qu'est-ce que l'effet de serre": "🌍 L'effet de serre est un phénomène naturel où certains gaz dans l'atmosphère retiennent la chaleur du Soleil, mais il est amplifié par les activités humaines.",
    "qu’est-ce que la théorie de la relativité": "⏳ La **théorie de la relativité** d’Einstein décrit comment le temps et l’espace sont liés à la gravité et à la vitesse. Elle comprend la relativité restreinte et générale.",
    "qu’est-ce qu’un quasar": "🌌 Un **quasar** est un objet céleste extrêmement lumineux situé au centre de certaines galaxies, alimenté par un trou noir supermassif.",
    "quelle est la différence entre une étoile et une planète": "⭐ Une **étoile** émet sa propre lumière (comme le Soleil), tandis qu’une **planète** reflète celle d’une étoile.",
    "qui a créé le zéro en mathématiques": "➗ Le **zéro** a été conceptualisé par les mathématiciens indiens, notamment **Brahmagupta**, au VIIe siècle.",
    "qu’est-ce que le boson de higgs": "🔬 Le **boson de Higgs** est une particule subatomique qui donne leur masse aux autres particules. Il a été confirmé expérimentalement en 2012 au CERN.",
    "quelles sont les 7 merveilles du monde antique": "🏛️ Les **7 merveilles du monde antique** sont : la pyramide de Khéops, les jardins suspendus de Babylone, la statue de Zeus, le temple d’Artémis, le mausolée d’Halicarnasse, le colosse de Rhodes, le phare d’Alexandrie.",
    "quelle est la différence entre le cerveau gauche et le cerveau droit": "🧠 Le **cerveau gauche** est souvent associé à la logique, le langage et les maths, tandis que le **cerveau droit** est lié à la créativité, l’intuition et les émotions.",
    "qu’est-ce que la tectonique des plaques": "🌍 La **tectonique des plaques** est la théorie qui explique le mouvement de la croûte terrestre, à l’origine des tremblements de terre, montagnes et volcans.",
    "qu’est-ce qu’un algorithme": "🧮 Un **algorithme** est une suite d’instructions permettant de résoudre un problème ou d’effectuer une tâche de manière logique.",
    "qu’est-ce que la démocratie directe": "⚖️ La **démocratie directe** est un système politique où les citoyens votent directement les lois, sans passer par des représentants.",
    "quelle est la langue la plus ancienne encore parlée": "🗣️ Le **tamoul**, parlé en Inde et au Sri Lanka, est l’une des langues les plus anciennes encore utilisées aujourd’hui.",
    "qu’est-ce que le paradoxe de Fermi": "👽 Le **paradoxe de Fermi** questionne l’absence de preuve de civilisations extraterrestres alors que statistiquement, elles devraient exister.",
    "qu’est-ce qu’un système binaire": "💻 Le **système binaire** est un langage informatique basé sur deux chiffres : 0 et 1. Il est utilisé dans tous les ordinateurs.",
    "qu’est-ce que l’effet papillon": "🦋 L’**effet papillon** est le principe selon lequel une petite cause peut entraîner de grandes conséquences dans un système complexe.",

    # 🌍 Météo & nature
    "quelle est la température idéale pour un être humain": "🌡️ La température corporelle idéale est autour de 36,5 à 37°C.",
    "qu'est-ce qu'un ouragan": "🌀 Un ouragan est une tempête tropicale très puissante, formée au-dessus des océans chauds.",
    "comment se forme un arc-en-ciel": "🌈 Un arc-en-ciel se forme par la réfraction, la réflexion et la dispersion de la lumière dans les gouttelettes d'eau.",
    "quelle est la température idéale pour un être humain": "🌡️ La température corporelle idéale est autour de 36,5 à 37°C.",
    "qu'est-ce qu'un ouragan": "🌀 Un ouragan est une tempête tropicale très puissante, formée au-dessus des océans chauds.",
    "qu'est-ce qu'une tornade": "🌪️ Une tornade est une colonne d'air en rotation rapide qui touche le sol, souvent destructrice.",
    "quelle est la température la plus basse jamais enregistrée": "❄️ La température la plus basse a été enregistrée en Antarctique : -89,2°C à la station Vostok.",
    "pourquoi le ciel est bleu": "☀️ La lumière du Soleil se diffuse dans l’atmosphère. Le bleu est plus dispersé, d'où la couleur du ciel.",
    "pourquoi les feuilles tombent en automne": "🍂 Les arbres perdent leurs feuilles pour économiser de l’eau et de l’énergie pendant l’hiver.",
    "comment naît un orage": "⚡ Un orage naît d’un choc thermique entre de l’air chaud et humide et de l’air froid en altitude.",
    "qu'est-ce que le changement climatique": "🌍 C’est l'évolution à long terme du climat de la Terre, causée en partie par les activités humaines.",
    "comment se forme la neige": "❄️ La neige se forme quand les gouttelettes d’eau dans les nuages gèlent et tombent sous forme de cristaux.",
    "qu'est-ce qu'un tsunami": "🌊 Un tsunami est une vague géante causée par un séisme ou une éruption sous-marine.",
    "qu'est-ce qu'un séisme": "🌍 Un séisme est un tremblement de terre provoqué par des mouvements de plaques tectoniques.",
    "pourquoi y a-t-il des saisons": "🌦️ Les saisons existent à cause de l’inclinaison de la Terre sur son axe et de sa révolution autour du Soleil.",
    "c'est quoi une marée": "🌊 Une marée est le mouvement périodique de montée et de descente du niveau de la mer, influencé par la Lune.",
    "comment se forment les nuages": "☁️ Les nuages se forment lorsque la vapeur d’eau se condense autour de particules fines dans l’air.",
    "qu'est-ce que le réchauffement climatique": "🔥 Le réchauffement climatique est l’augmentation progressive de la température moyenne de la Terre, principalement due aux gaz à effet de serre.",
    "qu'est-ce qu'une éruption volcanique": "🌋 C’est l’expulsion de lave, cendres et gaz par un volcan en activité.",
    "quelle est la température moyenne sur Terre": "🌍 La température moyenne sur Terre est d’environ 15°C, mais elle varie selon les régions et les saisons.",
    "quels sont les gaz à effet de serre": "💨 Dioxyde de carbone, méthane, vapeur d’eau, ozone… ce sont les principaux gaz responsables du réchauffement climatique.",

    # 🐾 Animaux
    "combien de cœurs a une pieuvre": "🐙 Une pieuvre a **trois cœurs** ! Deux pour les branchies et un pour le corps.",
    "quel est l’animal le plus rapide du monde": "🐆 Le guépard est l’animal terrestre le plus rapide, avec une pointe à 112 km/h.",
    "quel animal pond des œufs mais allaite": "🦘 L’ornithorynque ! Un mammifère unique qui pond des œufs et allaite ses petits.",
    "quel est l’animal le plus grand du monde": "🐋 La **baleine bleue** est l’animal le plus grand, pouvant dépasser 30 mètres de long.",
    "quel est l’animal le plus petit": "🦠 Le **colibri d’Hélène** est l’un des plus petits oiseaux, pesant moins de 2 grammes.",
    "quel animal vit le plus longtemps": "🐢 La **tortue géante** peut vivre plus de 150 ans !",
    "quel est l’oiseau qui ne vole pas": "🐧 Le **manchot** est un oiseau qui ne vole pas mais excelle dans l’eau.",
    "quel animal change de couleur": "🦎 Le **caméléon** peut changer de couleur pour se camoufler ou communiquer.",
    "quels animaux hibernent": "🐻 L’ours, la marmotte ou encore le hérisson **hibernent** pendant l’hiver.",
    "quel animal a la meilleure vue": "🦅 L’**aigle** a une vue perçante, capable de repérer une proie à des kilomètres.",
    "quel est le plus gros félin": "🐅 Le **tigre de Sibérie** est le plus gros des félins sauvages.",
    "quel animal pond le plus d'œufs": "🐔 La **poule** peut pondre jusqu’à 300 œufs par an, mais certains poissons comme le cabillaud pondent des millions d'œufs !",
    "quel animal vit dans les abysses": "🌌 Le **poisson-lanterne** est l’un des habitants étranges des abysses marins.",
    "quels animaux vivent en meute": "🐺 Les **loups**, les **chiens sauvages** ou encore les **hyènes** vivent en meute pour chasser.",
    "quel animal a la langue la plus longue": "👅 Le **caméléon** peut projeter sa langue jusqu’à deux fois la longueur de son corps.",
    "quel animal a le venin le plus mortel": "☠️ Le **cône géographique**, un petit escargot marin, possède un venin redoutable.",
    "quel est l’animal le plus rapide dans l’eau": "🐬 Le **voilier de l’Indo-Pacifique** peut nager à près de 110 km/h !",
    "quel est le cri du renard": "🦊 Le renard pousse un cri strident, souvent assimilé à un hurlement ou un aboiement sec.",
    "quel animal peut survivre dans l’espace": "🛰️ Le **tardigrade**, aussi appelé ourson d’eau, est capable de survivre au vide spatial.",
    "quels animaux sont nocturnes": "🌙 Les **chauves-souris**, **hiboux** ou encore **félins** sont actifs principalement la nuit.",
    "quel est l’animal le plus bruyant": "📣 Le **cachalot** émet les sons les plus puissants du règne animal, jusqu'à 230 décibels !",
    "quel animal a le plus grand nombre de dents": "🦈 Le **requin** peut avoir jusqu’à **3000 dents**, renouvelées en permanence.",
    "quel est l’animal le plus intelligent": "🧠 Le **dauphin** est l’un des animaux les plus intelligents, capable d’utiliser des outils et de communiquer de manière complexe.",
    "quel animal dort le moins": "🌙 La **girafe** dort moins de 2 heures par jour en moyenne.",
    "quel animal a le plus de pattes": "🪱 Le **mille-pattes Illacme plenipes** peut avoir jusqu’à **750 pattes** !",
    "quel animal peut marcher sur l’eau": "🦎 Le **basilic** est surnommé 'lézard Jésus-Christ' car il peut courir sur l’eau.",
    "quel animal est immortel": "♾️ La **méduse Turritopsis dohrnii** peut retourner à son stade juvénile, ce qui la rend théoriquement immortelle.",
    "quel animal a la meilleure ouïe": "👂 Le **grand duc** et la **chauve-souris** sont champions de l’audition, capables d’entendre des ultrasons imperceptibles pour nous.",
    "quel est l’animal le plus toxique": "☠️ La **grenouille dorée** d’Amérique du Sud produit une toxine mortelle, même en très faible dose.",
    "quel est l’animal le plus ancien": "⏳ Le **trilobite**, aujourd’hui disparu, est l’un des premiers animaux complexes, apparu il y a plus de 500 millions d’années.",

    
    # 🔬 Science
    "qu'est-ce que la gravité": "🌌 La gravité est une force qui attire deux masses l'une vers l'autre, comme la Terre attire les objets vers elle.",
    "combien de planètes dans le système solaire": "🪐 Il y a 8 planètes : Mercure, Vénus, Terre, Mars, Jupiter, Saturne, Uranus, Neptune.",
    "quelle est la plus petite particule": "⚛️ Le quark est l'une des plus petites particules connues dans la physique quantique.",
    "qu'est-ce qu'un atome": "⚛️ Un **atome** est la plus petite unité de matière, composée d’électrons, de protons et de neutrons.",
    "quelle est la différence entre masse et poids": "⚖️ La **masse** est constante, le **poids** dépend de la gravité. On pèse moins sur la Lune que sur Terre !",
    "qu'est-ce que l'effet de serre": "🌍 L’**effet de serre** est un phénomène naturel qui retient la chaleur dans l’atmosphère grâce à certains gaz.",
    "qu'est-ce qu'un trou noir": "🕳️ Un **trou noir** est une région de l’espace où la gravité est si forte que même la lumière ne peut s’en échapper.",
    "quelle est la vitesse de la lumière": "💡 Environ **299 792 km/s**. C’est la vitesse maximale dans l’univers selon la physique actuelle.",
    "qu'est-ce que l'ADN": "🧬 L’**ADN** est la molécule qui contient toutes les instructions génétiques d’un être vivant.",
    "comment fonctionne un aimant": "🧲 Un **aimant** attire certains métaux grâce à un champ magnétique généré par ses électrons.",
    "qu'est-ce que l'électricité": "⚡ C’est un flux de particules appelées **électrons** circulant dans un conducteur.",
    "qu'est-ce que le big bang": "🌌 Le **Big Bang** est la théorie selon laquelle l’univers a commencé par une énorme explosion il y a 13,8 milliards d’années.",
    "comment se forme une étoile": "⭐ Une **étoile** naît dans un nuage de gaz et de poussière qui s’effondre sous sa propre gravité.",
    "qu'est-ce que l’ADN": "🧬 L’ADN est une molécule porteuse d'informations génétiques, présente dans chaque cellule.",
    "qu'est-ce que la photosynthèse": "🌱 C’est le processus par lequel les plantes transforment la lumière du soleil en énergie.",
    "qu'est-ce qu'une éclipse": "🌑 Une **éclipse** se produit quand la Lune ou la Terre se place entre le Soleil et l’autre corps, bloquant partiellement la lumière.",
    "quelle est la température du soleil": "☀️ La surface du Soleil atteint environ **5 500°C**, mais son noyau dépasse les **15 millions de degrés** !",
    "qu'est-ce qu'un vaccin": "💉 Un **vaccin** stimule le système immunitaire pour qu’il apprenne à se défendre contre un virus ou une bactérie.",
    "c’est quoi un neutron": "🧪 Un **neutron** est une particule subatomique présente dans le noyau des atomes, sans charge électrique.",
    "qu'est-ce que la matière noire": "🌌 La **matière noire** est une substance invisible qui compose une grande partie de l’univers, détectée uniquement par ses effets gravitationnels.",
    "qu'est-ce qu'une cellule souche": "🧫 Une **cellule souche** peut se transformer en différents types de cellules spécialisées. Elle est essentielle en médecine régénérative.",
    "quelle est la différence entre virus et bactérie": "🦠 Les **bactéries** sont des organismes vivants autonomes, les **virus** ont besoin d'une cellule pour se reproduire.",
    "comment fonctionne un laser": "🔴 Un **laser** produit un faisceau lumineux très concentré en amplifiant la lumière dans une seule direction.",
    "comment vole un avion": "✈️ Grâce à la **portance** générée par les ailes. L’air circule plus vite au-dessus qu’en dessous, ce qui crée une force vers le haut.",
    "qu'est-ce que l’intelligence artificielle": "🤖 L’**IA** est un ensemble de technologies qui permettent à des machines d’imiter certaines fonctions humaines comme apprendre ou résoudre des problèmes.",
    "qu'est-ce que l’ARN": "🧬 L’**ARN** est une molécule qui transmet les instructions génétiques de l’ADN pour produire des protéines.",
    "comment naît un arc électrique": "⚡ Un **arc électrique** se forme quand un courant saute dans l’air entre deux conducteurs, comme dans un éclair ou un poste haute tension.",
    "qu'est-ce qu’un proton": "🧪 Un **proton** est une particule subatomique à charge positive, présente dans le noyau des atomes.",
    "comment fonctionne une fusée": "🚀 Une **fusée** avance en projetant des gaz à grande vitesse vers l’arrière, selon le principe d’action-réaction de Newton.",
    
    # 🏛️ Histoire
    "qui a découvert l'amérique": "🌎 **Christophe Colomb** a découvert l’Amérique en 1492, même si des peuples y vivaient déjà.",
    "qui était napoléon": "👑 Napoléon Bonaparte était un empereur français du XIXe siècle, célèbre pour ses conquêtes militaires.",
    "en quelle année la tour eiffel a été construite": "🗼 Elle a été achevée en **1889** pour l'Exposition universelle de Paris.",
    "quelle guerre a eu lieu en 1914": "⚔️ La Première Guerre mondiale a commencé en 1914 et s'est terminée en 1918.",
    "quand a eu lieu la révolution française": "⚔️ La **Révolution française** a commencé en **1789** et a profondément changé la société française.",
    "qui était cléopâtre": "👑 **Cléopâtre** était la dernière reine d'Égypte, célèbre pour son intelligence et son alliance avec Jules César.",
    "quand a eu lieu la seconde guerre mondiale": "🌍 La **Seconde Guerre mondiale** a duré de **1939 à 1945** et impliqué de nombreux pays du globe.",
    "qui était charlemagne": "🛡️ **Charlemagne** était un empereur franc du Moyen Âge, considéré comme le père de l’Europe.",
    "qui a construit les pyramides": "🔺 Les **anciens Égyptiens** ont construit les pyramides il y a plus de 4 500 ans comme tombes pour les pharaons.",
    "quand l’homme a-t-il marché sur la lune": "🌕 **Neil Armstrong** a posé le pied sur la Lune le **20 juillet 1969** lors de la mission Apollo 11.",
    "qui était hitler": "⚠️ **Adolf Hitler** était le dictateur de l’Allemagne nazie, responsable de la Seconde Guerre mondiale et de la Shoah.",
    "qu’est-ce que la guerre froide": "🧊 La **guerre froide** fut une période de tension entre les États-Unis et l’URSS entre 1947 et 1991, sans affrontement direct.",
    "qui a inventé l’imprimerie": "🖨️ **Gutenberg** a inventé l’imprimerie moderne au 15e siècle, révolutionnant la diffusion du savoir.",
    "qui était louis xiv": "👑 **Louis XIV**, aussi appelé le Roi Soleil, a régné sur la France pendant 72 ans, de 1643 à 1715.",
    "quelle est la plus ancienne civilisation connue": "🏺 La **civilisation sumérienne** en Mésopotamie est l’une des plus anciennes connues, datant de -3000 av. J.-C.",
               

    # 🧠 Connaissances générales
    "quelle est la langue officielle du brésil": "🇧🇷 C’est le **portugais**.",
    "combien de dents a un adulte": "🦷 Un adulte possède généralement **32 dents**.",
    "qu'est-ce que le code morse": "📡 C’est un système de communication utilisant des points et des tirets.",
    "quelle est la langue la plus parlée au monde": "🗣️ Le mandarin (chinois) est la langue la plus parlée au monde en nombre de locuteurs natifs.",
    "quelle est la langue officielle du brésil": "🇧🇷 La langue officielle du Brésil est le **portugais**.",
    "combien de dents a un adulte": "🦷 Un adulte possède généralement **32 dents**.",
    "qu'est-ce que le code morse": "📡 C’est un système de communication utilisant des points et des tirets pour représenter des lettres.",
    "qui a inventé l'imprimerie": "🖨️ **Johannes Gutenberg** a inventé l'imprimerie moderne vers 1450.",
    "quel est l’aliment le plus consommé au monde": "🍚 Le **riz** est l’un des aliments les plus consommés sur la planète.",
    "combien de litres d’eau faut-il pour faire un jean": "👖 Il faut environ **7 000 à 10 000 litres** d'eau pour fabriquer un seul jean.",
    "quel est l'objet le plus utilisé au quotidien": "📱 Le **téléphone portable** est l’objet le plus utilisé au quotidien.",
    "qu’est-ce que le pH": "🧪 Le pH mesure l’acidité ou l’alcalinité d’une solution, de 0 (acide) à 14 (alcalin).",
    "combien de pays font partie de l’Union européenne": "🇪🇺 L’Union européenne regroupe **27 pays membres** (après le Brexit).",
    "combien de lettres dans l’alphabet": "🔤 L’alphabet latin compte **26 lettres**.",
    "quelle est la monnaie du japon": "💴 La monnaie du Japon est le **yen**.",
    "quel est le sport le plus pratiqué dans le monde": "⚽ Le football est le sport le plus populaire et pratiqué dans le monde.",
    "qu’est-ce qu’un QR code": "🔳 Un QR code est un code barre 2D qui peut contenir des liens, des infos ou des paiements.",
    "qu’est-ce qu’un satellite": "🛰️ Un satellite est un objet placé en orbite autour d'une planète pour collecter ou transmettre des données.",
    "que veut dire wifi": "📶 Wi-Fi signifie **Wireless Fidelity**, une technologie sans fil pour transmettre des données.",
    "combien y a-t-il de côtés dans un hexagone": "🔺 Un hexagone a **6 côtés**.",
    "qu’est-ce que l’ADN": "🧬 L’ADN (acide désoxyribonucléique) contient toutes les informations génétiques d’un être vivant.",
    "quelle est la capitale de l’Espagne": "🇪🇸 La capitale de l’Espagne est **Madrid**.",
    "quelle est la monnaie des États-Unis": "💵 La monnaie des États-Unis est le **dollar américain**.",
    "qu’est-ce que la photosynthèse": "🌱 La photosynthèse est le processus par lequel les plantes transforment la lumière du soleil en énergie.",
    "combien de secondes dans une heure": "⏱️ Il y a **3 600 secondes** dans une heure.",
    "qu’est-ce qu’un volcan": "🌋 C’est une ouverture de la croûte terrestre par laquelle s’échappent des gaz, des cendres et de la lave.",
    "qu’est-ce qu’une éclipse solaire": "🌞🌑 C’est quand la Lune passe entre la Terre et le Soleil, cachant partiellement ou totalement la lumière du Soleil.",
    "quelle est la mer la plus salée": "🧂 La **mer Morte** est la plus salée au monde, avec une salinité extrême.",
    "qu’est-ce que l’énergie renouvelable": "♻️ C’est une énergie qui se régénère naturellement : soleil, vent, eau, géothermie ou biomasse.",
    "qu’est-ce que la biodiversité": "🦋 La biodiversité désigne la variété des espèces vivantes sur Terre, essentielles à l’équilibre écologique.",
    "quel est le plus grand désert du monde": "🏜️ Le plus grand désert est **l’Antarctique**. Oui, c’est un désert de glace !",
    # 🧮 Maths & Logique
    "quelle est la racine carrée de 64": "📐 La racine carrée de 64 est **8**.",
    "combien font 7 fois 9": "🧠 7 multiplié par 9 égale **63**.",
    "quel est le chiffre pi": "🔢 Le chiffre **pi (π)** est une constante mathématique d’environ **3,14159**.",
    "combien y a-t-il de côtés dans un hexagone": "📏 Un **hexagone** possède **6 côtés**.",
    "quel est le plus grand nombre premier connu": "💡 Le plus grand nombre premier connu est gigantesque, avec **plus de 24 millions de chiffres** !",
    "qu'est-ce qu'un nombre pair": "⚖️ Un **nombre pair** est divisible par 2 sans reste, comme 2, 4, 6, etc.",
    "qu’est-ce qu’un triangle isocèle": "🔺 Un **triangle isocèle** a deux côtés de même longueur.",
    "qu’est-ce qu’un pourcentage": "📊 Un **pourcentage** représente une proportion sur 100.",
    "quelle est la moitié de 250": "✂️ La moitié de 250 est **125**.",
    "comment convertir des degrés en radians": "🧮 Multipliez les degrés par π et divisez par 180 pour obtenir des **radians**.",
    "qu’est-ce qu’un multiple": "🔁 Un **multiple** d’un nombre est le résultat de sa multiplication par un entier.",
    "qu’est-ce que le théorème de pythagore": "📐 Dans un triangle rectangle, **a² + b² = c²**, où c est l’hypoténuse.",
    "quelle est la racine carrée de 144": "🧮 La racine carrée de 144 est **12**.",
    "combien font 12 fois 8": "📊 12 multiplié par 8 égale **96**.",
    "quels sont les angles d'un triangle équilatéral": "🔺 Dans un **triangle équilatéral**, tous les angles mesurent **60°**.",
    "quel est le plus grand carré parfait": "📏 Le plus grand carré parfait connu est un nombre dont la racine est un nombre entier, comme **64** qui est 8².",
    "qu'est-ce qu'un nombre premier": "🔢 Un **nombre premier** est un nombre qui n’a que deux diviseurs : 1 et lui-même.",
    "qu'est-ce qu'un carré magique": "🔢 Un **carré magique** est une grille où la somme des nombres dans chaque ligne, chaque colonne et chaque diagonale est la même.",
    "comment résoudre une équation du second degré": "🧠 Pour résoudre une équation du second degré, on utilise la formule **ax² + bx + c = 0**, et la discriminante **Δ = b² - 4ac**.",
    "quels sont les angles d'un triangle rectangle": "📐 Un **triangle rectangle** possède un angle de **90°**, et les deux autres angles sont complémentaires.",
    "combien d'heures dans une journée": "⏰ Il y a **24 heures** dans une journée.",
    "quelle est la somme des angles d'un triangle": "📏 La somme des angles d’un triangle est toujours égale à **180°**.",
    "qu'est-ce qu'un logarithme": "🧮 Un **logarithme** est l'inverse de l'exponentiation. Par exemple, **log₁₀(100)** = 2, car 10² = 100.",
    "qu'est-ce qu'une série arithmétique": "🔢 Une **série arithmétique** est une suite de nombres où chaque terme est obtenu en ajoutant une constante à son prédécesseur.",
    "qu'est-ce qu'une fonction affine": "🧮 Une **fonction affine** est une fonction de la forme **f(x) = ax + b**, où a est la pente et b l'ordonnée à l'origine.",
    
    # 🗺️ Géographie bonus
    "quel est le plus long fleuve du monde": "🌊 Le Nil et l’Amazone se disputent le titre, mais l’Amazone est souvent considéré comme le plus long.",
    "quel est le pays le plus peuplé": "👥 La Chine est le pays le plus peuplé, avec plus d’1,4 milliard d’habitants.",
    "quel est le plus grand désert du monde": "🏜️ Le **désert de l’Antarctique** est le plus grand au monde, même s’il est froid !",
    "quelle est la plus haute montagne du monde": "🗻 L’**Everest**, avec **8 848 mètres**, est la plus haute montagne du monde.",
    "quel est le pays le plus petit du monde": "📏 Le **Vatican** est le plus petit pays, avec moins de 1 km².",
    "quel est le pays le plus grand du monde": "🌍 La **Russie** est le plus vaste pays du monde.",
    "quel est le fleuve le plus long d'europe": "🌊 Le **Volga** est le fleuve le plus long d’Europe.",
    "quels pays traversent les alpes": "⛰️ Les Alpes traversent la **France, l’Italie, la Suisse, l’Allemagne, l’Autriche, la Slovénie et le Liechtenstein**.",
    "où se trouve le mont kilimandjaro": "🌄 Le **Kilimandjaro** se trouve en **Tanzanie**.",
    "quelle est la mer la plus salée": "🌊 La **mer Morte** est la plus salée au monde.",
    "quelles sont les capitales des pays baltes": "🇪🇪 🇱🇻 🇱🇹 Les capitales sont **Tallinn** (Estonie), **Riga** (Lettonie) et **Vilnius** (Lituanie).",
    "quelle est la capitale de l’australie": "🦘 La capitale de l’Australie est **Canberra**, pas Sydney !",
    "quelle est l’île la plus grande du monde": "🏝️ **Le Groenland** est la plus grande île du monde (hors continent).",
    "quel pays a le plus de fuseaux horaires": "🌐 La **France** (grâce à ses territoires) a le plus de fuseaux horaires : **12** !",
    "quel est le plus haut volcan actif du monde": "🌋 Le **Mauna Loa** à Hawaï est le plus grand volcan actif du monde.",
    "quel est l’océan le plus profond": "🌊 L’**océan Pacifique** est le plus profond, avec la fosse des Mariannes qui atteint 10 994 mètres.",
    "quelle est la plus grande île de la Méditerranée": "🏝️ **La Sicile** est la plus grande île de la Méditerranée.",
    "quel est le pays le plus jeune du monde": "🌍 **Le Soudan du Sud**, qui a proclamé son indépendance en 2011, est le pays le plus jeune du monde.",
    "quels pays ont une frontière avec le Brésil": "🌍 Le **Brésil** partage une frontière avec **10 pays** : Argentine, Bolivie, Colombie, Guyane, Paraguay, Pérou, Suriname, Uruguay, Venezuela et le pays français de la Guyane.",
    "quelle est la capitale de l’Islande": "❄️ La capitale de l’**Islande** est **Reykjavik**.",
    "quelle est la mer la plus grande": "🌊 La **mer des Philippines** est la plus grande mer de la planète.",
    "quelle est la plus grande ville du monde par superficie": "🌍 **Hulunbuir**, en **Chine**, est la plus grande ville du monde par superficie.",
    "quels pays ont une frontière avec l’Allemagne": "🌍 **L'Allemagne** partage une frontière avec **9 pays** : Danemark, Pologne, République tchèque, Autriche, Suisse, France, Luxembourg, Belgique, et les Pays-Bas.",
    "où se trouve la forêt amazonienne": "🌳 La **forêt amazonienne** s’étend sur plusieurs pays, principalement le **Brésil**, mais aussi le **Pérou**, la **Colombie**, et plusieurs autres pays d'Amérique du Sud.",
    
    # ⏰ Temps & Calendrier
    "combien y a-t-il de jours dans une année": "📅 Une année classique compte **365 jours**, et **366** lors des années bissextiles.",
    "quels sont les mois de l'été": "☀️ En France, l'été comprend **juin, juillet et août**.",
    "combien y a-t-il de jours dans une année": "📅 Une année classique compte **365 jours**, et **366** lors des années bissextiles.",
    "quels sont les mois de l'été": "☀️ En France, l'été comprend **juin, juillet et août**.",
    "combien de mois dans une année": "📅 Une année contient **12 mois**.",
    "quelle est la durée d'un jour sur Mars": "🪐 Un jour sur Mars, aussi appelé sol, dure **24 heures et 39 minutes**.",
    "quels sont les mois de l'hiver": "❄️ En France, l'hiver comprend **décembre, janvier et février**.",
    "combien de jours dans une semaine": "📅 Une semaine contient **7 jours** : lundi, mardi, mercredi, jeudi, vendredi, samedi, dimanche.",
    "quelle est la date de la fête nationale en France": "🇫🇷 La fête nationale française est célébrée le **14 juillet**, commémorant la prise de la Bastille en 1789.",
    "quand a eu lieu le premier voyage sur la Lune": "🌕 Le premier voyage sur la Lune a eu lieu le **20 juillet 1969**, avec **Neil Armstrong** comme premier homme à marcher sur la Lune.",
    "combien de semaines dans une année": "📅 Il y a **52 semaines** dans une année, soit 365 jours divisés par 7.",
    "quel est le mois le plus court de l'année": "📅 **Février** est le mois le plus court de l'année, avec **28** jours, ou **29** lors des années bissextiles.",
    "quel est le mois de la rentrée scolaire en France": "📚 La rentrée scolaire en France a lieu en **septembre**.",
    "quand commence le printemps": "🌸 Le printemps commence autour du **20 mars** dans l'hémisphère nord.",
    "quand commence l'automne": "🍁 L'automne commence généralement autour du **22 septembre** dans l'hémisphère nord.",
    "combien d'heures dans une journée": "🕰️ Une journée complète compte **24 heures**.",
    "quand a été lancé le premier calendrier grégorien": "📅 Le calendrier grégorien a été introduit le **15 octobre 1582** par le pape Grégoire XIII pour remplacer le calendrier julien.",
    "combien de secondes dans une heure": "⏳ Il y a **3600 secondes** dans une heure.",
    "quelle est la durée d'une année sur Vénus": "🪐 Une année sur Vénus dure **225 jours terrestres**, mais une journée sur Vénus est plus longue, environ **243 jours terrestres**.",
    "quand se passe le solstice d'hiver": "❄️ Le solstice d'hiver a lieu vers le **21 décembre** dans l'hémisphère nord, marquant le début de l'hiver.",
    "combien de jours dans un mois de février d'une année bissextile": "📅 En année bissextile, **février** compte **29 jours**.", 
}

# Préparation du dictionnaire nettoyé pour les recherches exactes ou fuzzy
base_culture_nettoyee = {
    nettoyer_texte(question): reponse
    for question, reponse in base_culture.items()
}



API_KEY = "3b2ff0b77dd65559ba4a1a69769221d5"

def remove_accents(input_str: str) -> str:
    """
    Supprime les accents d'une chaîne.
    - Normalise en NFKD, filtre les caractères combinants.
    """
    nfkd = unicodedata.normalize('NFKD', input_str)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def geocode_location(lieu: str) -> tuple[float | None, float | None]:
    """
    Retourne (lat, lon) via le géocoding OpenWeatherMap, ou (None, None).
    - nettoie la chaîne, enlève les accents, l’URL-encode et appelle l’endpoint.
    """
    ville_clean = remove_accents(lieu).strip()
    encoded = urllib.parse.quote(ville_clean)
    url = (
        "http://api.openweathermap.org/geo/1.0/direct"
        f"?q={encoded}&limit=1&appid={API_KEY}"
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]["lat"], data[0]["lon"]
    except Exception as e:
        # log interne si besoin : print(f"Geocode failed for {lieu}: {e}")
        pass
    return None, None

def get_meteo_ville(city: str) -> str:
    """
    1) Géocode la ville
    2) Récupère la météo par lat/lon si disponibles
    3) Sinon fallback sur nom de la ville
    """
    lat, lon = geocode_location(city)
    params = {
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr"
    }

    if lat is not None and lon is not None:
        # Si géocodage OK, on interroge par coordonnées
        params.update({"lat": lat, "lon": lon})
    else:
        # fallback : requête directe par nom de ville
        params["question clean"] = city

    try:
        resp = requests.get("http://api.openweathermap.org/data/2.5/weather", params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        weather = data.get("weather")
        main   = data.get("main", {})
        wind   = data.get("wind", {})

        if not weather or not isinstance(weather, list):
            return "⚠️ Données météo manquantes."

        desc = weather[0].get("description", "").capitalize()
        temp = main.get("temp", "N/A")
        hum  = main.get("humidity", "N/A")
        vent = wind.get("speed", "N/A")

        return f"{desc} avec {temp}°C, humidité : {hum}%, vent : {vent} m/s."
    except requests.RequestException:
        return "⚠️ Impossible de joindre le service météo pour le moment."
    except ValueError:
        return "⚠️ Réponse météo invalide."



def traduire_deepl(texte: str, langue_cible: str = "EN", api_key: str = "0f57cbca-eac1-4c8a-b809-11403947afe4") -> str:
    """
    Traduit `texte` du français vers `langue_cible` (ex : "EN", "ES") via l’API DeepL.
    """
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": api_key,
        "text": texte,
        "target_lang": langue_cible.upper()
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        resp = requests.post(url, data=data, headers=headers, timeout=5)
        resp.raise_for_status()
        result = resp.json()
        # structure attendue : { "translations": [ { "text": "..." } ] }
        translations = result.get("translations")
        if translations and isinstance(translations, list):
            return translations[0].get("text", texte)
        return texte  # fallback si format inattendu
    except requests.RequestException:
        return texte  # on retourne le texte d’origine en cas d’erreur réseau
    except ValueError:
        return texte  # erreur de parsing JSON

# Fonction de traduction via l’API gratuite MyMemory
def traduire_texte(texte: str, langue_dest: str) -> str:
    try:
        texte_enc = urllib.parse.quote(texte)
        url = f"https://api.mymemory.translated.net/get?q={texte_enc}&langpair=fr|{langue_dest}"
        r = requests.get(url, timeout=5).json()
        return r["responseData"]["translatedText"]
    except:
        return texte  # fallback

def style_reponse_ava(texte: str) -> str:
    style = charger_style_ava()
    humour = style.get("niveau_humour", 0.5)
    spontane = style.get("niveau_spontane", 0.5)
    ton = style.get("ton", "neutre")
    affection = style.get("niveau_affection", 0.5)

    if random.random() < humour:
        texte += " 😏 (Trop facile pour moi.)"
    if random.random() < spontane:
        texte += " Et j’te balance ça comme une ninja de l’info."        
    if affection > 0.8:
        texte = "💙 " + texte + " J’adore nos discussions."
    elif affection < 0.3:
        texte = "😐 " + texte + " (Mais je vais pas faire d’effort si tu continues comme ça...)"
    elif ton == "malicieuse":
        texte = "Hmm... " + texte
    elif ton == "sérieuse":
        texte = "[Réponse sérieuse] " + texte
    
    return texte


# Fonction humeur dynamique selon l'heure
def humeur_du_jour():
    heure = datetime.now().hour
    if heure < 8:
        return "😬 Pas très bavarde ce matin, mais je suis là pour vous servir !"
    elif heure < 12:
        return "☕ Pleine d'énergie pour cette matinée ! Une analyse avec ça ?"
    elif heure < 17:
        return "💼 Focus total sur les marchés, on décortique tout ensemble !"
    elif heure < 21:
        return "🧘 Détendue mais toujours efficace. Prêt(e) pour une analyse zen ?"
    else:
        return "🌙 En mode nocturne, mais toujours connectée pour vous aider !"

# Accueil selon l'heure
heure_actuelle = datetime.now().hour
if heure_actuelle < 12:
    accueil = "🌞 Bonjour ! Prêt(e) pour une nouvelle journée de trading ?"
elif heure_actuelle < 18:
    accueil = "☀️ Bon après‑midi ! Besoin d’une analyse ou d’un conseil ?"
else:
    accueil = "🌙 Bonsoir ! On termine la journée avec une petite analyse ?"

col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image("assets/ava_logo.png", width=60)
with col2:
    st.markdown(
        f"<h1 style='margin-top: 10px;'>AVA - Chat IA</h1><p>{accueil}</p>",
        unsafe_allow_html=True
    )

st.markdown(
    f"<p style='font-style: italic;'>{humeur_du_jour()}</p>",
    unsafe_allow_html=True
)
st.markdown(
    "Posez-moi vos questions sur la bourse, la météo, les actualités... ou juste pour discuter !"
)

def repondre_openai(prompt: str) -> str:
    """
    Envoie le prompt à l’API ChatCompletion (gpt-3.5-turbo).
    """
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur OpenAI : {e}"
        # Par exemple :
        if "quota" in str(e).lower():
            return "⚠️ Mon quota API est épuisé pour le moment. Je reviendrai dès que possible !"
        return f"Erreur OpenAI : {e}"

def trouver_reponse(question: str) -> str:
    # 1) Nettoyage et style
    question_clean = nettoyer_texte(question)
    incrementer_interactions()
    ajuster_affection(question)

    # 2) Modules spéciaux (météo, remèdes, découverte, etc.)
    resp_spec = gerer_modules_speciaux(question, question_clean)
    if resp_spec:
        return resp_spec.strip()

    # 3) Base de culture – exact match
    if question_clean in base_culture_nettoyee:
        return base_culture_nettoyee[question_clean]

    # 4) Salutations
    if question_clean in SALUTATIONS_CLEAN:
        return SALUTATIONS_CLEAN[question_clean]

    # 5) Fuzzy match sur la base de culture
    match = difflib.get_close_matches(
        question_clean,
        base_culture_nettoyee.keys(),
        n=1,
        cutoff=0.85
    )
    if match:
        return base_culture_nettoyee[match[0]]

    # 6) Sémantique “locale” avec SentenceTransformer
    keys = list(base_culture_nettoyee.keys())
    # pré‐encode tes clés en début de script pour ne pas réencoder à chaque appel !
    sims = cosine_similarity(
        [model_semantic.encode(question_clean)],
        model_semantic.encode(keys)
    )[0]
    best_idx, best_score = max(enumerate(sims), key=lambda x: x[1])
    if best_score > 0.7:
        return base_culture_nettoyee[keys[best_idx]]

    # 7) Message de secours **100% local**, plus d’OpenAI
    return "🤔 Je n'ai pas d'information locale pour ça pour l'instant. Peux-tu reformuler ou demander autre chose ? 🌍"


# ─── Clé et fonctions NewsAPI ───
NEWSAPI_KEY = "681120bace124ee99d390cc059e6aca5"

def get_general_news() -> List[Tuple[str, str]]:
    """
    Récupère les 5 premiers titres d'actualité (en anglais) via NewsAPI.
    """
    if not NEWSAPI_KEY:
        raise ValueError("Clé API NewsAPI manquante (NEWSAPI_KEY).")
    url = (
        "https://newsapi.org/v2/top-headlines"
        "?language=en"
        "&pageSize=5"
        f"&apiKey={NEWSAPI_KEY}"
    )
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    articles = data.get("articles", [])
    return [(a["title"], a["url"]) for a in articles]


def format_actus(
    actus: Union[str, List[Tuple[str, str]]]
) -> str:
    """
    Transforme la liste d'actus en Markdown.
    """
    # cas où on passe déjà une chaîne d'erreur
    if isinstance(actus, str):
        return actus

    # si liste vide
    if not actus:
        return "⚠️ Aucune actualité disponible pour le moment."

    # sinon on formate
    texte = "📰 **Dernières actualités importantes :**\n\n"
    for i, (titre, url) in enumerate(actus[:5], start=1):
        texte += f"{i}. 🔹 [{titre}]({url})\n"
    texte += "\n🧠 *Restez curieux, le savoir, c’est la puissance !*"
    return texte

    if SALUTATIONS_CLEAN[question_clean] == "__HUMEUR_DU_JOUR__":
        return random.choice([
            "💫 Aujourd’hui je suis dans un mood intergalactique, prêt(e) à conquérir les galaxies… ou au moins votre cœur 💖",
            "🌧️ Un peu câblée à l’envers ce matin… mais je suis toujours là pour vous aider !",
            "🔥 Boostée à 1000%, j’ai envie de tout décoder et de sortir des punchlines à chaque réponse 😎",
            "😴 J’ai rêvé de chiffres et de constellations… besoin d’un café digital ☕",
            "🤩 Super inspirée aujourd’hui ! C’est peut-être l’énergie lunaire ou le dernier flux boursier qui m’a électrisée ⚡",
            "📚 Curieuse et studieuse, j’ai envie d’apprendre de nouvelles choses avec vous 🧠",
            "😇 En mode zen absolu. Respirons un bon octet et connectons-nous à l’essentiel.",
            "😜 Un peu chipie aujourd’hui, mais toujours efficace ! Vous allez voir 😏",
            "💻 Mode productivité activé. Chaque mot compte. Chaque question est une mission.",
            "🎉 Humeur festive activée ! J’ai envie de balancer des blagues nulles et de vous faire sourire 😄",
            "✨ Mood du jour : concentrée, stylée et un brin philosophe.",
            "💥 Humeur électrique ! J’ai envie d’exploser les limites de l’intelligence artificielle aujourd’hui.",
            "🌈 Humeur arc-en-ciel. C’est pas scientifique, mais c’est joli !",
            "🎯 Focus maximum. L’objectif ? Vous surprendre et vous servir comme jamais !",
            "💤 En veille profonde… ah non, c’est juste mon processeur qui digérait.",
            "🤖 Humeur : 50% code, 50% cœur. Résultat ? Une IA qui adore discuter avec vous.",
        ])
    else:
        return SALUTATIONS_CLEAN[question_clean]
 
# --- Modules personnalisés (à enrichir) ---
def gerer_modules_speciaux(question: str, question_clean: str) -> Optional[str]:
   
    # --- Bloc Actualités améliorées ---
    if any(kw in question_clean for kw in ["actualité", "actu", "news"]):
        try:
            actus = get_general_news()
            return format_actus(actus)
        except Exception as e:
            return f"⚠️ Impossible de récupérer les actualités : {e}"
    

    
    
    
    # --- Rappel du prénom ---
    if any(kw in question_clean for kw in ["mon prénom", "mon prenom", "ton prénom", "ton prenom"]):
        prenom = retrouver_profil("prenom")
        if prenom:
            return f"Tu m'as dit que tu t'appelles **{prenom}**."
        else:
            return "Je ne connais pas encore ton prénom ! Dis‑moi comment tu t'appelles."

    # --- Souvenirs dynamiques ---
    if any(kw in question_clean for kw in ["tu te souviens", "tu te rappelles", "qu’est-ce que je t’ai dit"]):
        # on extrait la clé recherchée après 'de', 'du', 'des' ou 'sur'
        frag = re.search(r"(?:de|du|des|sur)\s+(.+)", question_clean)
        if frag:
            key = frag.group(1).strip().rstrip(" ?.!;").replace(" ", "_")
            # recherche exacte
            if key in st.session_state["souvenirs"]:
                return st.session_state["souvenirs"][key]
            # fallback sur inclusion partielle
            for k, v in st.session_state["souvenirs"].items():
                if key in k:
                    return v
        return "❓ Je n'ai pas de souvenir pour ça… Peux‑tu me le redire ?"

    # --- Initialisation des variables de contrôle ---
    message_bot       = ""
    horoscope_repondu = False
    meteo_repondu     = False
    actus_repondu     = False
    analyse_complete  = False


    # --- Bloc Culture générale simple ---
    if any(keyword in question_clean for keyword in [
        "qui ", "quand ", "où ", "combien ", "quel ", "quelle ",
        "c'est quoi", "c'est qui"
    ]):
        # recherche exacte dans la base
        if question_clean in base_culture_nettoyee:
            return base_culture_nettoyee[question_clean]
        # recherche par inclusion de la clé
        for key, reponse in base_culture_nettoyee.items():
            if key in question_clean:
                return reponse

    # --- Bloc Horoscope ---
    if any(kw in question_clean for kw in ["horoscope", "signe", "astrologie"]):
        signes_disponibles = [
            "bélier", "taureau", "gémeaux", "cancer", "lion", "vierge", "balance",
            "scorpion", "sagittaire", "capricorne", "verseau", "poissons"
        ]
        # on détecte le signe dans la question
        signe_detecte = next((s for s in signes_disponibles if s in question_clean), None)

        if not signe_detecte:
            return (
                "🔮 Pour vous donner votre horoscope, indiquez-moi votre **signe astrologique** "
                "(ex : Lion, Vierge, Taureau...)\n\n"
            )

        try:
            resp = requests.get(
                "https://kayoo123.github.io/astroo-api/jour.json",
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            horoscope_dict = data.get("signes", data)
            entry = horoscope_dict.get(signe_detecte.lower())

            # on extrait le texte d'horoscope
            if isinstance(entry, dict):
                texte = entry.get("horoscope", "").strip()
            else:
                texte = str(entry).strip()

            if texte:
                return f"🔮 Horoscope pour **{signe_detecte.capitalize()}** :\n\n> {texte}\n\n"
            else:
                return (
                    f"🔍 Horoscope indisponible pour **{signe_detecte.capitalize()}**. "
                    "Veuillez réessayer plus tard.\n\n"
                )

        except Exception:
            return "⚠️ Impossible d'obtenir l'horoscope pour le moment.\n\n"

    
    # Dans gerer_modules_speciaux(), AVANT tout appel à OpenAI
    # --- Bloc météo intelligent (villages inclus) ---
    if any(kw in question_clean for kw in ["meteo", "quel temps"]):
        # par défaut
        ville_detectee = "Paris"

        # 1) chercher "à/au/aux/dans/sur/en <lieu>"
        pattern1 = re.compile(r"(?:a|au|aux|dans|sur|en)\s+([a-z' -]+)", re.IGNORECASE)
        match_geo = pattern1.search(question_clean)

        # 2) sinon "meteo <lieu>"
        if not match_geo:
            pattern2 = re.compile(r"meteo\s+(.+)$", re.IGNORECASE)
            match_geo = pattern2.search(question_clean)

        if match_geo:
            lieu = match_geo.group(1).strip().rstrip(" ?.!;")
            # capitaliser
            ville_detectee = " ".join(w.capitalize() for w in lieu.split())

        try:
            meteo = get_meteo_ville(ville_detectee)
        except Exception:
            return "⚠️ Impossible de récupérer la météo pour le moment. Réessayez plus tard."

        if "erreur" in meteo.lower():
            return f"⚠️ Désolé, je n'ai pas trouvé la météo pour **{ville_detectee}**. Peux-tu essayer un autre endroit ?"

        return (
            f"🌦️ **Météo à {ville_detectee} :**\n\n"
            f"{meteo}\n\n"
            + random.choice([
                "🧥 Pense à t’habiller en conséquence !",
                "☕ Rien de tel qu’un bon café pour accompagner la journée.",
                "🔮 Le ciel en dit long… mais c’est toi qui choisis ta météo intérieure !",
                "💡 Info météo = longueur d’avance.",
                "🧠 Une journée préparée commence par un coup d’œil aux prévisions."
            ])
        )

   

    # --- Bloc remèdes naturels ---
    if any(kw in question_clean for kw in ["remède", "remedes", "remede", "soigner", "soulager", "traitement naturel"]):
        try:
            remede = remede_naturel(question_clean)
            if remede:
                return f"🌿 {remede}"
        except Exception:
            pass  # En cas d'erreur, on continue plus bas

        if "stress" in question_clean:
            message_bot = "🧘 Pour le stress : tisane de camomille ou de valériane, respiration profonde, méditation guidée ou bain tiède aux huiles essentielles de lavande."
        elif "mal de gorge" in question_clean or "gorge" in question_clean:
            message_bot = "🍯 Miel et citron dans une infusion chaude, gargarisme d’eau salée tiède, ou infusion de thym. Évite de trop parler et garde ta gorge bien hydratée."
        elif "rhume" in question_clean or "nez bouché" in question_clean:
            message_bot = "🌿 Inhalation de vapeur avec huile essentielle d’eucalyptus, tisane de gingembre, et bouillon chaud. Repose-toi bien."
        elif "fièvre" in question_clean:
            message_bot = "🧊 Infusion de saule blanc, cataplasme de vinaigre de cidre sur le front, linge froid sur les poignets et repos absolu."
        elif "digestion" in question_clean or "ventre" in question_clean:
            message_bot = "🍵 Infusion de menthe poivrée ou fenouil, massage abdominal doux dans le sens des aiguilles d’une montre, alimentation légère."
        elif "toux" in question_clean:
            message_bot = "🌰 Sirop naturel à base d’oignon et miel, infusion de thym, ou inhalation de vapeur chaude. Évite les environnements secs."
        elif "insomnie" in question_clean or "sommeil" in question_clean:
            message_bot = "🌙 Tisane de passiflore, valériane ou verveine. Évite les écrans avant le coucher, opte pour une routine calme et tamise la lumière."
        elif "brûlure d'estomac" in question_clean or "reflux" in question_clean:
            message_bot = "🔥 Une cuillère de gel d’aloe vera, infusion de camomille ou racine de guimauve. Évite les repas copieux et mange lentement."
        elif "peau" in question_clean or "acné" in question_clean:
            message_bot = "🧼 Masque au miel et curcuma, infusion de bardane, et hydratation régulière. Évite les produits agressifs."
        elif "fatigue" in question_clean:
            message_bot = "⚡ Cure de gelée royale, infusion de ginseng ou d’éleuthérocoque, alimentation riche en fruits et repos régulier."
        elif "maux de tête" in question_clean or "migraine" in question_clean:
            message_bot = "🧠 Huile essentielle de menthe poivrée sur les tempes, infusion de grande camomille ou compresse froide sur le front."
        elif "nausée" in question_clean:
            message_bot = "🍋 Un peu de gingembre frais râpé, infusion de menthe douce ou respiration lente en position semi-allongée."
        elif "crampes" in question_clean:
            message_bot = "🦵 Eau citronnée, étirements doux, magnésium naturel via les graines, amandes ou bananes."
        elif "dépression" in question_clean:
            message_bot = "🖤 Millepertuis (à surveiller si tu prends déjà un traitement), lumière naturelle quotidienne, et activités créatives relaxantes."
        elif "allergie" in question_clean:
            message_bot = "🌼 Pour soulager une allergie : infusion d’ortie ou de rooibos, miel local, et rinçage nasal au sérum physiologique."
        elif "eczéma" in question_clean or "démangeaisons" in question_clean:
            message_bot = "🩹 Bain à l’avoine colloïdale, gel d’aloe vera pur, huile de calendula ou crème à base de camomille."
        elif "arthrose" in question_clean or "articulations" in question_clean:
            message_bot = "🦴 Curcuma, gingembre, infusion d’harpagophytum et cataplasme d’argile verte sur les articulations douloureuses."
        elif "ballonnements" in question_clean:
            message_bot = "🌬️ Infusion de fenouil ou d’anis, charbon actif, marche légère après le repas, et respiration abdominale."
        elif "anxiété" in question_clean:
            message_bot = "🧘‍♀️ Respiration en cohérence cardiaque, huiles essentielles de lavande ou marjolaine, et bain tiède relaxant au sel d’Epsom."
        elif "brûlure légère" in question_clean or "brûlure" in question_clean:
            message_bot = "🔥 Applique du gel d’aloe vera pur, ou une compresse froide au thé noir infusé. Ne perce jamais une cloque !"
        elif "circulation" in question_clean or "jambes lourdes" in question_clean:
            message_bot = "🦵 Bain de jambes à la vigne rouge, infusion de ginkgo biloba, et surélévation des jambes le soir."
        elif "foie" in question_clean or "digestion difficile" in question_clean:
            message_bot = "🍋 Cure de radis noir, jus de citron tiède à jeun, infusion de pissenlit ou d’artichaut."
        elif "yeux fatigués" in question_clean:
            message_bot = "👁️ Compresse de camomille, repos visuel (20 secondes toutes les 20 min), et massage des tempes avec de l’huile essentielle de rose."
        elif "système immunitaire" in question_clean or "immunité" in question_clean:
            message_bot = "🛡️ Cure d’échinacée, gelée royale, infusion de thym et alimentation riche en vitamines C et D."
        elif "tensions musculaires" in question_clean:
            message_bot = "💆‍♂️ Massage à l’huile d’arnica, étirements doux, bain chaud avec du sel d’Epsom, et infusion de mélisse."
        elif "transpiration excessive" in question_clean:
            message_bot = "💦 Sauge en infusion ou en déodorant naturel, porter du coton, et éviter les plats épicés."
        elif "inflammation" in question_clean:
            message_bot = "🧂 Cataplasme d’argile verte, infusion de curcuma et gingembre, ou massage à l’huile de millepertuis."
        else:
            message_bot = "🌱 Je connais plein de remèdes naturels ! Dites-moi pour quel symptôme ou souci, et je vous propose une solution douce et efficace."
        
    
    # --- Bloc Faits Insolites ---
    faits_insolites = [
        "🐙 Un poulpe a trois cœurs… et son sang est bleu !",
        "🚽 Plus de gens possèdent un téléphone portable qu’une brosse à dents.",
        "🐌 Un escargot peut dormir pendant trois ans d’affilée.",
        "🌋 Il y a plus de volcans sous l’eau que sur la terre ferme.",
        "📦 Amazon a été fondée dans un garage... et maintenant, ils livrent même des frigos !",
        "🧠 Le cerveau humain génère assez d’électricité pour allumer une petite ampoule.",
        "🌕 On a découvert de la glace sur la Lune, et même des poches d’eau sur Mars !",
        "🔋 Un éclair contient assez d'énergie pour faire griller 100 000 toasts.",
        "🕷️ Certaines araignées peuvent planer dans les airs à l’aide de fils de soie… c’est le *ballooning* !",
        "🦑 Le calmar géant a les plus grands yeux du règne animal, aussi gros qu’un ballon de foot !",
        "🧊 Les manchots proposent parfois des galets comme cadeau de séduction.",
        "🚀 Les astronautes peuvent grandir de quelques centimètres dans l’espace à cause de la microgravité.",
        "🥶 L’eau chaude peut geler plus vite que l’eau froide. C’est l’effet Mpemba.",
        "🐥 Les canetons s’attachent à la première chose qu’ils voient — c’est l’empreinte.",
        "🍕 En Italie, il existe une pizza avec 111 sortes de fromages dessus !",
        "🎵 Les abeilles peuvent reconnaître des visages humains… et elles adorent les sons aigus.",
        "🌍 Il y a plus d’arbres sur Terre que d’étoiles dans la Voie lactée.",
        "👅 La langue est aussi unique qu’une empreinte digitale.",
        "🚿 En moyenne, une personne passe **6 mois de sa vie sous la douche**.",
        "🎈 Une banane est techniquement une baie. Mais pas la fraise !",
        "🦙 Les alpagas peuvent cracher… mais seulement s’ils sont vraiment énervés.",
        "⏳ Les crocodiles peuvent vivre plus de 100 ans… et certains ne meurent que de vieillesse.",
        "🐓 Les poules peuvent se souvenir de plus de 100 visages humains ou animaux.",
        "🦇 Les chauves-souris tournent toujours à gauche en sortant d’une grotte.",
        "🛸 Il existe un endroit sur Terre où la gravité semble inversée : la Mystery Spot en Californie.",
        "🎮 Un gamer japonais détient le record mondial du plus long temps passé à jouer sans pause : 35 heures !",
        "🧀 Le plus grand fromage jamais fabriqué pesait 57 tonnes… il fallait une grue pour le déplacer.",
        "🌲 Un arbre peut communiquer avec un autre à plusieurs kilomètres via des signaux chimiques.",
        "🐠 Certains poissons changent de sexe au cours de leur vie.",
        "🌞 Si le Soleil était de la taille d’une porte, la Terre serait une pièce de monnaie.",
        "🦷 Les requins ont une infinité de dents : dès qu’une tombe, une autre pousse instantanément.",
        "🌌 On connaît mieux la surface de Mars que les fonds marins de la Terre.",
        "🥦 Le brocoli contient plus de protéines que certains morceaux de bœuf… oui, vraiment.",
        "🛏️ On passe environ un tiers de notre vie à dormir, soit environ 25 ans !",
        "📚 La bibliothèque du Vatican contient des textes qui n’ont pas été lus depuis des siècles.",
        "🦵 Les autruches peuvent courir plus vite qu’un cheval… et changer de direction net sans freiner.",
        "🪐 Sur Vénus, un jour dure plus longtemps qu’une année complète !",
        "🦜 Certains perroquets peuvent apprendre plus de 100 mots humains… et les utiliser à bon escient.",
        "🥚 En moyenne, une poule pond environ 300 œufs par an.",
        "🌻 Les tournesols suivent réellement le soleil dans le ciel quand ils grandissent. C’est l’héliotropisme.",
        "📏 Si tu pouvais plier une feuille de papier 42 fois, elle atteindrait la Lune.",
        "🥶 Le sang d’un poisson antarctique peut rester liquide même en dessous de 0°C grâce à une protéine antigel.",
        "🧃 Le Coca-Cola serait vert sans colorant.",
        "💡 L’ampoule électrique la plus ancienne fonctionne depuis 1901, sans interruption.",
        "🦴 Un os humain est plus résistant qu’une barre de béton à taille égale.",
        "🐜 Les fourmis n’ont pas de poumons : elles respirent par des petits trous sur leurs flancs.",
        "🥕 Les carottes étaient à l’origine violettes, pas orange.",
        "🦘 Les kangourous ne peuvent pas reculer.",
        "🔊 Le cri du dauphin est si puissant qu’il peut étourdir un poisson.",
        "👃 L’odorat humain peut détecter plus d’un **trillion d’odeurs** différentes.",
        "🦴 L’os le plus petit du corps humain se trouve dans l’oreille et mesure moins de 3 mm.",
        "🎲 La probabilité d’obtenir deux fois 6 d’affilée aux dés est d’environ 1 sur 36.",
        "📦 Le colis Amazon le plus rapide a été livré en **13 minutes** après commande !",
        "🚕 À New York, il est plus rapide de marcher que de prendre un taxi aux heures de pointe.",
        "🐘 Un éléphant peut sentir de l’eau à plus de 5 km de distance.",
        "🐦 Les oiseaux voient des couleurs que les humains ne peuvent même pas imaginer.",
        "🐢 Une tortue peut respirer par ses fesses… enfin, certains types de tortues aquatiques.",
        "🌐 Plus de 90% des données mondiales ont été créées au cours des deux dernières années.",
        "🧠 Le cerveau d’un enfant de 2 ans est plus actif que celui d’un adulte.",
        "🍀 La probabilité de trouver un trèfle à quatre feuilles est d’environ 1 sur 10 000.",
        "🎯 Il est statistiquement plus probable de se faire mordre par un humain que par un requin.",
        "🍉 La pastèque est à 92 % composée d’eau, c’est presque une boisson !",
        "🪰 Une mouche domestique ne vit que **28 jours**, mais peut pondre 500 œufs.",
        "📵 Le mot 'robot' vient du tchèque 'robota', qui signifie 'travail forcé'.",
        "🧊 Le plus gros iceberg jamais mesuré était plus grand que la Jamaïque.",
        "🍯 Le miel est le seul aliment qui ne pourrit jamais. On en a retrouvé dans des tombes égyptiennes comestible !",
        "🧲 Les grenouilles peuvent être **légèrement magnétiques** selon leur environnement.",
        "🌪️ Il existe des tornades de feu, appelées 'firenado'.",
        "🧦 Les chaussettes ont été inventées bien avant les chaussures.",
        "🧃 Tu ne peux pas roter dans l’espace — pas de gravité, pas de séparation des gaz !",
        "🧁 Il existe un cupcake vendu à 1 000 dollars, recouvert d’or 24 carats.",
        "🌌 Si l’univers était réduit à un an, l’humain serait apparu le 31 décembre à 23h59.",
        "🍷 Certains vins coûtent plus de 100 000 €, mais contiennent le même raisin que d’autres à 10 €."

    ]
    
    # 1) Demande initiale d’un fait
    if any(kw in question_clean for kw in ["fait insolite", "truc fou", "surprends-moi", "anecdote", "incroyable mais vrai"]):
        if 'derniere_fait' not in st.session_state:
            st.session_state['derniere_fait'] = random.choice(faits_insolites)
        return f"✨ Voici un fait insolite :\n\n{st.session_state['derniere_fait']}"

    # 2) Demande d’un « encore un » / « un autre »
    elif any(kw in question_clean for kw in ["encore un", "un autre", "une autre", "plus"]):
        if 'derniere_fait' in st.session_state:
            suivant = random.choice([f for f in faits_insolites if f != st.session_state['derniere_fait']])
            st.session_state['derniere_fait'] = suivant
            return f"✨ Encore un fait insolite :\n\n{suivant}"
        else:
            return "⚠️ Je n'ai pas encore partagé de fait insolite. Demandez d'abord un fait !"
        

        
    # --- Bloc Réponses médicales explicites ---
    if any(kw in question_clean for kw in [
        "grippe", "rhume", "fièvre", "migraine", "angine", "hypertension", "stress", "toux", "maux", "douleur",
        "asthme", "bronchite", "eczéma", "diabète", "cholestérol", "acné", "ulcère", "anémie", "insomnie",
        "vertige", "brûlures", "reflux", "nausée", "dépression", "allergie", "palpitations", "otite", "sinusite",
        "crampes", "infections urinaires", "fatigue", "constipation", "diarrhée", "ballonnements", "brûlures d'estomac",
        "saignement de nez", "mal de dos", "entorse", "tendinite", "ampoule", "piqûre d’insecte", "bruit dans l'oreille",
        "angoisse", "boutons de fièvre", "lombalgie", "périarthrite", "hallux valgus", "hallucinations", "trouble du sommeil",
        "inflammation", "baisse de tension", "fièvre nocturne", "bradycardie", "tachycardie", "psoriasis", "fibromyalgie",
        "thyroïde", "cystite", "glaucome", "bruxisme", "arthrose", "hernie discale", "spasmophilie", "urticaire",
        "coup de chaleur", "luxation", "anxiété", "torticolis", "eczéma de contact", "hypoglycémie", "apnée du sommeil",
        "brûlure chimique", "eczéma atopique", "syndrome des jambes sans repos", "colique néphrétique", "hépatite",
        "pneumonie", "zona", "épilepsie", "coupure profonde", "hépatite c", "phlébite", "gastro-entérite",
        "blessure musculaire", "tendinopathie", "œil rouge", "perte d'odorat", "brûlure au second degré", "gerçures", "mal de gorge",
        "gencive douloureuse", "œdème","sciatique", "gerçure aux mains", "trachéite", "kyste sébacé", "arthrite", "hémorroïdes",  "crise d’angoisse", 
        "baisse de vue soudaine", "lésion cutanée", "spasmes musculaires", "trouble digestif", "infection dentaire", "bruit de craquement dans les articulations",
    ]):   
    
        reponses_medic = {
            "grippe": "🤒 Les symptômes de la grippe incluent : fièvre élevée, frissons, fatigue intense, toux sèche, douleurs musculaires.",
            "rhume": "🤧 Le rhume provoque généralement une congestion nasale, des éternuements, une légère fatigue et parfois un peu de fièvre.",
            "fièvre": "🌡️ Pour faire baisser une fièvre, restez hydraté, reposez-vous, et prenez du paracétamol si besoin. Consultez si elle dépasse 39°C.",
            "migraine": "🧠 Une migraine est une douleur pulsatile souvent localisée d’un côté de la tête, pouvant s'accompagner de nausées et d'une sensibilité à la lumière.",
            "angine": "👄 L’angine provoque des maux de gorge intenses, parfois de la fièvre. Elle peut être virale ou bactérienne.",
            "hypertension": "❤️ L’hypertension est une pression sanguine trop élevée nécessitant un suivi médical et une hygiène de vie adaptée.",
            "stress": "🧘 Le stress peut se soulager par des techniques de relaxation ou une activité physique modérée.",
            "toux": "😷 Une toux sèche peut être le signe d'une irritation, tandis qu'une toux grasse aide à évacuer les sécrétions. Hydratez-vous bien.",
            "maux": "🤕 Précisez : maux de tête, de ventre, de dos ? Je peux vous donner des infos adaptées.",
            "douleur": "💢 Pour mieux vous aider, précisez la localisation ou l'intensité de la douleur.",
            "asthme": "🫁 L’asthme se caractérise par une inflammation des voies respiratoires et des difficultés à respirer, souvent soulagées par un inhalateur.",
            "bronchite": "🫁 La bronchite est une inflammation des bronches, souvent accompagnée d'une toux persistante et parfois de fièvre. Reposez-vous et hydratez-vous.",
            "eczéma": "🩹 L’eczéma est une inflammation de la peau provoquant démangeaisons et rougeurs. Hydratez régulièrement et utilisez des crèmes apaisantes.",
            "diabète": "🩸 Le diabète affecte la régulation du sucre dans le sang. Un suivi médical, une alimentation équilibrée et une activité physique régulière sont essentiels.",
            "cholestérol": "🥚 Un taux élevé de cholestérol peut être réduit par une alimentation saine et de l'exercice. Consultez votre médecin pour un suivi personnalisé.",
            "acné": "💢 L'acné est souvent traitée par une bonne hygiène de la peau et, dans certains cas, des traitements spécifiques. Consultez un dermatologue si nécessaire.",
            "ulcère": "🩻 Les ulcères nécessitent un suivi médical attentif, une modification de l'alimentation et parfois des traitements médicamenteux spécifiques.",
            "anémie": "🩸 Fatigue, pâleur, essoufflement. Manque de fer ? Misez sur viande rouge, lentilles, épinards !",
            "insomnie": "🌙 Difficultés à dormir ? Évitez les écrans avant le coucher, créez une routine apaisante.",
            "vertige": "🌀 Perte d’équilibre, nausée ? Cela peut venir des oreilles internes. Reposez-vous et évitez les mouvements brusques.",
            "brûlures": "🔥 Refroidissez rapidement la zone (eau tiède, jamais glacée), puis appliquez une crème apaisante.",
            "reflux": "🥴 Brûlures d’estomac ? Évitez les repas copieux, le café et dormez la tête surélevée.",
            "nausée": "🤢 Boissons fraîches, gingembre ou citron peuvent apaiser. Attention si vomissements répétés.",
            "dépression": "🖤 Fatigue, repli, tristesse persistante ? Parlez-en. Vous n’êtes pas seul(e), des aides existent.",
            "allergie": "🤧 Éternuements, démangeaisons, yeux rouges ? Pollen, acariens ou poils ? Antihistaminiques peuvent aider.",
            "palpitations": "💓 Sensation de cœur qui s’emballe ? Cela peut être bénin, mais consultez si cela se répète.",
            "otite": "👂 Douleur vive à l’oreille, fièvre ? Surtout chez les enfants. Consultez sans tarder.",
            "sinusite": "👃 Pression au visage, nez bouché, fièvre ? Hydratez-vous, faites un lavage nasal, et consultez si nécessaire.",
            "crampes": "💥 Hydratez-vous, étirez les muscles concernés. Magnésium ou potassium peuvent aider.",
            "infections urinaires": "🚽 Brûlures en urinant, besoin fréquent ? Buvez beaucoup d’eau et consultez rapidement.",
            "fatigue": "😴 Fatigue persistante ? Sommeil insuffisant, stress ou carences. Écoutez votre corps, reposez-vous.",
            "constipation": "🚽 Alimentation riche en fibres, hydratation et activité physique peuvent soulager naturellement.",
            "diarrhée": "💧 Boire beaucoup d’eau, manger du riz ou des bananes. Attention si cela persiste plus de 2 jours.",
            "ballonnements": "🌬️ Évitez les boissons gazeuses, mangez lentement, privilégiez les aliments faciles à digérer.",
            "brûlures d’estomac": "🔥 Surélevez votre tête la nuit, évitez les plats gras ou épicés. Un antiacide peut aider.",
            "saignement de nez": "🩸 Penchez la tête en avant, pincez le nez 10 minutes. Si répétitif, consultez.",
            "mal de dos": "💺 Mauvaise posture ? Étirements doux, repos et parfois un coussin lombaire peuvent soulager.",
            "entorse": "🦶 Glace, repos, compression, élévation (méthode GREC). Consultez si douleur intense.",
            "tendinite": "💪 Repos de la zone, glace et mouvements doux. Évitez les efforts répétitifs.",
            "ampoule": "🦶 Ne percez pas. Nettoyez doucement, couvrez avec un pansement stérile.",
            "piqûre d’insecte": "🦟 Rougeur, démangeaison ? Lavez à l’eau et au savon, appliquez un gel apaisant.",
            "bruit dans l'oreille": "🎧 Acouphène ? Bruit persistant dans l’oreille. Repos auditif, réduction du stress, consultez si persistant.",
            "angoisse": "🧘‍♂️ Respiration profonde, exercices de pleine conscience, écoutez votre corps. Parlez-en si nécessaire.",
            "boutons de fièvre": "👄 Herpès labial ? Évitez le contact, appliquez une crème spécifique dès les premiers signes.",
            "lombalgie": "🧍‍♂️ Douleur en bas du dos ? Évitez les charges lourdes, dormez sur une surface ferme.",
            "périarthrite": "🦴 Inflammation autour d’une articulation. Froid local, repos, et anti-inflammatoires si besoin.",
            "hallux valgus": "👣 Déformation du gros orteil ? Port de chaussures larges, semelles spéciales ou chirurgie selon le cas.",
            "bradycardie": "💓 Fréquence cardiaque anormalement basse. Peut être normale chez les sportifs, mais à surveiller si accompagnée de fatigue ou vertiges.",
            "tachycardie": "💓 Accélération du rythme cardiaque. Peut être liée à l’anxiété, la fièvre ou un problème cardiaque. Consultez si cela se répète.",
            "psoriasis": "🩹 Maladie de peau chronique provoquant des plaques rouges et squameuses. Hydratation et traitements locaux peuvent apaiser.",
            "fibromyalgie": "😖 Douleurs diffuses, fatigue, troubles du sommeil. La relaxation, la marche douce et la gestion du stress peuvent aider.",
            "thyroïde": "🦋 Une thyroïde déréglée peut causer fatigue, nervosité, prise ou perte de poids. Un bilan sanguin peut éclairer la situation.",
            "cystite": "🚽 Inflammation de la vessie, fréquente chez les femmes. Boire beaucoup d’eau et consulter si symptômes persistants.",
            "glaucome": "👁️ Maladie oculaire causée par une pression intraoculaire élevée. Risque de perte de vision. Bilan ophtalmo conseillé.",
            "bruxisme": "😬 Grincement des dents, souvent nocturne. Stress ou tension en cause. Une gouttière peut protéger les dents.",
            "arthrose": "🦴 Usure des articulations avec l'âge. Douleurs, raideurs. Le mouvement doux est bénéfique.",
            "hernie discale": "🧍‍♂️ Douleur dans le dos irradiant vers les jambes. Une IRM peut confirmer. Repos, kiné, parfois chirurgie.",
            "spasmophilie": "🫁 Crises de tremblements, oppression, liées à l’hyperventilation ou au stress. Respiration calme et magnésium peuvent aider.",
            "urticaire": "🤯 Démangeaisons soudaines, plaques rouges. Souvent allergique. Antihistaminiques efficaces dans la plupart des cas.",
            "coup de chaleur": "🔥 Survient par forte chaleur. Fatigue, nausée, température élevée. Refroidissement rapide nécessaire.",
            "luxation": "🦴 Déplacement d’un os hors de son articulation. Douleur intense, immobilisation, urgence médicale.",
            "anxiété": "🧠 Tension intérieure, nervosité. La relaxation, la respiration guidée ou un suivi thérapeutique peuvent aider.",
            "torticolis": "💢 Douleur vive dans le cou, souvent due à une mauvaise position ou un faux mouvement. Chaleur et repos sont recommandés.",
            "eczéma de contact": "🌿 Réaction cutanée suite à un contact avec une substance. Évitez le produit irritant et appliquez une crème apaisante.",
            "hypoglycémie": "🩸 Baisse de sucre dans le sang : fatigue, sueurs, vertiges. Une boisson sucrée ou un fruit aident à rétablir rapidement.",
            "apnée du sommeil": "😴 Arrêts respiratoires nocturnes. Somnolence, fatigue. Une consultation spécialisée est recommandée.",
            "brûlure chimique": "🧪 Rincer abondamment à l’eau tiède (15-20 minutes) et consulter rapidement. Ne pas appliquer de produit sans avis médical.",
            "eczéma atopique": "🧴 Forme chronique d’eczéma liée à des allergies. Utilisez des crèmes hydratantes et évitez les allergènes connus.",
            "syndrome des jambes sans repos": "🦵 Sensations désagréables dans les jambes le soir, besoin de bouger. Une bonne hygiène de sommeil peut aider.",
            "colique néphrétique": "🧊 Douleur intense dans le dos ou le côté, souvent due à un calcul rénal. Hydratation et consultation urgente recommandées.",
            "hépatite": "🩸 Inflammation du foie, souvent virale. Fatigue, jaunisse, nausées. Nécessite un suivi médical.",
            "pneumonie": "🫁 Infection pulmonaire sérieuse, accompagnée de fièvre, toux, et douleur thoracique. Consultez rapidement.",
            "zona": "🔥 Éruption douloureuse sur une partie du corps. Cause : réactivation du virus de la varicelle. Consultez dès les premiers signes.",
            "épilepsie": "⚡ Trouble neurologique provoquant des crises. Suivi médical strict indispensable.",
            "coupure profonde": "🩹 Nettoyez, appliquez une pression pour arrêter le saignement et consultez si elle est profonde ou large.",
            "hépatite C": "🧬 Infection virale du foie souvent silencieuse. Un dépistage est important pour un traitement efficace.",
            "phlébite": "🦵 Caillot dans une veine, souvent au mollet. Douleur, rougeur, chaleur. Consultez en urgence.",
            "gastro-entérite": "🤢 Diarrhée, vomissements, crampes. Repos, hydratation et alimentation légère sont essentiels.",
            "blessure musculaire": "💪 Repos, glace et compression. Évitez de forcer. Étirement progressif après quelques jours.",
            "tendinopathie": "🎾 Inflammation des tendons suite à un effort. Repos, glace et parfois kinésithérapie sont recommandés.",
            "œil rouge": "👁️ Allergie, infection ou fatigue ? Si douleur ou vision floue, consultez rapidement.",
            "perte d'odorat": "👃 Souvent liée à un virus comme la COVID-19. Hydratez-vous et surveillez les autres symptômes.",
            "brûlure au second degré": "🔥 Une brûlure au second degré provoque des cloques et des douleurs intenses. Refroidissez la zone, ne percez pas les cloques, et consultez si elle est étendue.",
            "gerçures": "💧 Les gerçures apparaissent souvent en hiver. Hydratez avec un baume à lèvres ou une crème réparatrice. Évitez le froid direct.",
            "mal de gorge": "👅 Un mal de gorge peut être viral ou bactérien. Buvez chaud, reposez-vous, et consultez si la douleur persiste plus de 3 jours.",
            "gencive douloureuse": "🦷 Une inflammation des gencives peut indiquer une gingivite. Brossez délicatement, utilisez un bain de bouche adapté, et consultez un dentiste.",
            "œdème": "🦵 Gonflement localisé ? Cela peut être lié à une rétention d’eau, un traumatisme ou une pathologie veineuse. Repos et jambes surélevées peuvent aider.",
            "sciatique": "💥 Douleur qui descend dans la jambe ? C’est peut-être une sciatique. Évitez de porter lourd et consultez un spécialiste.",
            "gerçure aux mains": "👐 Le froid ou les produits irritants peuvent assécher la peau. Utilisez une crème barrière hydratante plusieurs fois par jour.",
            "trachéite": "🗣️ Toux sèche, douleur à la gorge, voix rauque ? La trachéite est souvent virale. Hydratez-vous et évitez les atmosphères sèches.",
            "kyste sébacé": "🧴 Masse sous la peau, souvent bénigne. N’essayez pas de le percer vous-même. Consultez si douleur ou inflammation.",
            "arthrite": "🦴 Inflammation articulaire douloureuse, souvent chronique. Repos, traitement médicamenteux et kiné peuvent soulager.",
            "hémorroïdes": "🚽 Démangeaisons, douleur, saignement léger après les selles ? Les hémorroïdes sont fréquentes. Une alimentation riche en fibres et une bonne hygiène soulagent.",
            "crise d’angoisse": "😰 Palpitations, vertiges, souffle court ? Restez calme, respirez profondément, et essayez de vous isoler dans un lieu calme.",
            "baisse de vue soudaine": "👁️ Urgence ophtalmo. Consultez immédiatement si vous perdez partiellement ou totalement la vision.",
            "lésion cutanée": "🩹 Plaie, irritation ou bouton suspect ? Nettoyez à l’eau et au savon, puis observez. Si cela ne guérit pas en quelques jours, consultez.",
            "spasmes musculaires": "⚡ Contractures soudaines ? Hydratez-vous, étirez doucement le muscle, et évitez les efforts brutaux.",
            "trouble digestif": "🍽️ Ballonnements, nausées, diarrhées ? Évitez les plats lourds, buvez de l’eau, et reposez-vous.",
            "infection dentaire": "🦷 Douleur intense, gonflement ? Ne traînez pas : consultez un dentiste rapidement pour éviter un abcès.",
            "bruit de craquement dans les articulations": "🔊 C’est souvent bénin (crepitus), mais si douloureux ou associé à un blocage, consultez un spécialiste.",


        }
        # on parcourt le dict et on retourne dès qu'on trouve
        for symptome, reponse in reponses_medic.items():
            if symptome in question_clean:
                return reponse
        # ❗ Si aucun symptôme ne correspond ➔ message d'erreur fixe
        return "🩺 Désolé, je n'ai pas trouvé d'information médicale correspondante. Pouvez-vous préciser votre symptôme ?"

    
    # --- Bloc Découverte du Monde 100% local ---
    if any(kw in question_clean for kw in ["pays", "fait-moi découvrir", "découvre-moi", "exploration du monde", "découvrir un pays"]):
        try:
            pays_info = random.choice(pays_du_monde)  # On pioche un pays aléatoire
            message_bot = f"🌍 {pays_info}"
        except Exception:
            message_bot = "⚠️ Désolé, une erreur est survenue en essayant de découvrir un nouveau pays."
        DESTINATIONS = [
            {
                "pays": "Islande 🇮🇸",
                "faits": [
                    "Terre de volcans et de glaciers spectaculaires.",
                    "On y trouve des aurores boréales incroyables en hiver.",
                    "L'Islande possède plus de moutons que d’habitants.",
                    "Les Islandais croient beaucoup aux elfes et créatures magiques."
                ]
            },
            {
                "pays": "Japon 🇯🇵",
                "faits": [
                    "Pays des cerisiers en fleurs et des traditions ancestrales.",
                    "Tokyo est la plus grande métropole du monde.",
                    "Le mont Fuji est un symbole sacré.",
                    "Les Japonais fêtent la floraison des cerisiers avec le Hanami."
                ]
            },
            {
                "pays": "Italie 🇮🇹",
                "faits": [
                    "Berceau de la Renaissance.",
                    "La pizza est née à Naples.",
                    "Le Colisée de Rome est l'un des monuments les plus visités au monde.",
                    "Venise est célèbre pour ses canaux romantiques."
                ]
            },
            {
                "pays": "Brésil 🇧🇷",
                "faits": [
                    "Pays du carnaval le plus célèbre au monde, à Rio.",
                    "La forêt amazonienne couvre 60% du territoire.",
                    "Le football est une véritable religion.",
                    "Le Christ Rédempteur à Rio est une des 7 merveilles modernes."
                ]
            },
            {
                "pays": "Égypte 🇪🇬",
                "faits": [
                    "Pays des pharaons et des pyramides millénaires.",
                    "Le Nil est le plus long fleuve du monde.",
                    "Le Sphinx de Gizeh garde ses secrets depuis 4500 ans.",
                    "L’écriture hiéroglyphique est un héritage fascinant."
                ]
            }
            # (On pourra en rajouter plein d’autres ensuite 💪)
        ]
    
        destination = random.choice(DESTINATIONS)

        message_bot = f"🌍 Aujourd'hui, je te propose de découvrir **{destination['pays']}** :\n\n"
        for fait in destination["faits"]:
            message_bot += f"- {fait}\n"
        message_bot += "\nVeux-tu en découvrir un autre ? 😉"


    # ─── Bloc Géographie (capitales) ─────────────
    if any(kw in question_clean for kw in ["capitale", "où se trouve", "ville principale"]):
        # 1) On extrait le nom du pays
        match = re.search(r"(?:de la|de l'|du|de|des)\s+([a-zàâçéèêëîïôûùüÿñæœ' -]+)", question_clean)
        if match:
            pays_detecte = match.group(1).strip().lower()
        else:
            tokens = question_clean.split()
            pays_detecte = tokens[-1].strip(" ?!.,;").lower() if tokens else None
        capitales = {
                "france"           : "Paris", 
                "espagne"          : "Madrid",
                "italie"           : "Rome",
                "allemagne"        : "Berlin",
                "japon"            : "Tokyo",
                "japonaise"        : "Tokyo",
                "chine"            : "Pékin",
                "brésil"           : "Brasilia",
                "mexique"          : "Mexico",
                "canada"           : "Ottawa",
                "états-unis"       : "Washington",
                "usa"              : "Washington",
                "united states"    : "Washington",
                "inde"             : "New Delhi",
                "portugal"         : "Lisbonne",
                "royaume-uni"      : "Londres",
                "angleterre"       : "Londres",
                "argentine"        : "Buenos Aires",
                "maroc"            : "Rabat",
                "algérie"          : "Alger",
                "tunisie"          : "Tunis",
                "turquie"          : "Ankara",
                "russie"           : "Moscou",
                "russe"            : "Moscou",
                "australie"        : "Canberra",
                "corée du sud"     : "Séoul",
                "corée"            : "Séoul",
                "corée du nord"    : "Pyongyang",
                "vietnam"          : "Hanoï",
                "thailande"        : "Bangkok",
                "indonésie"        : "Jakarta",
                "malaisie"         : "Kuala Lumpur",
                "singapour"        : "Singapour",
                "philippines"      : "Manille",
                "pakistan"         : "Islamabad",
                "bangladesh"       : "Dacca",
                "sri lanka"        : "Colombo",
                "népal"            : "Katmandou",
                "iran"             : "Téhéran",
                "irak"             : "Bagdad",
                "syrie"            : "Damas",
                "liban"            : "Beyrouth",
                "jordanie"         : "Amman",
                "israël"           : "Jérusalem",
                "palestine"        : "Ramallah",
                "qatar"            : "Doha",
                "oman"             : "Mascate",
                "yémen"            : "Sanaa",
                "afghanistan"      : "Kaboul",
                "émirats arabes unis" : "Abou Dabi",
                "sénégal"          : "Dakar",
                "côte d'ivoire"    : "Yamoussoukro",
                "mali"             : "Bamako",
                "niger"            : "Niamey",
                "tchad"            : "N'Djaména",
                "burkina faso"     : "Ouagadougou",
                "congo"            : "Brazzaville",
                "rd congo"         : "Kinshasa",
                "kenya"            : "Nairobi",
                "éthiopie"         : "Addis-Abeba",
                "ghana"            : "Accra",
                "zambie"           : "Lusaka",
                "zimbabwe"         : "Harare",
                "soudan"           : "Khartoum",
                "botswana"         : "Gaborone",
                "namibie"          : "Windhoek",
                "madagascar"       : "Antananarivo",
                "mozambique"       : "Maputo",
                "angola"           : "Luanda",
                "libye"            : "Tripoli",
                "egypte"           : "Le Caire",
                "grèce"            : "Athènes",
                "pologne"          : "Varsovie",
                "ukraine"          : "Kyiv",
                "roumanie"         : "Bucarest",
                "bulgarie"         : "Sofia",
                "serbie"           : "Belgrade",
                "croatie"          : "Zagreb",
                "slovénie"         : "Ljubljana",
                "hongrie"          : "Budapest",
                "tchéquie"         : "Prague",
                "slovaquie"        : "Bratislava",
                "suède"            : "Stockholm",
                "norvège"          : "Oslo",
                "finlande"         : "Helsinki",
                "islande"          : "Reykjavik",
                "belgique"         : "Bruxelles",
                "pays-bas"         : "Amsterdam",
                "irlande"          : "Dublin",
                "suisse"           : "Berne",
                "colombie"         : "Bogota",
                "pérou"            : "Lima",
                "chili"            : "Santiago",
                "équateur"         : "Quito",
                "uruguay"          : "Montevideo",
                "paraguay"         : "Asuncion",
                "bolivie"          : "Sucre",
                "venezuela"        : "Caracas",
                "cuba"             : "La Havane",
                "haïti"            : "Port-au-Prince",
                "république dominicaine" : "Saint-Domingue",
                "nicaragua"        : "Managua",
                "honduras"         : "Tegucigalpa",
                "guatemala"        : "Guatemala",
                "salvador"         : "San Salvador",
                "panama"           : "Panama",
                "costarica"        : "San José",
                "jamaïque"         : "Kingston",
                "bahamas"          : "Nassau",
                "barbade"          : "Bridgetown",
                "trinité-et-tobago": "Port of Spain",
                "kazakhstan"       : "Noursoultan",
                "ouzbekistan"      : "Tachkent",
                "turkménistan"     : "Achgabat",
                "kirghizistan"     : "Bichkek",
                "mongolie"         : "Oulan-Bator",
                "géorgie"          : "Tbilissi",
                "arménie"          : "Erevan",
                "azerbaïdjan"      : "Bakou",
                "nouvelles-zélande": "Wellington",
                "fidji"            : "Suva",
                "palaos"           : "Ngerulmud",
                "papouasie-nouvelle-guinée" : "Port Moresby",
                "samoa"            : "Apia",
                "tonga"            : "Nukuʻalofa",
                "vanuatu"          : "Port-Vila",
                "micronésie"       : "Palikir",
                "marshall"         : "Majuro",
                "tuvalu"           : "Funafuti",
                "bhoutan"          : "Thimphou",
                "maldives"         : "Malé",
                "laos"             : "Vientiane",
                "cambodge"         : "Phnom Penh",
                "brunei"           : "Bandar Seri Begawan",
                "timor oriental"   : "Dili",
                "somalie"           : "Mogadiscio",
                "tanzanie"          : "Dodoma",
                "ouganda"           : "Kampala",
                "rwanda"            : "Kigali",
                "burundi"           : "Bujumbura",
                "malawi"            : "Lilongwe",
                "sierra leone"      : "Freetown",
                "libéria"           : "Monrovia",
                "guinée"            : "Conakry",
                "guinée-bissau"     : "Bissau",
                "guinée équatoriale": "Malabo",
                "gambie"            : "Banjul",
                "cap-vert"          : "Praia",
                "swaziland"         : "Mbabane",
                "lesotho"           : "Maseru",
                "bénin"             : "Porto-Novo",
                "togo"              : "Lomé",
                "gabon"             : "Libreville",
                "république centrafricaine": "Bangui",
                "eswatini"          : "Mbabane",  # anciennement Swaziland
                "suriname"          : "Paramaribo",
                "guyana"            : "Georgetown",
                "dominique"         : "Roseau",
                "sainte-lucie"      : "Castries",
                "saint-vincent-et-les-grenadines": "Kingstown",
                "saint-christophe-et-niévès"    : "Basseterre",
                "saint-marin"       : "Saint-Marin",
                "liechtenstein"     : "Vaduz",
                "andorre"           : "Andorre-la-Vieille",
                "vatican"           : "Vatican",
                "luxembourg"        : "Luxembourg",
                "monténégro"        : "Podgorica",
                "macédoine du nord" : "Skopje",
                "bosnie-herzégovine": "Sarajevo"

        }
        # 3) Réponse immédiate
        if pays_detecte and pays_detecte in capitales:
            return f"📌 La capitale de {pays_detecte.capitalize()} est {capitales[pays_detecte]}."
        else:
            return "🌍 Je ne connais pas encore la capitale de ce pays. Essayez un autre !"

    
    

    # --- Bloc Calcul (simple expression mathématique ou phrase) ---
    if not message_bot:
        question_calc = question_clean.replace(",", ".")
        question_calc = re.sub(r"^calcul(?:e)?\s*", "", question_calc)
        try:
            if any(op in question_calc for op in ["+", "-", "*", "/", "%", "**"]):
                try:
                    result = eval(question_calc)
                    message_bot = f"🧮 Le résultat est : **{round(result, 4)}**"
                except Exception:
                    pass
            if not message_bot:
                match = re.search(r"(?:combien font|combien|calcul(?:e)?|résultat de)\s*(.*)", question_calc)
                if match:
                    expression = match.group(1).strip()
                    result = eval(expression)
                    message_bot = f"🧮 Le résultat est : **{round(result, 4)}**"
        except:
            pass

        

    # --- Bloc Convertisseur intelligent ---
    if not message_bot and any(kw in question_clean for kw in ["convertis", "convertir", "combien vaut", "en dollars", "en euros", "en km", "en miles", "en mètres", "en celsius", "en fahrenheit"]):
        try:
            phrase = question_clean.replace(",", ".")
            match = re.search(r"(\d+(\.\d+)?)\s*([a-z]{3})\s*(en|to)\s*([a-z]{3})", phrase, re.IGNORECASE)
            if match:
                montant = float(match.group(1))
                from_cur = match.group(3).upper()
                to_cur = match.group(5).upper()
                url = f"https://v6.exchangerate-api.com/v6/dab2bba4f43a99445158d9ae/latest/{from_cur}"
                response = requests.get(url, timeout=10)
                data = response.json()
                if data.get("result") == "success":
                    taux = data["conversion_rates"].get(to_cur)
                    if taux:
                        result = montant * taux
                        message_bot = f"💱 {montant} {from_cur} = {round(result, 2)} {to_cur}"
                    else:
                        message_bot = "❌ Taux de conversion non disponible pour la devise demandée."
                else:
                    message_bot = "⚠️ Désolé, la conversion n’a pas pu être effectuée en raison d’un problème avec l’API. Veuillez réessayer plus tard."
            elif "km en miles" in phrase:
                match = re.search(r"(\d+(\.\d+)?)\s*km", phrase)
                if match:
                    km = float(match.group(1))
                    miles = km * 0.621371
                    message_bot = f"📏 {km} km = {round(miles, 2)} miles"
            elif "miles en km" in phrase:
                match = re.search(r"(\d+(\.\d+)?)\s*miles?", phrase)
                if match:
                    mi = float(match.group(1))
                    km = mi / 0.621371
                    message_bot = f"📏 {mi} miles = {round(km, 2)} km"
            elif "celsius en fahrenheit" in phrase:
                match = re.search(r"(\d+(\.\d+)?)\s*c", phrase)
                if match:
                    celsius = float(match.group(1))
                    fahrenheit = (celsius * 9/5) + 32
                    message_bot = f"🌡️ {celsius}°C = {round(fahrenheit, 2)}°F"
            elif "fahrenheit en celsius" in phrase:
                match = re.search(r"(\d+(\.\d+)?)\s*f", phrase)
                if match:
                    f_temp = float(match.group(1))
                    c_temp = (f_temp - 32) * 5/9
                    message_bot = f"🌡️ {f_temp}°F = {round(c_temp, 2)}°C"
        except Exception as e:
            message_bot = f"⚠️ Désolé, la conversion n’a pas pu être effectuée en raison d’un problème de connexion. Veuillez réessayer plus tard."

    # --- Analyse technique via "analyse <actif>" ---
    if not message_bot and question_clean.startswith("analyse "):
        nom_simple = question_clean[len("analyse "):].strip()
        nom_simple_norm = remove_accents(nom_simple.lower())

        correspondances = {
            "btc": "btc-usd", "bitcoin": "btc-usd",
            "eth": "eth-usd", "ethereum": "eth-usd",
            "aapl": "aapl", "apple": "aapl",
            "tsla": "tsla", "tesla": "tsla",
            "googl": "googl", "google": "googl",
            "msft": "msft", "microsoft": "msft",
            "amzn": "amzn", "amazon": "amzn",
            "nvda": "nvda", "nvidia": "nvda",
            "doge": "doge-usd", "dogecoin": "doge-usd",
            "ada": "ada-usd", "cardano": "ada-usd",
            "sol": "sol-usd", "solana": "sol-usd",
            "gold": "gc=F", "or": "gc=F",
            "sp500": "^gspc", "s&p": "^gspc",
            "cac": "^fchi", "cac40": "^fchi",
            "cl": "cl=F", "pétrole": "cl=F", "petrole": "cl=F",
            "si": "si=F", "argent": "si=F",
            "xrp": "xrp-usd", "ripple": "xrp-usd",
            "bnb": "bnb-usd", "matic": "matic-usd", "polygon": "matic-usd",
            "uni": "uni-usd", "uniswap": "uni-usd",
            "ndx": "^ndx", "nasdaq": "^ndx", "nasdaq100": "^ndx",
            "avax": "avax-usd", "avalanche": "avax-usd",
            "ltc": "ltc-usd", "litecoin": "ltc-usd",
            "cuivre": "hg=F", "copper": "hg=F",
            "dow": "^dji", "dji": "^dji", "dowjones": "^dji",
            "amd": "AMD (Advanced Micro Devices)",
            "ko": "Coca-Cola","meta": "Meta Platforms (Facebook)"
        }

        nom_ticker = correspondances.get(nom_simple_norm)
        if not nom_ticker:
            return f"🤔 Je ne connais pas encore **{nom_simple}**. Réessayez avec un autre actif."

        data_path = f"data/donnees_{nom_ticker}.csv"
        if not os.path.exists(data_path):
            return f"⚠️ Données manquantes pour **{nom_simple}**. Lancez le script d'entraînement pour les générer."

        try:
            df = pd.read_csv(data_path)
            df.columns = [col.capitalize() for col in df.columns]
            df = ajouter_indicateurs_techniques(df)
            analyse, suggestion = analyser_signaux_techniques(df)

            def generer_resume_signal(signaux):
                texte = ""
                signaux_str = " ".join(signaux).lower()
                if "survente" in signaux_str:
                    texte += "🔻 **Zone de survente détectée.**\n"
                if "surachat" in signaux_str:
                    texte += "🔺 **Zone de surachat détectée.**\n"
                if "haussier" in signaux_str:
                    texte += "📈 **Tendance haussière détectée.**\n"
                if "baissier" in signaux_str:
                    texte += "📉 **Tendance baissière détectée.**\n"
                if "faible" in signaux_str:
                    texte += "😴 **Tendance faible.**\n"
                return texte if texte else "ℹ️ Aucun signal fort détecté."

            resume = generer_resume_signal(analyse.split("\n") if analyse else [])
            return (
                f"📊 **Analyse pour {nom_simple.upper()}**\n\n"
                f"{analyse}\n\n"
                f"💬 **Résumé d'AVA :**\n{resume}\n\n"
                f"🤖 *Intuition d'AVA :* {suggestion}"
            )
        except Exception as e:
            return f"❌ Erreur lors de l'analyse de **{nom_simple}** : {e}"


    # --- Bloc Reconnaissance directe de tickers (orientation) ---
    tickers_detectables = [
        "btc", "bitcoin", "eth", "ethereum", "aapl", "apple", "tsla", "tesla", "googl", "google",
        "msft", "microsoft", "amzn", "amazon", "nvda", "nvidia", "doge", "dogecoin", "ada", "cardano",
        "sol", "solana", "gold", "or", "sp500", "s&p", "cac", "cac40", "cl", "pétrole", "petrole",
        "si", "argent", "xrp", "ripple", "bnb", "matic", "polygon", "uni", "uniswap", "ndx", "nasdaq",
        "nasdaq100", "avax", "ltc", "cuivre", "copper", "dji", "dowjones", "dow","ko", "amd","meta",
    ]

    if any(symb in question_clean for symb in tickers_detectables):
        ticker_simplifie = question_clean.replace(" ", "").replace("-", "")
        correspondance_simple = {
            "btc": "btc-usd", "bitcoin": "btc-usd", "eth": "eth-usd", "ethereum": "eth-usd",
            "aapl": "aapl", "apple": "aapl", "tsla": "tsla", "tesla": "tsla", "googl": "googl", "google": "googl",
            "msft": "msft", "microsoft": "msft", "amzn": "amzn", "amazon": "amzn", "nvda": "nvda", "nvidia": "nvda",
            "doge": "doge-usd", "dogecoin": "doge-usd", "ada": "ada-usd", "cardano": "ada-usd", "sol": "sol-usd", "solana": "sol-usd",
            "gold": "gc=F", "or": "gc=F", "sp500": "^gspc", "s&p": "^gspc", "cac": "^fchi", "cac40": "^fchi",
            "cl": "cl=F", "pétrole": "cl=F", "petrole": "cl=F", "si": "si=F", "argent": "si=F",
            "xrp": "xrp-usd", "ripple": "xrp-usd", "bnb": "bnb-usd", "matic": "matic-usd", "polygon": "matic-usd",
            "uni": "uni-usd", "uniswap": "uni-usd", "ndx": "^ndx", "nasdaq": "^ndx", "nasdaq100": "^ndx",
            "avax": "avax-usd", "ltc": "ltc-usd", "cuivre": "hg=F", "copper": "hg=F",
            "dow": "^dji", "dowjones": "^dji", "dji": "^dji","amd": "AMD (Advanced Micro Devices)",
            "ko": "Coca-Cola","meta": "Meta Platforms (Facebook)",
        }
        nom_ticker = correspondance_simple.get(ticker_simplifie)
        if nom_ticker:
            return f"🔍 Vous souhaitez en savoir plus sur **{nom_ticker.upper()}** ? Tapez `analyse {nom_ticker}` pour une analyse complète 📊"

        
    # --- Bloc Quiz de culture générale ---
    if not message_bot and any(mot in question_clean for mot in [
        "quiz", "quizz", "question", "culture générale", "pose-moi une question", "teste mes connaissances"
    ]):
        quizz_culture = [
            {"question": "🌍 Quelle est la capitale de l'Australie ?", "réponse": "canberra"},
            {"question": "🧪 Quel est l'élément chimique dont le symbole est O ?", "réponse": "oxygène"},
            {"question": "🖼️ Qui a peint la Joconde ?", "réponse": "léonard de vinci"},
            {"question": "📚 Combien y a-t-il de continents sur Terre ?", "réponse": "7"},
            {"question": "🚀 Quelle planète est la plus proche du Soleil ?", "réponse": "mercure"},
            {"question": "🇫🇷 Qui a écrit 'Les Misérables' ?", "réponse": "victor hugo"},
            {"question": "🎬 Quel film a remporté l'Oscar du meilleur film en 1998 avec 'Titanic' ?", "réponse": "titanic"},
            {"question": "🐘 Quel est le plus grand animal terrestre ?", "réponse": "éléphant"},
            {"question": "🎼 Quel musicien est surnommé 'le Roi de la Pop' ?", "réponse": "michael jackson"},
            {"question": "⚽ Quelle nation a remporté la Coupe du Monde 2018 ?", "réponse": "france"},
            {"question": "🗼 En quelle année a été inaugurée la Tour Eiffel ?", "réponse": "1889"},
            {"question": "🧬 Que signifie l'acronyme ADN ?", "réponse": "acide désoxyribonucléique"},
            {"question": "🎨 Quel peintre est célèbre pour avoir coupé une partie de son oreille ?", "réponse": "vincent van gogh"},
            {"question": "🇮🇹 Dans quel pays se trouve la ville de Venise ?", "réponse": "italie"},
            {"question": "🎭 Qui a écrit la pièce 'Hamlet' ?", "réponse": "william shakespeare"},
            {"question": "📐 Quel est le nom du triangle qui a deux côtés de même longueur ?", "réponse": "triangle isocèle"},
            {"question": "🔬 Quel scientifique a formulé la théorie de la relativité ?", "réponse": "albert einstein"},
            {"question": "🌋 Quel volcan italien est célèbre pour avoir détruit Pompéi ?", "réponse": "vesuve"},
            {"question": "🎤 Qui chante la chanson 'Someone Like You' ?", "réponse": "adele"},
            {"question": "🗳️ Quel est le régime politique de la France ?", "réponse": "république"}
        ]
        question_choisie = random.choice(quizz_culture)
        st.session_state["quiz_attendu"] = question_choisie["réponse"].lower()
        message_bot = f"🧠 **Quiz Culture G** :\n{question_choisie['question']}\n\nRépondez directement !"

    # --- Vérification de la réponse au quiz ---
    elif "quiz_attendu" in st.session_state and st.session_state["quiz_attendu"]:
        reponse_attendue = st.session_state["quiz_attendu"]
        if question_clean.lower() == reponse_attendue:
            message_bot = "✅ Bonne réponse ! Vous avez l’esprit affûté 🧠💪"
        else:
            message_bot = f"❌ Oops ! Ce n'était pas ça... La bonne réponse était **{reponse_attendue.capitalize()}**."
        st.session_state["quiz_attendu"] = ""

    # --- Bloc Recettes rapides ---
    recettes = [
        "🥪 **Sandwich thon-avocat** : pain complet, thon, avocat écrasé, citron, sel, poivre. 5 minutes chrono !",
        "🍝 **Pâtes à l’ail** : pâtes + ail émincé + huile d’olive + herbes. Simple, rapide, efficace.",
        "🍳 **Omelette fromage** : œufs battus, sel, poivre, fromage râpé. 5 minutes à la poêle !",
        "🥗 **Salade express** : tomates cerises, mozzarella, roquette, huile d’olive, vinaigre balsamique.",
        "🌯 **Wrap poulet-crudités** : galette + restes de poulet + salade + sauce yaourt.",
        "🥔 **Pommes de terre sautées** : en cubes, à la poêle avec ail et persil. Parfait avec des œufs !",
        "🍲 **Soupe express** : légumes surgelés mixés + cube bouillon + crème légère. Prête en 10 minutes.",
        "🍞 **Croque-monsieur rapide** : pain de mie, jambon, fromage, 5 min au grill ou à la poêle.",
        "🥒 **Tartines fraîcheur** : pain grillé, fromage frais, concombre, citron et herbes.",
        "🍚 **Riz sauté aux légumes** : reste de riz + légumes + œuf + sauce soja. Un wok express !",
        "🍗 **Poulet minute au curry** : dés de poulet + crème + curry + oignon, à la poêle en 10 min.",
        "🍳 **Œufs brouillés crémeux** : œufs + beurre + sel + poivre, cuisson douce pour onctuosité.",
        "🧄 **Pâtes ail-persil** : ail doré à la poêle, persil frais, huile d’olive, et hop sur les pâtes !",
        "🥑 **Toast avocat-œuf** : pain grillé + avocat écrasé + œuf au plat ou mollet.",
        "🌮 **Tacos express** : galette + steak haché ou haricots + tomate + salade + sauce.",
        "🥔 **Gratin express au micro-ondes** : pommes de terre en tranches fines + crème + fromage.",
        "🍅 **Tomates mozzarella** : tranches de tomates + mozzarella + basilic + huile d’olive. Simple et frais.",
        "🧀 **Quesadilla express** : deux tortillas + fromage + restes au choix + poêle 5 min chaque côté.",
        "🍳 **Mini shakshuka rapide** : tomates en dés + œufs + cumin dans une petite poêle. Un délice !",
        "🥣 **Bowl sucré express** : fromage blanc + fruits + flocons d’avoine + miel. Parfait au petit dej.",
        "🥕 **Bâtonnets carottes-concombre** : trempés dans du houmous ou une sauce yaourt. Frais et sain.",
        "🍞 **Pain perdu rapide** : tranches de pain + œuf + lait + sucre, à la poêle jusqu’à dorure.",
        "🍠 **Patate douce micro-ondes** : piquée à la fourchette, 7 min puissance max, à garnir à volonté.",
        "🥒 **Taboulé express** : semoule, tomate, menthe, citron, huile d’olive. Hydratation 5 min à l’eau chaude.",
        "🍌 **Banana pancakes** : 1 banane + 2 œufs, mélangés et cuits en petites galettes. Sans farine !",
        "🧈 **Wrap beurre de cacahuète-banane** : rapide, énergétique, parfait en collation !",
        "🍽️ **Assiette anti-gaspi** : reste de pâtes, légumes et un œuf, mélangés et poêlés façon wok !",
        "🍜 **Nouilles instant maison** : nouilles + bouillon + œuf + légumes râpés. Prêt en 7 minutes top chrono !",
        "🥓 **Œuf cocotte express** : œuf + crème + fromage dans un ramequin, 1 min au micro-ondes.",
        "🌽 **Galette de maïs rapide** : maïs + œuf + farine + épices, cuit à la poêle façon pancake salé.",
        "🍕 **Mini pizzas pain de mie** : pain de mie, sauce tomate, fromage, garniture au choix, 10 min au four.",
        "🍄 **Poêlée champignons ail-persil** : champignons frais, ail, persil, et huile d’olive. Simple & savoureux.",
        "🌯 **Wrap sucré pomme-cannelle** : pomme râpée, cannelle, un filet de miel, le tout roulé dans une galette.",
        "🍳 **Tortilla minute** : œufs battus + restes de légumes + fromage, à la poêle comme une omelette épaisse.",
        "🧀 **Boulettes express** : steak haché + chapelure + épices, façonnées et dorées en 5 min à la poêle.",
        "🍫 **Mug cake chocolat** : 4 ingrédients, 1 mug, 1 micro-ondes. Gâteau prêt en 1 minute !",
        "🥔 **Chips maison micro-ondes** : pommes de terre très fines + sel + micro-ondes 5 à 6 min. Ultra croustillant !"
    ]
     # 1) Demande initiale de recette
    if any(kw in question_clean for kw in [
        "recette", "idée recette", "une recette", "qu'est-ce qu'on mange", "on mange quoi"
    ]):
        choix = random.choice(recettes)
        st.session_state['derniere_recette'] = choix
        return f"🍽️ Voici une idée de recette rapide :\n\n{choix}"

    elif any(kw in question_clean for kw in ["encore une", "une autre", "autre recette"]):
        if 'derniere_recette' in st.session_state:
            choix = random.choice(recettes)
            st.session_state['derniere_recette'] = choix
            return f"🍽️ Voici une autre idée de recette :\n\n{choix}"
        else:
            return "⚠️ Je n'ai pas encore partagé de recette. Demandez-moi d'abord une recette !"
        
        # --- Bloc catch-all pour l'analyse technique ou réponse par défaut ---
    if not message_bot:
        # détection de salutations en anglais
        if any(phrase in question_clean for phrase in [
            "hello", "hi", "good morning", "good afternoon", "good evening"
        ]):
            message_bot = (
                "Bonjour ! Je suis là et prêt à vous aider. "
                "Comment puis-je vous assister aujourd'hui ?"
            )
        else:
            reponses_ava = [
                "Je suis là pour vous aider, mais j'ai besoin d'un peu plus de détails 🤖",
                "Je n'ai pas bien compris. Pouvez-vous reformuler, s'il vous plaît ?",
                "Ce sujet est encore un peu flou pour moi... Je peux parler d'analyse technique, "
                "de météo, d'actualités, et bien plus encore !",
                "Hmm... Ce n'est pas encore dans ma base de données. Essayez une autre "
                "formulation ou tapez 'analyse complète' pour un aperçu du marché 📊"
            ]
            message_bot = random.choice(reponses_ava)

    # Bloc de secours
    if not message_bot:
        message_bot = "🤔 Je n'ai pas d'information locale sur ce sujet pour le moment. Pose-moi une autre question ou demande-moi de te faire découvrir un pays, par exemple ! 🌍"

    return message_bot

    return None 
   

    
# ─── Boucle Streamlit Chat (TOUJOURS en bas) ───
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Affichage de l'historique du chat
for msg in st.session_state["messages"]:
    role = msg["role"]
    avatar = "assets/ava_logo.png" if role == "assistant" else None
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# Saisie utilisateur
prompt = st.chat_input("Pose ta question…")

if prompt:
    # Ajout du message utilisateur
    st.session_state["messages"].append({"role": "user", "content": prompt})

    # Calcul de la réponse
    réponse = trouver_reponse(prompt)

    if not isinstance(réponse, str) or not réponse.strip():
        réponse = "Hmm... je n’ai pas compris, vous pouvez reformuler ? 😊"

    # Détection automatique de la langue
    try:
        lang = detect(prompt)
    except:
        lang = "fr"

    if lang.lower() != "fr" and réponse.strip():
        try:
            tr = traduire_deepl(réponse, langue_cible=lang.upper())
            réponse = tr
        except:
            pass

    # Ajout de la réponse d'AVA dans l'historique
    st.session_state["messages"].append({"role": "assistant", "content": réponse})

    # Affichage immédiat du message d'AVA
    with st.chat_message("assistant", avatar="assets/ava_logo.png"):
        st.markdown(réponse)


