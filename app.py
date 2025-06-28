import streamlit as st
from PIL import Image

# --- Config page ---------------------------------------------------
st.set_page_config(page_title="OBLIVIA – L’IA de l’Ombre", layout="centered")

# --- FOND & THEME  -------------------------------------------------
st.markdown("""
<style>
    /* Dégradé radial + légère animation glitch en fond */
    .stApp {
        background: radial-gradient(circle at center, #000000 0%, #0d0d0d 70%) fixed,
                    url('https://i.imgur.com/4HJbzEq.gif') repeat;
        background-size: cover;
        color: #e6e6e6;
        font-family: "Courier New", monospace;
    }

    /* TITRE */
    .title {
        text-align: center;
        font-size: 3.7em;
        font-weight: bold;
        margin-top: 2rem;
        color: #FF3C3C;
        text-shadow: 0 0 18px #FF3C3C;
    }

    /* SOUS-TITRE */
    .subtitle {
        text-align: center;
        font-size: 1.1em;
        margin: 0.1rem 0 2.0rem 0;
        color: #bbbbbb;
        font-style: italic;
    }

    /* BOUTON */
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





