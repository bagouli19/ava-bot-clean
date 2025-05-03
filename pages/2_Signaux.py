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

# Lecture du CSV complet et mapping dynamique des colonnes OHLCV
try:
    df_raw = pd.read_csv(fichier)
    df_raw.columns = [c.lower() for c in df_raw.columns]
    col_map = {}
    for col in df_raw.columns:
        if col in ["date", "datetime", "time"]:
            col_map[col] = "date"
        elif col.startswith("open"):
            col_map[col] = "open"
        elif col.startswith("high"):
            col_map[col] = "high"
        elif col.startswith("low"):
            col_map[col] = "low"
        elif col.startswith("close") or "adj" in col:
            col_map[col] = "close"
        elif col == "volume":
            col_map[col] = "volume"
    df = df_raw.rename(columns=col_map)
    df = df[["date", "open", "high", "low", "close", "volume"]]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["date", "open", "high", "low", "close"], inplace=True)
except Exception as e:
    st.error(f"Erreur lecture CSV : {e}")
    st.stop()

# Ajout indicateurs
try:
    df = ajouter_indicateurs_techniques(df)
except Exception as e:
    st.error(f"Erreur indicateurs : {e}")
    st.stop()

# Analyse signaux
try:
    analyse, suggestion = analyser_signaux_techniques(df)
except Exception as e:
    st.error(f"Erreur analyse technique : {e}")
    st.stop()

st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
st.markdown(analyse or "Pas de signaux.")

# Suggestion
st.subheader("📌 Suggestion de position")
def suggerer_position_et_niveaux(df):
    try:
        close = df["close"].iloc[-1]
        macd = df["macd"].iloc[-1]
        rsi = df["rsi"].iloc[-1]
        adx = df["adx"].iloc[-1]
        if macd > 0 and rsi < 70 and adx > 20:
            sl, tp = round(close*0.97, 2), round(close*1.05, 2)
            return f"📈 Achat possible  SL: {sl}, TP: {tp}"
        elif macd < 0 and rsi > 30 and adx > 20:
            sl, tp = round(close*1.03, 2), round(close*0.95, 2)
            return f"📉 Vente possible  SL: {sl}, TP: {tp}"
        else:
            return "⚠️ Conditions insuffisantes"
    except:
        return "⚠️ Indicateurs manquants."

st.markdown(suggerer_position_et_niveaux(df))

# Bougies
st.subheader("📈 Bougies japonaises")
try:
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        increasing_line_color="green", decreasing_line_color="red"
    )])
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Erreur bougies : {e}")














