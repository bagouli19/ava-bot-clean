import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

# Configuration de la page
st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers et noms d'affichage ---
tickers = [
    "aapl","tsla","googl","btc-usd","eth-usd","msft","amzn","nvda",
    "^gspc","doge-usd","ada-usd","sol-usd","gc=F","^fchi","xrp-usd",
    "bnb-usd","cl=F","si=F","matic-usd","uni-usd","^ndx","avax-usd",
    "ltc-usd","hg=F","^dji","amd","ko","meta"
]
nom_affichages = {
    "aapl":"Apple","tsla":"Tesla","googl":"Google","btc-usd":"Bitcoin",
    "eth-usd":"Ethereum","msft":"Microsoft","amzn":"Amazon","nvda":"NVIDIA",
    "^gspc":"S&P500","doge-usd":"Dogecoin","ada-usd":"Cardano","^fchi":"CAC 40",
    "sol-usd":"Solana","gc=F":"Or","xrp-usd":"XRP","bnb-usd":"BNB",
    "cl=F":"Pétrole brut","si=F":"Argent","matic-usd":"Polygon",
    "uni-usd":"Uniswap","^ndx":"Nasdaq 100","avax-usd":"Avalanche",
    "ltc-usd":"Litecoin","hg=F":"Cuivre","^dji":"Dow Jones","amd":"AMD",
    "ko":"Coca-Cola","meta":"Meta"
}

# --- Fonctions utilitaires ---
def generer_resume_signal(signaux):
    texte = ""
    s = " ".join(signaux).lower()
    if "survente" in s:
        texte += "🔻 Zone de survente détectée. L'actif pourrait être sous-évalué.\n"
    if "surachat" in s:
        texte += "🔺 Zone de surachat détectée. Attention à une possible correction.\n"
    if "haussier" in s:
        texte += "📈 Tendance haussière en cours. L'élan semble positif.\n"
    if "baissier" in s:
        texte += "📉 Tendance baissière détectée. Soyez prudent.\n"
    if "faible" in s:
        texte += "😴 Manque de tendance. Le marché est incertain.\n"
    return texte or "ℹ️ Aucun signal fort détecté pour l'instant."

def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd = df.filter(regex="^Macd($|[^a-z])", axis=1).iloc[:,0].iloc[-1]
    rsi = df.filter(regex="^Rsi", axis=1).iloc[:,0].iloc[-1]
    adx = df.filter(regex="^Adx", axis=1).iloc[:,0].iloc[-1]
    if macd > 0 and rsi < 70 and adx > 20:
        sl, tp = round(close*0.97,2), round(close*1.05,2)
        return f"📈 **Position acheteuse**  🛑 SL : {sl}  🎯 TP : {tp}"
    if macd < 0 and rsi > 30 and adx > 20:
        sl, tp = round(close*1.03,2), round(close*0.95,2)
        return f"📉 **Position vendeuse**  🛑 SL : {sl}  🎯 TP : {tp}"
    return "⚠️ Conditions insuffisantes pour prise de position."

# --- Sélection du ticker ---
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# --- Chargement et préparation des données ---
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Aucune donnée trouvée pour {nom_affichages[ticker]}")
    st.stop()

# 1) Lecture CSV puis sélection des 6 premières colonnes
df_raw = pd.read_csv(fichier)
if df_raw.shape[1] < 6:
    st.error("Le fichier doit contenir au moins 6 colonnes OHLCV.")
    st.stop()
df = df_raw.iloc[:, :6].copy()

# 2) Renommage explicite des colonnes
df.columns = ["Date","Open","High","Low","Close","Volume"]

# 3) Conversion des types et suppression des lignes incomplètes
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
for col in ["Open","High","Low","Close","Volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df.dropna(subset=["Date","Open","High","Low","Close","Volume"], inplace=True)

# 4) Ajout des indicateurs techniques
try:
    df = ajouter_indicateurs_techniques(df)
except Exception as e:
    st.error(f"Erreur indicateurs techniques : {e}")
    st.stop()

# 5) Analyse des signaux
try:
    analyse, suggestion = analyser_signaux_techniques(df)
except Exception as e:
    st.error(f"Erreur analyse technique : {e}")
    st.stop()

# --- Affichage des résultats ---
# Analyse brute
st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
st.markdown(analyse or "Pas de signaux.")

# Résumé
st.markdown(f"💬 **Résumé d'AVA :**\n{generer_resume_signal(analyse.split('\n'))}")
st.success(f"🤖 *Intuition d'AVA :* {suggestion}")

# Suggestion de position
st.subheader("📌 Suggestion de position")
st.markdown(suggerer_position_et_niveaux(df))

# Graphique en bougies japonaises
st.subheader("📈 Graphique en bougies japonaises")
fig = go.Figure(data=[go.Candlestick(
    x=df["Date"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    increasing_line_color="green",
    decreasing_line_color="red"
)])
fig.update_layout(xaxis_title="Date", yaxis_title="Prix", height=500, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# Actualités financières
st.subheader("🗞️ Actualités financières récentes")
flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
if flux.entries:
    for entry in flux.entries[:5]:
        st.markdown(f"🔹 [{entry.title}]({entry.link})", unsafe_allow_html=True)
else:
    st.info("Aucune actualité disponible.")

# Prédiction IA
st.subheader("📈 Prédiction IA (demain)")
fichier_pred = f"predictions/prediction_{ticker.lower().replace('-','').replace('^','').replace('=','')}.csv"
if os.path.exists(fichier_pred):
    pred = pd.read_csv(fichier_pred)["prediction"].iloc[-1]
    st.info("Hausse probable" if pred==1 else "Baisse probable")
else:
    st.warning("Aucune prédiction trouvée.")

# RSI actuel
st.subheader("📊 RSI actuel")
if "Rsi14" in df.columns:
    st.metric("RSI", round(df["Rsi14"].iloc[-1],2))

# Données brutes
st.subheader("📄 Données récentes")
st.dataframe(df.tail(10), use_container_width=True)


























