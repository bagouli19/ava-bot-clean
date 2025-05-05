import openai
import streamlit as st

def repondre_openai(prompt: str) -> str:
    try:
        openai.api_key = st.secrets["api_key"]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es une intelligence vive, chaleureuse et utile."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"❌ Erreur GPT-3.5 : {e}"