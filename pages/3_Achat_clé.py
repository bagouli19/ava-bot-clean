import streamlit as st
import uuid
from datetime import datetime, timedelta
import os 
import json

formule = st.selectbox("Choisis la formule que tu as payée :", [
    "Accès 1 mois – 3 €",
    "Accès 1 an – 20 €",
    "Accès à vie – 50 €"
])

if st.button("🎟 Générer une clé maintenant"):
    nouvelle_cle = str(uuid.uuid4())[:8].upper()

    # Calcul de l'expiration
    if "mois" in formule:
        expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    elif "an" in formule:
        expiration = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    else:
        expiration = "illimite"

    # Charger les données
    if os.path.exists("cles_acces.json"):
        with open("cles_acces.json", "r") as f:
            data = json.load(f)
    else:
        data = {"cles": [], "admin_key": "ADMIN-ULTIMATE-KEY"}

    # Ajouter la nouvelle clé
    data["cles"].append({
        "cle": nouvelle_cle,
        "expiration": expiration
    })

    with open("cles_acces.json", "w") as f:
        json.dump(data, f, indent=4)

    st.success(f"✅ Clé générée : `{nouvelle_cle}`")
    st.info(f"Valable jusqu’au : **{expiration}** (copie-la sur la page d’accueil)")

