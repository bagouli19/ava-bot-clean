import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

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
    "ltc-usd":"Litecoin","hg=F":"Cuivre","^dji":"Dow Jones",
    "amd":"AMD","ko":"Coca-Cola","meta":"Meta"
}

def generer_resume_signal(signaux):
    texte = ""
    signaux_str = " ".join(signaux).lower()
    if "survente" in signaux_str:
        texte += "🔻 **Zone de survente détectée.** L'actif pourrait être sous-évalué.\n"
    if "surachat" in signaux_str:
        texte += "🔺 **Zone de surachat détectée.** Attention à une possible correction.\n"
    if "haussier" in signaux_str:
        texte += "📈 **Tendance haussière en cours.** Les indicateurs suggèrent un élan positif.\n"
    if "baissier" in signaux_str:
        texte += "📉 **Tendance baissière détectée.** Prudence sur les mouvements actuels.\n"
    if "faible" in signaux_str:
        texte += "😴 **Manque de tendance.** Le marché semble indécis.\n"
    if not texte:
        texte = "ℹ️ Aucun signal fort détecté pour l'instant. Restez à l'affût."
    return texte

def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd  = df["Macd"].iloc[-1]
    rsi   = df["Rsi"].iloc[-1]
    adx   = df["Adx"].iloc[-1]
    if macd > 0 and rsi < 70 and adx > 20:
        sl, tp = round(close * 0.97, 2), round(close * 1.05, 2)
        return f"📈 **Long**  🛑 SL : {sl}  🎯 TP : {tp}"
    elif macd < 0 and rsi > 30 and adx > 20:
        sl, tp = round(close * 1.03, 2), round(close * 0.95, 2)
        return f"📉 **Short**  🛑 SL : {sl}  🎯 TP : {tp}"
    else:
        return "⚠️ Conditions insuffisantes pour prise de position."

# --- Sélection du ticker ---
ticker = st.selectbox(
    "Choisissez un actif :",
    options=tickers,
    format_func=lambda x: nom_affichages[x]
)

# --- Chargement du CSV ---
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Aucune donnée pour {nom_affichages[ticker]}.")
    st.stop()

df = pd.read_csv(fichier)

# --- 1) Uniformiser tous les noms de colonnes en minuscules et sans espaces ---
df.columns = df.columns.str.strip().str.lower()

# --- 2) Déterminer le suffixe ticker pour repérer les colonnes spécifiques ---
suffix = ticker.lower().replace("^","").replace("=","").replace("-","_")

# --- 3) Mapper date_, open_, high_, low_, close_, volume_ spécifiques vers génériques ---
mapping = {}
for base in ["date","open","high","low","close","volume"]:
    # si la colonne générique existe déjà, on la garde
    if base in df.columns:
        mapping[base] = base
    # sinon si la colonne ticker-spécifique existe, on la renomme
    tcol = f"{base}_{suffix}"
    if tcol in df.columns:
        mapping[tcol] = base

# --- 4) Appliquer le mapping et supprimer les doublons éventuels ---
df = df.rename(columns=mapping)
df = df.loc[:, ~df.columns.duplicated()]

# --- 5) Vérifier que l'on dispose bien de date/open/high/low/close/volume ---
required = ["date","open","high","low","close","volume"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Colonnes manquantes : {missing}")
    st.stop()

# --- 6) Conversion des types ---
df = df.rename(columns={c: c.title() for c in required})
df["Date"]   = pd.to_datetime(df["Date"])
for col in ["Open","High","Low","Close","Volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["Open","High","Low","Close","Volume"])

# --- 7) Ajout des indicateurs techniques ---
df = ajouter_indicateurs_techniques(df)

# --- 8) Renommage des indicateurs en Title Case ---
df = df.rename(columns={
    "sma":   "Sma",
    "ema":   "Ema",
    "rsi":   "Rsi",
    "macd":  "Macd",
    "adx":   "Adx",
    "cci":   "Cci",
    "willr": "Willr"
})
df = df.loc[:, ~df.columns.duplicated()]

# --- 9) Analyse, affichages et graphiques ---
try:
    analyse, suggestion = analyser_signaux_techniques(df)

    # Analyse technique brute
    st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
    st.markdown(analyse)

    # Résumé AVA
    signaux_list = analyse.split("\n") if analyse else []
    resume = generer_resume_signal(signaux_list)
    st.markdown(f"💬 **Résumé d'AVA :**\n{resume}")
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
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Prix",
        height=500,
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Actualités financières
    st.subheader("🗞️ Actualités financières récentes")
    flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
    if flux.entries:
        for entry in flux.entries[:5]:
            st.markdown(f"🔹 [{entry.title}]({entry.link})", unsafe_allow_html=True)
    else:
        st.info("Aucune actualité récupérée.")

    # Prédiction IA
    fichier_pred = (
        f"predictions/prediction_"
        f"{ticker.lower().replace('-', '').replace('^','').replace('=','')}.csv"
    )
    if os.path.exists(fichier_pred):
        pred = pd.read_csv(fichier_pred)["prediction"].iloc[-1]
        st.subheader("📈 Prédiction IA (demain)")
        st.info("Hausse probable" if pred == 1 else "Baisse probable")
    else:
        st.warning("Aucune prédiction trouvée.")

    # RSI actuel
    if "Rsi" in df.columns:
        st.subheader("📊 RSI actuel")
        st.metric("RSI", round(df["Rsi"].iloc[-1], 2))

    # Données brutes
    st.subheader("📄 Données récentes")
    st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue pendant l'analyse : {e}")











