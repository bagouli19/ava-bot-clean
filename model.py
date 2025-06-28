from sentence_transformers import SentenceTransformer
import streamlit as st

@st.cache_resource
def load_semantic_model():
    try:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return model
    except Exception as e:
        st.error(f"⚠️ Impossible de charger le modèle sémantique : {e}")
        return None

# Chargement du modèle
model_semantic = load_semantic_model()
