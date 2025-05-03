import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

# Configuration page
st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# Tickers et affichages
tickers = ["aapl","tsla","googl","btc-usd","eth-usd","msft","amzn","nvda",
           "^gspc","doge-usd","ada-usd","sol-usd","gc=F","^fchi","xrp-usd",
           "bnb-usd","cl=F","si=F","matic-usd","uni-usd","^ndx","avax-usd",
           "ltc-usd","hg=F","^dji","amd","ko","meta"]
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

# Fonctions auxiliaires
def generer_resume_signal(signaux):
    texte, s = "", " ".join(signaux).lower()
    if "survente" in s: texte += "🔻 Zone de survente détectée.\n"
    if "surachat" in s: texte += "🔺 Zone de surachat détectée.\n"
    if "haussier" in s: texte += "📈 Tendance haussière.\n"
    if "baissier" in s: texte += "📉 Tendance baissière.\n"
    if not texte: texte = "ℹ️ Aucun signal fort détecté."
    return texte

def suggerer_position(df):
    last = df.iloc[-1]
    try:
        macd = float(last.Macd) if 'Macd' in df.columns else None
        rsi  = float(last.Rsi)  if 'Rsi'  in df.columns else None
        adx  = float(last.Adx)  if 'Adx'  in df.columns else None
    except:
        return "⚠️ Valeurs d'indicateurs invalides."
    if macd is None or rsi is None or adx is None:
        return "⚠️ Indicateurs manquants."
    if macd > 0 and rsi < 70 and adx > 20:
        sl, tp = round(last.Close * 0.97, 2), round(last.Close * 1.05, 2)
        return f"📈 Long | SL: {sl} | TP: {tp}"
    if macd < 0 and rsi > 30 and adx > 20:
        sl, tp = round(last.Close * 1.03, 2), round(last.Close * 0.95, 2)
        return f"📉 Short | SL: {sl} | TP: {tp}"
    return "⚠️ Conditions insuffisantes."

# Sélection du ticker
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda t: nom_affichages[t])

# Chargement du CSV et préparation des données
try:
    df_raw = pd.read_csv(f"data/donnees_{ticker.lower()}.csv", parse_dates=True)
    col_mapping = {
        "date": "Date", "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "adj close": "Close", "adjclose": "Close", "volume": "Volume"
    }
    df_raw.rename(columns=lambda c: col_mapping.get(c.lower().strip(), c), inplace=True)
    df_raw["Date"] = pd.to_datetime(df_raw["Date"], errors="coerce")
    for col in ["Open", "High", "Low", "Close"]:
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")
    df = df_raw.dropna(subset=["Date", "Open", "High", "Low", "Close"]).copy()
except Exception as e:
    st.error(f"Erreur lors du chargement ou de la préparation des données : {e}")
    st.stop()

# Ajout des indicateurs
df = ajouter_indicateurs_techniques(df)
df.columns = df.columns.str.title()

# Analyse
analyse, suggestion = analyser_signaux_techniques(df)
st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
st.markdown(analyse or "Pas de signaux.")
st.markdown(f"💬 **Résumé :**\n{generer_resume_signal(analyse.splitlines())}")
st.success(f"🤖 Intuition : {suggestion}")

# Suggestion de position
st.subheader("📌 Suggestion de position")
st.markdown(suggerer_position(df))


# Actualités
st.subheader("🗞️ Actualités")
flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
if flux.entries:
    for entry in flux.entries[:5]:
        st.markdown(f"🔹 [{entry.title}]({entry.link})")
else:
    st.info("Pas d'actualités disponibles.")

# Prédiction IA
st.subheader("📈 Prédiction IA (demain)")
pred_file = f"predictions/prediction_{ticker.lower().replace('-','').replace('^','').replace('=','')}.csv"
if os.path.exists(pred_file):
    pred = pd.read_csv(pred_file)["prediction"].iloc[-1]
    st.info("Hausse probable" if pred==1 else "Baisse probable")
else:
    st.warning("Pas de prédiction disponible.")

# RSI
st.subheader("📊 RSI actuel")
if "Rsi" in df.columns:
    st.metric("RSI", round(df["Rsi"].iloc[-1], 2))

# Données récentes
st.subheader("📄 Données récentes")
st.dataframe(df.tail(10), use_container_width=True)






















