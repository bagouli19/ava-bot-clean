import streamlit as st
import uuid
import json
import os

st.set_page_config(page_title="Acheter une clé Oblivia")

st.title("💸 Obtenir une clé d'accès à Oblivia")

st.markdown("""
Bienvenue dans la zone d'activation d'accès.  
Choisis une formule pour soutenir le projet et recevoir ta **clé personnelle d’accès** à Oblivia.

### 🔐 Formules disponibles :

- **💡 Accès 1 mois – 3 €**  
  👉 [Payer via PayPal](https://www.paypal.com/ncp/payment/XVF9KTNZPA7V4)

- **🧠 Accès 1 an – 20 €**  
  👉 [Payer via PayPal](https://www.paypal.com/ncp/payment/2XPN9ABLDGMY6)

- **👑 Accès à vie – 50 €**  
  👉 [Payer via PayPal](https://www.paypal.com/ncp/payment/64D59UV24KMZ8)
""")

st.markdown("---")
st.info("📩 Après avoir payé, clique sur le bouton ci-dessous pour générer ta clé unique.")

if st.button("🎟 Générer une clé maintenant"):
    # Génère une clé unique simple
    nouvelle_cle = str(uuid.uuid4())[:8].upper()

    # Charge les anciennes clés
    if os.path.exists("cles_acces.json"):
        with open("cles_acces.json", "r") as f:
            data = json.load(f)
    else:
        data = {"cles_valides": [], "admin_key": "ADMIN-ULTIMATE-KEY"}

    # Ajoute la nouvelle clé si elle n'existe pas déjà
    if nouvelle_cle not in data["cles_valides"]:
        data["cles_valides"].append(nouvelle_cle)
        with open("cles_acces.json", "w") as f:
            json.dump(data, f, indent=4)

    # Affiche la clé
    st.success(f"✅ Ta clé a été générée : `{nouvelle_cle}`")
    st.info("Copie-la et colle-la sur la page d’accueil pour débloquer Oblivia.")
