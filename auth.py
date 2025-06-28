import streamlit as st
import json

def verifier_acces():
    if "cle_validee" not in st.session_state:
        st.session_state.cle_validee = False
        st.session_state.est_admin = False

    if not st.session_state.cle_validee:
        # Charger les clés
        with open("cles_acces.json", "r") as f:
            data = json.load(f)
        cles_valides = data["cles_valides"]
        admin_key = data["admin_key"]

        st.title("🔐 Accès sécurisé Oblivia")
        cle = st.text_input("Entrez votre clé d'accès :", type="password")

        if st.button("Valider la clé"):
            if cle in cles_valides or cle == admin_key:
                st.session_state.cle_validee = True
                st.session_state.est_admin = (cle == admin_key)
                st.success("✅ Clé valide. Accès accordé.")
                st.experimental_rerun()
            else:
                st.error("❌ Clé invalide. Paiement requis pour obtenir une clé.")
        st.stop()