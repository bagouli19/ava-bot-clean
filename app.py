import streamlit as st
from PIL import Image
from streamlit.components.v1 import html

st.set_page_config(page_title="Bienvenue sur AVA", layout="centered")

# --- CSS pour fond et style AVA ---
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f0f0f 0%, #1c1c1c 100%);
            color: #ffffff;
        }
        .title {
            text-align: center;
            font-size: 3.5em;
            font-weight: bold;
            margin-top: 2rem;
            color: #00FFFF;
            text-shadow: 0 0 15px #00FFFF;
        }
        .subtitle {
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 1.5rem;
            color: #d0d0d0;
        }
        .logo-container {
            display: flex;
            justify-content: center;
            margin: 2rem 0;
        }
        .button-container {
            display: flex;
            justify-content: center;
            margin-top: 2rem;
        }
        .enter-button {
            background-color: #00FFFF;
            color: #000000;
            border: none;
            padding: 1rem 2.5rem;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 0 20px #00FFFF;
            transition: 0.3s ease;
        }
        .enter-button:hover {
            background-color: #00cccc;
            box-shadow: 0 0 25px #00cccc;
        }
    </style>
""", unsafe_allow_html=True)

# --- Titre et sous-titre ---
st.markdown('<div class="title">Bienvenue sur AVA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Votre assistante boursière, météo et actualités 24h/24 — toujours connectée, toujours prête 🤖</div>', unsafe_allow_html=True)

# --- Logo centré ---
try:
    logo = Image.open("assets/ava_logo.png")
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(logo, width=200)
    st.markdown('</div>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Logo non trouvé : {e}")
    
# --- Mention spéciale "Nyx veille" ---
st.markdown("""
<div style='text-align: center; margin-top: -1rem; margin-bottom: 2rem;'>
    <p style='font-size: 1.1em; color: #888;'>🌙 Nyx veille sur AVA et Teddy depuis les étoiles...</p>
</div>
""", unsafe_allow_html=True)

# --- Bouton vers Dashboard ---
st.markdown("""
<div class="button-container">
    <p style="text-align:center; color:#aaa; font-size: 1.1em;">
        🌐 Utilisez le menu en haut à gauche pour accéder au Dashboard, Signaux ou Chat AVA.
    </p>
</div>
""", unsafe_allow_html=True)





