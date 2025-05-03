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

# Fonctions
def generer_resume_signal(signaux):
    texte = ""
    s = " ".join(signaux).lower()
    if "survente" in s: texte += "🔻 Zone de survente détectée.\n"
    if "surachat" in s: texte += "🔺 Zone de surachat détectée.\n"
    if "haussier" in s: texte += "📈 Tendance haussière détectée.\n"
    if "baissier" in s: texte += "📉 Tendance baissière détectée.\n"
    if not texte: texte = "ℹ️ Aucun signal fort détecté."
    return texte

def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd  = df.get("Macd", df.get("MacdHist", pd.Series())).iloc[-1]
    rsi   = df.get("Rsi14", df.get("Rsi", pd.Series())).iloc[-1]
    adx   = df.get("Adx14", df.get("Adx", pd.Series())).iloc[-1]
    if pd.isna(macd) or pd.isna(rsi) or pd.isna(adx):
        return "⚠️ Indicateurs manquants pour suggestion."
    if macd > 0 and rsi < 70 and adx > 20:
        sl, tp = round(close * 0.97,2), round(close * 1.05,2)
        return f"📈 Long  SL:{sl}  TP:{tp}"
    if macd < 0 and rsi > 30 and adx > 20:
        sl, tp = round(close * 1.03,2), round(close * 0.95,2)
        return f"📉 Short  SL:{sl}  TP:{tp}"
    return "⚠️ Conditions insuffisantes."

# Sélection du ticker
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# Lecture et préparation des données
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"Aucune donnée trouvée pour {nom_affichages[ticker]}")
    st.stop()

# 1) Lire CSV (sans parse_dates) et prendre les 6 premières colonnes
df_raw = pd.read_csv(fichier)
df = df_raw.iloc[:, :6].copy()

# 2) Renommer colonnes explicitement en Date/Open/.../Volume
df.columns = ["Date","Open","High","Low","Close","Volume"]
df.columns = ["Date","Open","High","Low","Close","Volume"]

# 3) Conversion des types
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
for col in ["Open","High","Low","Close","Volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df.dropna(subset=["Date","Open","High","Low","Close","Volume"], inplace=True)

# 4) Ajout des indicateurs
try:
    df = ajouter_indicateurs_techniques(df)
except Exception as e:
    st.error(f"Erreur indicateurs techniques : {e}")
    st.stop()

# 5) Analyse
try:
    analyse, suggestion = analyser_signaux_techniques(df)
except Exception as e:
    st.error(f"Erreur analyse technique : {e}")
    st.stop()

# Affichage
st.subheader(f"Analyse pour {nom_affichages[ticker]}")
st.markdown(analyse)

st.subheader("Résumé AVA")
st.markdown(generer_resume_signal(analyse.split("\n")))

st.subheader("Suggestion de position")
st.markdown(suggerer_position_et_niveaux(df))

st.subheader("Graphique en bougies japonaises")
fig = go.Figure(data=[go.Candlestick(
    x=df["Date"], open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"],
    increasing_line_color="green", decreasing_line_color="red"
)])
fig.update_layout(xaxis_title="Date", yaxis_title="Prix", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Actualités financières")
flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
if flux.entries:
    for entry in flux.entries[:5]: st.markdown(f"- [{entry.title}]({entry.link})", unsafe_allow_html=True)
else:
    st.info("Aucune actualité disponible.")

st.subheader("Prédiction IA")
file_pred = f"predictions/prediction_{ticker.lower().replace('-','').replace('^','').replace('=','')}.csv"
if os.path.exists(file_pred):
    pred = pd.read_csv(file_pred)["prediction"].iloc[-1]
    st.info("Hausse probable" if pred==1 else "Baisse probable")
else:
    st.warning("Aucune prédiction trouvée.")

st.subheader("RSI actuel")
if "Rsi14" in df.columns:
    st.metric("RSI", round(df["Rsi14"].iloc[-1],2))

st.subheader("Données récentes")
st.dataframe(df.tail(10), use_container_width=True)

























