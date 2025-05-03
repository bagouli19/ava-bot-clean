import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers et noms ---
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

def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd  = df["Macd"].iloc[-1]
    rsi   = df["Rsi"].iloc[-1]
    adx   = df["Adx"].iloc[-1]
    if macd > 0 and rsi < 70 and adx > 20:
        sl, tp = round(close*0.97,2), round(close*1.05,2)
        return f"📈 **Long**  🛑 SL : {sl}  🎯 TP : {tp}"
    elif macd < 0 and rsi > 30 and adx > 20:
        sl, tp = round(close*1.03,2), round(close*0.95,2)
        return f"📉 **Short**  🛑 SL : {sl}  🎯 TP : {tp}"
    else:
        return "⚠️ Conditions insuffisantes pour prise de position."

# --- Sélection du ticker ---
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# --- Lecture du fichier CSV ---
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Aucune donnée pour {nom_affichages[ticker]}.")
    st.stop()

df = pd.read_csv(fichier)

# 1) Strip + lowercase toutes les colonnes
df.columns = df.columns.str.strip().str.lower()

# 2) Repérage dynamique du suffixe ticker dans les noms
suffix = ticker.lower().replace('^','').replace('=','').replace('-','_')
# ex: "tsla", "btc_usd", "gc_f", etc.

# 3) Construction du mapping { "open_tsla": "open", ... }
mapping = {}
for col in df.columns:
    parts = col.rsplit('_', 1)
    if len(parts) == 2 and parts[1] == suffix:
        mapping[col] = parts[0]

# 4) Renommer les colonnes OHLCV ticker-spécifiques
df.rename(columns=mapping, inplace=True)

# 5) Conversion de la date
df["date"] = pd.to_datetime(df["date"])

# 6) Ajout des indicateurs (ils seront en minuscules, ex: 'macd','rsi','adx')
df = ajouter_indicateurs_techniques(df)

# 7) Renommage des indicateurs en Title Case
df.rename(columns={
    "macd": "Macd",
    "rsi":  "Rsi",
    "adx":  "Adx"
}, inplace=True)

# 8) Mettre Title Case sur les colonnes de base
df.rename(columns=lambda c: c.title(), inplace=True)

# 9) Supprimer d’éventuels doublons (génériques vs ticker-spécifiques résiduels)
df = df.loc[:, ~df.columns.duplicated()]

# 6) Remap des colonnes OHLCV si une version ticker-spécifique existe
ticker_ts = ticker.title()  # ex: "Tsla", "Btc-Usd", etc.
for attr in ["Open", "High", "Low", "Close", "Volume"]:
    col_ts = f"{attr}_{ticker_ts}"
    if col_ts in df.columns:
        df[attr] = df[col_ts]

try:
    analyse, suggestion = analyser_signaux_techniques(df)
    st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
    st.markdown(analyse)

    st.subheader("📌 Suggestion de position")
    st.markdown(suggerer_position_et_niveaux(df))

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










