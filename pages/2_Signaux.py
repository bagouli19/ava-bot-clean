import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

# Configuration de la page
st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# Tickers et leurs noms
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

# Fonctions de résumé et de suggestion de position
def generer_resume_signal(signaux):
    texte = ""
    s = " ".join(signaux).lower()
    if "survente" in s:  texte += "🔻 **Survente détectée.**\n"
    if "surachat" in s:  texte += "🔺 **Surachat détecté.**\n"
    if "haussier" in s:  texte += "📈 **Tendance haussière.**\n"
    if "baissier" in s:  texte += "📉 **Tendance baissière.**\n"
    if "faible" in s:    texte += "😴 **Marché sans tendance.**\n"
    return texte or "ℹ️ Aucun signal fort."

def suggerer_position_et_niveaux(df):
    # Recherche dynamique des colonnes d'indicateurs
    cols = {col.lower(): col for col in df.columns}
    macd_col = cols.get('macd') or next((c for c in df.columns if c.lower().startswith('macd') and 'signal' not in c.lower()), None)
    rsi_col  = cols.get('rsi14') or cols.get('rsi') or next((c for c in df.columns if c.lower().startswith('rsi')), None)
    adx_col  = cols.get('adx14') or cols.get('adx') or next((c for c in df.columns if c.lower().startswith('adx')), None)
    if not all([macd_col, rsi_col, adx_col]):
        return "⚠️ Indicateurs manquants pour suggestion de position."
    close = df['Close'].iat[-1]
    macd  = df[macd_col].iat[-1]
    rsi   = df[rsi_col].iat[-1]
    adx   = df[adx_col].iat[-1]
    if macd > 0 and rsi < 70 and adx > 20:
        sl, tp = round(close * 0.97,2), round(close * 1.05,2)
        return f"📈 **Long**  🛑 SL : {sl}  🎯 TP : {tp}"
    if macd < 0 and rsi > 30 and adx > 20:
        sl, tp = round(close * 1.03,2), round(close * 0.95,2)
        return f"📉 **Short**  🛑 SL : {sl}  🎯 TP : {tp}"
    return "⚠️ Conditions insuffisantes."

# Sélection de l'actif
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# Lecture & préparation des données
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Pas de données pour {nom_affichages[ticker]}." )
    st.stop()

# 1) Lecture du CSV complet
#    On renomme dynamiquement les colonnes OHLCV par leur nom (ignore la position)
df = pd.read_csv(fichier, dayfirst=True)
# Mapping des colonnes en base de leur nom (insensible à la casse)
mapping = {}
for orig in df.columns:
    low = orig.strip().lower()
    if low in ["date", "datetime"]:
        mapping[orig] = "Date"
    elif low in ["open", "open_price"]:
        mapping[orig] = "Open"
    elif low in ["high", "high_price"]:
        mapping[orig] = "High"
    elif low in ["low", "low_price"]:
        mapping[orig] = "Low"
    elif low in ["close", "close_price", "adj close", "adjclose"]:
        mapping[orig] = "Close"
    elif low == "volume":
        mapping[orig] = "Volume"
# On applique le renommage
if mapping:
    df = df.rename(columns=mapping)
# 2) On garde uniquement les colonnes indispensables
required = ["Date","Open","High","Low","Close","Volume"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Colonnes OHLCV manquantes : {missing}")
    st.stop()
# 3) Conversion des types et purge des lignes incomplètes
df = df[required].copy()
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
for c in ["Open","High","Low","Close","Volume"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df.dropna(subset=["Date","Open","High","Low","Close","Volume"], inplace=True)

# 4) Ajout des indicateurs
from analyse_technique import ajouter_indicateurs_techniques
try:
    df = ajouter_indicateurs_techniques(df)
except Exception as e:
    st.error(f"Erreur indicateurs techniques : {e}")
    st.stop()

# 5) Suppression d’éventuels doublons de colonnes, sans renommer
#    On conserve les indices des colonnes existantes pour garder les bons noms.
df = df.loc[:, ~df.columns.duplicated()]

# 6) Analyse & affichages
try:
    analyse, suggestion = analyser_signaux_techniques(df)

    # Analyse
    st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
    st.markdown(analyse or "Pas de signaux.")

    # Résumé
    signaux_list = analyse.split("\n") if analyse else []
    st.markdown(f"💬 **Résumé d'AVA :**\n{generer_resume_signal(signaux_list)}")
    st.success(f"🤖 *Intuition AVA :* {suggestion}")

    # Suggestion de position
    st.subheader("📌 Suggestion de position")
    st.markdown(suggerer_position_et_niveaux(df))

        # Candlestick
    st.subheader("📈 Graphique en bougies japonaises")
    # Utilisation des colonnes garanties
    fig = go.Figure(data=[go.Candlestick(
        x=df["Date"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        increasing_line_color="green",
        decreasing_line_color="red"
    )])
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Prix",
        height=500,
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Actualités
    st.subheader("🗞️ Actualités financières récentes")
    flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
    if flux.entries:
        for e in flux.entries[:5]: st.markdown(f"🔹 [{e.title}]({e.link})", unsafe_allow_html=True)
    else: st.info("Aucune actualité récupérée.")

    # Prédiction IA
    pred_file = (
        f"predictions/prediction_{ticker.lower().replace('-', '').replace('^','').replace('=','')}.csv"
    )
    if os.path.exists(pred_file):
        pred = pd.read_csv(pred_file)["prediction"].iat[-1]
        st.subheader("📈 Prédiction IA (demain)")
        st.info("Hausse probable" if pred==1 else "Baisse probable")
    else:
        st.warning("Aucune prédiction trouvée.")

    # RSI
    if "Rsi14" in df.columns:
        st.subheader("📊 RSI actuel")
        st.metric("RSI", round(df["Rsi14"].iat[-1],2))

    # Données brutes
    st.subheader("📄 Données récentes")
    st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Erreur pendant l'analyse : {e}")





















