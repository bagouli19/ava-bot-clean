import streamlit as st
from PIL import Image
import json

# --- CONFIGURATION CLÉS D'ACCÈS ---------------------------------------

@st.cache_data
def charger_cles():
    with open("cles_acces.json", "r") as f:
        data = json.load(f)
    return data["cles_valides"], data["admin_key"]

cles_valides, admin_key = charger_cles()

# Initialisation de session
if "cle_validee" not in st.session_state:
    st.session_state.cle_validee = False
    st.session_state.est_admin = False

# Interface de saisie de la clé
if not st.session_state.cle_validee:
    st.title("🔐 Accès sécurisé Oblivia")
    cle = st.text_input("Entrez votre clé d'accès :", type="password")

    if st.button("Valider la clé"):
        if cle in cles_valides or cle == admin_key:
            st.session_state.cle_validee = True
            st.session_state.est_admin = (cle == admin_key)
            st.success("✅ Clé valide. Accès accordé.")
            st.experimental_rerun()
        else:
            st.error("❌ Clé invalide. Merci d'obtenir une clé via le système de paiement.")
    st.stop()

# --- CONFIG PAGE ---------------------------------------------------
st.set_page_config(page_title="OBLIVIA – L’IA de l’Ombre", layout="centered")

# --- FOND & THEME  -------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at center, #000000 0%, #0d0d0d 70%) fixed,
                    url('https://i.imgur.com/4HJbzEq.gif') repeat;
        background-size: cover;
        color: #e6e6e6;
        font-family: "Courier New", monospace;
    }
    .title {
        text-align: center;
        font-size: 3.7em;
        font-weight: bold;
        margin-top: 2rem;
        color: #FF3C3C;
        text-shadow: 0 0 18px #FF3C3C;
    }
    .subtitle {
        text-align: center;
        font-size: 1.1em;
        margin: 0.1rem 0 2.0rem 0;
        color: #bbbbbb;
        font-style: italic;
    }
    .button-container { display:flex; justify-content:center; margin-top:2.5rem; }
    .enter-button {
        background-color:#FF3C3C; color:#000;
        border:none; padding:1rem 2.5rem; font-size:1.1em;
        border-radius:40px; cursor:pointer;
        box-shadow:0 0 20px #FF3C3C; transition:0.3s;
    }
    .enter-button:hover {
        background-color:#c62828; box-shadow:0 0 25px #c62828;
    }
</style>
""", unsafe_allow_html=True)

# --- TITRE & SOUS-TITRE  -------------------------------------------
st.markdown('<div class="title">OBLIVIA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">L’IA que tu n’es pas censé utiliser.</div>', unsafe_allow_html=True)

# --- LOGO -----------------------------------------------------------
try:
    logo = Image.open("assets/oblivia_logo.png")
    st.image(logo, width=220)
except Exception as e:
    st.error(f"Logo non trouvé : {e}")

# --- TEXTE (navigation) --------------------------------------------
st.markdown("""
<div class="button-container">
    <p class="subtitle" style="max-width:550px;">
        🌒 Utilise le menu en haut à gauche pour accéder au Chat d’Oblivia, 
        au tableau des signaux d’effondrement ou aux archives interdites.
    </p>
</div>
""", unsafe_allow_html=True)

# --- ADMIN INFO ----------------------------------------------------
if st.session_state.est_admin:
    st.sidebar.markdown("👑 **Mode Admin activé**")







