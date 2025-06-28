import streamlit as st
import json
import os

st.set_page_config(page_title="OBLIVIA – Accès", page_icon="💀")

st.title("🔮 Rejoins la Zone Fantôme – OBLIVIA")

st.markdown("""
Bienvenue, **Initié**.  
Choisis ton niveau de soutien pour obtenir une **clé d'accès** au réseau clandestin OBLIVIA :

---

### 🧩 Formules d’accès

💶 **3 € — Accès "Spectre"**  
*Tu observes les ombres, mais ne fais qu'effleurer la vérité.*  
👉 [Activer l'accès Spectre](https://www.paypal.com/ncp/payment/9M55SN5BHKT3J)

💠 **10 € — Accès "Cipher"**  
*Un signal discret, une clé silencieuse. Tu avances masqué.*  
👉 [Activer l'accès Cipher](https://www.paypal.com/ncp/payment/DLS75NFPTRTLN)

🔐 **20 € — Accès "Phantom"**  
*Tu effaces tes traces. OBLIVIA t’ouvre ses portes les plus sombres.*  
👉 [Activer l'accès Phantom](https://www.paypal.com/ncp/payment/AUM56GA3ZEKWS)

👁 **50 € — Accès "Doppelgänger"**  
*Tu deviens l’ombre, tu deviens l’IA. Accès total. À vie.*  
👉 [Activer l'accès Doppelgänger](https://www.paypal.com/ncp/payment/T2JWSF9YFXHN2)

---
""")

st.markdown("### 🎟️ Récupérer ta clé secrète")

email = st.text_input("🔍 Entre l’email utilisé lors de ton paiement PayPal :").strip().lower()

if st.button("🔓 Vérifier et récupérer la clé"):
    if not os.path.exists("cles_acces.json"):
        st.error("❌ Aucun paiement encore enregistré.")
    else:
        with open("cles_acces.json", "r") as f:
            data = json.load(f)

        cles_trouvees = [
            cle for cle in data.get("cles", [])
            if cle.get("email", "").lower() == email
        ]

        if cles_trouvees:
            for cle in cles_trouvees:
                st.success(f"🗝️ Clé trouvée : `{cle['cle']}` — expire le : **{cle['expiration']}**")
        else:
            st.warning("⚠️ Aucun accès trouvé pour cet email. Vérifie bien que le paiement est passé.")


