import streamlit as st
import base64
import os

st.set_page_config(page_title="Oblivia", page_icon="👁️", layout="wide")

# Appliquer un fond noir + style texte
st.markdown("""
    <style>
        .stApp {
            background-color: #000000;
            color: white;
        }
        h1, h2, h3, h4, h5, h6, p {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Afficher le logo centré, redimensionné
image_path = "assets/oblivia_logo.png"
if os.path.exists(image_path):
    with open(image_path, "rb") as file_:
        contents = file_.read()
        data_url = base64.b64encode(contents).decode("utf-8")
    st.markdown(
        f'<div style="text-align: center;"><img src="data:image/png;base64,{data_url}" width="200"/></div>',
        unsafe_allow_html=True
    )

# Texte principal
st.markdown("""
# 👁️ Oblivia — Menu Principal

Bienvenue dans l'interface Oblivia. Utilise le menu à gauche pour naviguer entre les pages :
- Génération de clé  
- Vérification d'accès  
- Soutien & financement
""")


