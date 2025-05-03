import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers et noms d'affichage ---
tickers = ["aapl", "tsla", "googl", "btc-usd", "eth-usd", "msft", "amzn", "nvda",
           "^gspc", "doge-usd", "ada-usd", "sol-usd", "gc=F", "^fchi", "xrp-usd",
           "bnb-usd", "cl=F", "si=F", "matic-usd", "uni-usd", "^ndx","avax-usd",
           "ltc-usd", "hg=F","^dji","amd","ko","meta"]
nom_affichages = {
    "aapl":"Apple","tsla":"Tesla","googl":"Google","btc-usd":"Bitcoin","eth-usd":"Ethereum",
    "msft":"Microsoft","amzn":"Amazon","nvda":"NVIDIA","^gspc":"S&P500","doge-usd":"Dogecoin",
    "ada-usd":"Cardano","^fchi":"CAC 40","sol-usd":"Solana","gc=F":"Or (Gold)","xrp-usd":"XRP",
    "bnb-usd":"BNB","cl=F":"Pétrole brut","si=F":"Argent (Silver)","matic-usd":"Polygon (MATIC)",
    "uni-usd":"Uniswap","^ndx":"Nasdaq 100","avax-usd":"Avalanche","ltc-usd":"Litecoin",
    "hg=F":"Cuivre (Copper)","^dji":"Dow Jones","amd":"AMD","ko":"Coca-Cola","meta":"Meta"
}

def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd  = df["Macd"].iloc[-1]
    rsi   = df["Rsi"].iloc[-1]
    adx   = df["Adx"].iloc[-1]

    if macd > 0 and rsi < 70 and adx > 20:
        sl = round(close * 0.97, 2)
        tp = round(close * 1.05, 2)
        return f"📈 **Position acheteuse**\n🛑 SL : {sl}\n🎯 TP : {tp}"
    elif macd < 0 and rsi > 30 and adx > 20:
        sl = round(close * 1.03, 2)
        tp = round(close * 0.95, 2)
        return f"📉 **Position vendeuse**\n🛑 SL : {sl}\n🎯 TP : {tp}"
    else:
        return "⚠️ Conditions insuffisantes pour prise de position."

# --- Sélection du ticker ---
ticker = st.selectbox(
    "Choisissez un actif :",
    options=tickers,
    format_func=lambda x: nom_affichages.get(x, x)
)

# --- Lecture du CSV ---
fichier_data = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier_data):
    st.warning(f"❌ Aucune donnée pour {ticker}.")
    st.stop()

df = pd.read_csv(fichier_data)

# 1) Normalisation Title Case
df.columns = df.columns.str.strip().str.lower().str.title()

# 2) Conversion de Date
df["Date"] = pd.to_datetime(df["Date"])

# 3) Ajout des indicateurs (colonnes initialement lowercase)
df = ajouter_indicateurs_techniques(df)

# 4) Nouvelle normalisation (inclut Macd, Rsi, Adx…)
df.columns = df.columns.str.strip().str.lower().str.title()

# 5) Suppression des doublons de noms de colonnes
df = df.loc[:, ~df.columns.duplicated()]

# 6) Remap des colonnes OHLCV si une version ticker-spécifique existe
ticker_ts = ticker.title()  # ex: "Tsla", "Btc-Usd", etc.
for attr in ["Open", "High", "Low", "Close", "Volume"]:
    col_ts = f"{attr}_{ticker_ts}"
    if col_ts in df.columns:
        df[attr] = df[col_ts]

try:
    # Analyse technique
    analyse, suggestion = analyser_signaux_techniques(df)

    st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
    st.markdown(analyse)
    st.markdown(f"💬 **Résumé AVA :** {suggestion}")

    # Suggestion de position
    st.subheader("📌 Suggestion de position")
    st.markdown(suggerer_position_et_niveaux(df))

    # Candlestick
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

    # Actualités
    st.subheader("🗞️ Actualités financières")
    flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
    if flux.entries:
        for e in flux.entries[:5]:
            st.markdown(f"🔹 [{e.title}]({e.link})", unsafe_allow_html=True)
    else:
        st.info("Pas d’actus dispo.")

    # Prédiction IA
    fichier_pred = f"predictions/prediction_{ticker.lower().replace('-', '').replace('^','').replace('=','')}.csv"
    if os.path.exists(fichier_pred):
        pred = pd.read_csv(fichier_pred)["prediction"].iloc[-1]
        st.subheader("📈 Prédiction IA (demain)")
        st.info("Hausse probable" if pred==1 else "Baisse probable")
    else:
        st.warning("Aucune prédiction trouvée.")

    # RSI
    if "Rsi" in df.columns:
        st.subheader("📊 RSI actuel")
        st.metric("RSI", round(df["Rsi"].iloc[-1],2))

    # Données brutes
    st.subheader("📄 Données récentes")
    st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue pendant l'analyse : {e}")










