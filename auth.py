import streamlit as st
import json
from datetime import datetime

def verifier_acces():
    if "cle_validee" not in st.session_state:
        st.session_state.cle_validee = False
        st.session_state.est_admin = False

    if not st.session_state.cle_validee:
        with open("cles_acces.json", "r") as f:
            data = json.load(f)

        admin_key = data["admin_key"]
        liste_cles = data["cles"]

        st.title("🔐 Accès sécurisé Oblivia")
        cle = st.text_input("Entrez votre clé d'accès :", type="password")

        if st.button("Valider la clé"):
            maintenant = datetime.now().date()
            for entree in liste_cles:
                if cle == entree["cle"]:
                    if entree["expiration"] == "illimite":
                        st.session_state.cle_validee = True
                        st.success("✅ Accès illimité accordé.")
                        return
                    else:
                        exp = datetime.strptime(entree["expiration"], "%Y-%m-%d").date()
                        if maintenant <= exp:
                            st.session_state.cle_validee = True
                            st.success(f"✅ Clé valide jusqu’au {exp}")
                            return
                        else:
                            st.error("❌ Clé expirée.")
                            st.stop()

            if cle == admin_key:
                st.session_state.cle_validee = True
                st.session_state.est_admin = True
                st.success("✅ Clé administrateur reconnue.")
                return

            st.error("❌ Clé invalide.")
        st.stop()