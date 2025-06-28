import streamlit as st
import base64
import os

# Fond noir global
st.markdown(
    """
    <style>
        body {
            background-color: #000000;
            color: white;
        }
        .stApp {
            background-color: #000000;
        }
        .css-1v0mbdj {
            background-color: #000000;
        }
        .title {
            font-size: 2em;
            font-weight: bold;
            color: #ffffff;
            margin-top: 20px;
        }
        .pay-button {
            background-color: #111111;
            border: 1px solid #444;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        .pay-button a {
            text-decoration: none;
            color: #00ffcc;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Affichage du logo redimensionné
image_path = "assets/oblivia_logo.png"
if os.path.exists(image_path):
    file_ = open(image_path, "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()

    st.markdown(
        f'<img src="data:image/png;base64,{data_url}" width="200" style="display: block; margin-left: auto; margin-right: auto;" />',
        unsafe_allow_html=True,
    )

st.markdown('<div class="title">💸 Soutiens Oblivia en 1 clic</div>', unsafe_allow_html=True)

# Les 4 liens avec titres originaux
links = [
    ("☕ Micro-soutien rebelle – 3€", "https://www.paypal.com/ncp/payment/9M55SN5BHKT3J"),
    ("⚔️ Soutien activiste – 10€", "https://www.paypal.com/ncp/payment/DLS75NFPTRTLN"),
    ("🧠 Accès prioritaire – 20€", "https://www.paypal.com/ncp/payment/AUM56GA3ZEKWS"),
    ("👑 Accès fondateur à vie – 50€", "https://www.paypal.com/ncp/payment/T2JWSF9YFXHN2"),
]

for title, url in links:
    st.markdown(
        f'<div class="pay-button"><a href="{url}" target="_blank">{title}</a></div>',
        unsafe_allow_html=True
    )

