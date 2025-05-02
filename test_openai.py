import openai
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

def repondre_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es une IA sympathique et précise."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur : {e}"

print(repondre_openai("Donne-moi une idée de projet original avec une IA."))

