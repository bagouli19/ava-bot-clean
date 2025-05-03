import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers disponibles et noms à afficher ---
tickers = [
    "aapl", "tsla", "googl", "btc-usd", "eth-usd",
    "msft", "amzn", "nvda", "^gspc", "doge-usd", "ada-usd",
    "sol-usd", "gc=F", "^fchi", "xrp-usd", "bnb-usd", "cl=F", "si=F",
    "matic-usd", "uni-usd", "^ndx","avax-usd","ltc-usd",
    "hg=F","^dji","amd","ko","meta"
]

nom_affichages = {
    "aapl": "Apple", "tsla": "Tesla", "googl": "Google",
    "btc-usd": "Bitcoin", "eth-usd": "Ethereum", "msft": "Microsoft",
    "amzn": "Amazon", "nvda": "NVIDIA", "^gspc": "S&P500",
    "doge-usd": "Dogecoin", "ada-usd": "Cardano", "^fchi": "CAC 40",
    "sol-usd": "Solana", "gc=F": "Or (Gold)", "xrp-usd": "XRP",
    "bnb-usd": "BNB", "cl=F": "Pétrole brut", "si=F": "Argent (Silver)",
    "matic-usd": "Polygon (MATIC)", "uni-usd": "Uniswap", "^ndx": "Nasdaq 100",
    "avax-usd": "Avalanche", "ltc-usd": "Litecoin", "hg=F": "Cuivre (Copper)",
    "^dji": "Dow Jones", "amd": "AMD", "ko": "Coca-Cola", "meta": "Meta"
}

def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd  = df["Macd"].iloc[-1]
    rsi   = df["Rsi"].iloc[-1]
    adx   = df["Adx"].iloc[-1]

    if macd > 0 and rsi < 70 and adx > 20:
        sl = round(close * 0.97, 2)
        tp = round(close * 1.05, 2)
        return (
            "📈 **Position acheteuse**\n"
            f"🛑 Stop-Loss : {sl}\n"
            f"🎯 Take-Profit : {tp}"
        )
    elif macd < 0 and rsi > 30 and adx > 20:
        sl = round(close * 1.03, 2)
        tp = round(close * 0.95, 2)
        return (
            "📉 **Position vendeuse**\n"
            f"🛑 Stop-Loss : {sl}\n"
            f"🎯 Take-Profit : {tp}"
        )
    else:
        return "⚠️ Conditions insuffisantes pour prise de position."

# --- Sélection du ticker ---
ticker = st.selectbox(
    "Choisissez un actif :",
    options=tickers,
    format_func=lambda x: nom_affichages.get(x, x)
)

# --- Chargement des données ---
fichier_data = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier_data):
    st.warning(f"❌ Aucune donnée trouvée pour {ticker}. Veuillez lancer l'entraînement AVA.")
    st.stop()

df = pd.read_csv(fichier_data)

# 1) Normaliser toutes les colonnes : strip → lower → title
df.columns = df.columns.str.strip().str.lower().str.title()

# 2) Conversion de la date
df["Date"] = pd.to_datetime(df["Date"])

# 3) Ajout des indicateurs techniques (colonnes en minuscules)
df = ajouter_indicateurs_techniques(df)

# 4) Re-normalisation des colonnes (ajouts inclus)
df.columns = df.columns.str.strip().str.lower().str.title()

# 5) Suppression des doublons de colonnes
df = df.loc[:, ~df.columns.duplicated()]

# 6) Analyse des signaux
try:
    analyse, suggestion = analyser_signaux_techniques(df)

    # Affichage de l’analyse
    st.subheader(f"🔎 Analyse pour {nom_affichages.get(ticker)}")
    st.markdown(analyse)

    # Résumé des signaux
    st.markdown(f"💬 **Résumé d'AVA :**\n{suggestion}")

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
    fichier_pred = f"predictions/prediction_{ticker.lower().replace('-', '').replace('^','').replace('=','')}.csv"
    if os.path.exists(fichier_pred):
        pred = pd.read_csv(fichier_pred)["prediction"].iloc[-1]
        st.subheader("📈 Prédiction IA (demain)")
        st.info("Hausse probable" if pred == 1 else "Baisse probable")
    else:
        st.warning("Aucune prédiction trouvée.")

    # Affichage du RSI actuel
    if "Rsi" in df.columns:
        st.subheader("📊 RSI actuel")
        st.metric("RSI", round(df["Rsi"].iloc[-1], 2))

    # Données brutes
    st.subheader("📄 Données récentes")
    st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue pendant l'analyse : {e}")









