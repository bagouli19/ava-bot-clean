import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

# Configuration de la page
st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers et affichages ---
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

# Sélection de l'actif
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# Chargement des données
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Aucune donnée trouvée pour {nom_affichages[ticker]}")
    st.stop()

# Lecture des 6 premières colonnes et renommage
try:
    df_raw = pd.read_csv(fichier)
    if df_raw.shape[1] < 6:
        raise ValueError("Le fichier doit contenir au moins 6 colonnes OHLCV.")
    df = df_raw.iloc[:, :6].copy()
    df.columns = ["Date","Open","High","Low","Close","Volume"]
except Exception as e:
    st.error(f"Erreur lecture/renommage CSV : {e}")
    st.stop()

# Conversion des types
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
for c in ["Open","High","Low","Close","Volume"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df.dropna(subset=["Date","Open","High","Low","Close","Volume"], inplace=True)

# Debug initial
st.write("Données préparées (5 premières lignes) :")
st.dataframe(df.head())

# Ajout des indicateurs techniques
try:
    df = ajouter_indicateurs_techniques(df)
    df.columns = df.columns.str.title()
except Exception as e:
    st.error(f"Erreur indicateurs techniques : {e}")
    st.stop()

# Debug colonnes après indicateurs
st.write("Colonnes après indicateurs :", df.columns.tolist())

# Analyse des signaux
try:
    analyse, suggestion = analyser_signaux_techniques(df)
except Exception as e:
    st.error(f"Erreur analyse technique : {e}")
    st.stop()

# Affichage des résultats
st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
st.markdown(analyse or "Pas de signaux.")

# Résumé
from typing import List
def generer_resume_signal(signaux: List[str]) -> str:
    texte = ""
    for s in signaux:
        lower = s.lower()
        if "survente" in lower:
            texte += "🔻 Zone de survente détectée.\n"
        if "surachat" in lower:
            texte += "🔺 Zone de surachat détectée.\n"
        if "haussier" in lower:
            texte += "📈 Tendance haussière.\n"
        if "baissier" in lower:
            texte += "📉 Tendance baissière.\n"
        if "faible" in lower:
            texte += "😴 Marché sans tendance.\n"
    return texte or "ℹ️ Aucun signal fort détecté."

st.markdown(f"💬 **Résumé d'AVA :**\n{generer_resume_signal(analyse.splitlines())}")
st.success(f"🤖 *Intuition d'AVA :* {suggestion}")

# Suggestion de position
def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd = df.get("Macd", df.get("MacdHist"))
    rsi  = df.get("Rsi14", df.get("Rsi"))
    adx  = df.get("Adx14", df.get("Adx"))
    if macd is None or rsi is None or adx is None:
        return "⚠️ Indicateurs manquants."
    macd_val, rsi_val, adx_val = macd.iloc[-1], rsi.iloc[-1], adx.iloc[-1]
    if macd_val > 0 and rsi_val < 70 and adx_val > 20:
        sl, tp = round(close*0.97,2), round(close*1.05,2)
        return f"📈 Position acheteuse  SL:{sl}  TP:{tp}"
    if macd_val < 0 and rsi_val > 30 and adx_val > 20:
        sl, tp = round(close*1.03,2), round(close*0.95,2)
        return f"📉 Position vendeuse  SL:{sl}  TP:{tp}"
    return "⚠️ Conditions insuffisantes."

st.subheader("📌 Suggestion de position")
st.markdown(suggerer_position_et_niveaux(df))

# Candlestick plot
st.subheader("📈 Graphique en bougies japonaises")
df_plot = df.sort_values("Date")
# Debug df_plot head
st.write("Données pour graphique bougies (5 premières lignes):")
st.dataframe(df_plot[["Date","Open","High","Low","Close"]].head())
fig = go.Figure(data=[go.Candlestick(
    x=df_plot["Date"], open=df_plot["Open"], high=df_plot["High"],
    low=df_plot["Low"], close=df_plot["Close"],
    increasing_line_color="green", decreasing_line_color="red"
)])
fig.update_layout(
    xaxis_title="Date", yaxis_title="Prix", height=500,
    xaxis_rangeslider_visible=False
)
fig.update_xaxes(type='date')
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
elif "Rsi" in df.columns:
    st.metric("RSI", round(df["Rsi"].iloc[-1],2))

# Données brutes
st.subheader("📄 Données récentes")
st.dataframe(df.tail(10), use_container_width=True)










