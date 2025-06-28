import streamlit as st
import base64
import os

st.set_page_config(page_title="Soutenir Oblivia", page_icon="💀", layout="centered")

# Style fond noir
st.markdown("""
    <style>
        .stApp {
            background-color: #000;
            color: #fff;
        }
        h1, h2, h3, h4, h5, h6, p {
            color: white;
        }
        .paypal-box {
            padding: 20px;
            border: 1px solid #444;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            background-color: #111;
        }
        a.button {
            background-color: #222;
            color: #00ffcc;
            padding: 12px 25px;
            text-decoration: none;
            font-weight: bold;
            border-radius: 8px;
            display: inline-block;
            margin-top: 10px;
        }
        a.button:hover {
            background-color: #00ffcc;
            color: black;
        }
    </style>
""", unsafe_allow_html=True)

# Affichage du logo
logo_path = "assets/oblivia_logo.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_data}" width="180"></div>', unsafe_allow_html=True)

st.markdown("## 💀 Financer Oblivia")

st.write("Tu veux soutenir un projet libre, obscur et sans filtre ? Choisis ton niveau de soutien :")

# Liens PayPal
soutiens = [
    ("☠️ Soutien Symbolique – 3 €", "https://www.paypal.com/ncp/payment/9M55SN5BHKT3J"),
    ("🧠 Soutien Mental – 10 €", "https://www.paypal.com/ncp/payment/DLS75NFPTRTLN"),
    ("👁️ Soutien Officiel – 20 €", "https://www.paypal.com/ncp/payment/AUM56GA3ZEKWS"),
    ("🕶️ Soutien Légendaire – 50 €", "https://www.paypal.com/ncp/payment/T2JWSF9YFXHN2"),
]

for titre, lien in soutiens:
    st.markdown(f"""
    <div class="paypal-box">
        <h3>{titre}</h3>
        <a class="button" href="{lien}" target="_blank">Soutenir</a>
    </div>
    """, unsafe_allow_html=True)