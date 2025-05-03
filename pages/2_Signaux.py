import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser

st.set_page_config(page_title="📈 Signaux Techniques", layout="wide")
st.title("📍 Signaux Techniques d'AVA")

# --- Tickers et noms d'affichage ---
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
    close, macd, rsi, adx = df["Close"].iat[-1], df["Macd"].iat[-1], df["Rsi"].iat[-1], df["Adx"].iat[-1]
    if macd>0 and rsi<70 and adx>20:
        sl, tp = round(close*0.97,2), round(close*1.05,2)
        return f"📈 **Long**  🛑 SL:{sl}  🎯 TP:{tp}"
    if macd<0 and rsi>30 and adx>20:
        sl, tp = round(close*1.03,2), round(close*0.95,2)
        return f"📉 **Short**  🛑 SL:{sl}  🎯 TP:{tp}"
    return "⚠️ Conditions insuffisantes."

# --- Choix du ticker ---
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# --- Lecture & formattage du CSV ---
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Pas de données pour {nom_affichages[ticker]}.")
    st.stop()

    # 1) On lit et on sélectionne *toujours* les 6 premières colonnes
    df_raw = pd.read_csv(fichier, parse_dates=[0], dayfirst=True)
    df = df_raw.iloc[:, :6].copy()

    # 2) On renomme à la main les 6 colonnes
    col_map = {
        "date":  "Date",
        "open":  "Open",
        "high":  "High",
        "low":   "Low",
        "close": "Close",
        "volume":"Volume"
    }
    df.columns = [col_map.get(col.strip().lower(), col) for col in df.columns]

    # 3) On force les types et on droppe toute ligne incomplète
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["Open","High","Low","Close","Volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.dropna(subset=["Date","Open","High","Low","Close","Volume"], inplace=True)

    # 4) On ajoute les indicateurs techniques (fonction inchangée)
    df = ajouter_indicateurs_techniques(df)

    # 5) On renomme **seulement** les colonnes issues des indicateurs
    #    (elles étaient créées en minuscules dans votre fonction)
    df.rename(columns={
        "sma":   "Sma",
        "ema":   "Ema",
        "rsi":   "Rsi",
        "macd":  "Macd",
        "adx":   "Adx",
        "cci":   "Cci",
        "willr": "Willr"
    }, inplace=True)

    # 6) On s’assure qu’il n’y a pas de doublons de colonnes
    df = df.loc[:, ~df.columns.duplicated()]

    # --- Affichage complet ---
    try:
        analyse, suggestion = analyser_signaux_techniques(df)
        st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
        st.markdown(analyse)

        resume = generer_resume_signal(analyse.split("\n"))
        st.markdown(f"💬 **Résumé AVA :**\n{resume}")
        st.success(f"🤖 *Intuition AVA :* {suggestion}")

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

        # 🗞️ Actualités
        st.subheader("🗞️ Actualités financières")
        flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
        if flux.entries:
            for e in flux.entries[:5]:
                st.markdown(f"🔹 [{e.title}]({e.link})", unsafe_allow_html=True)
        else:
            st.info("Aucune actualité à afficher.")

        # 🤖 Prédiction IA
        pred_file = f"predictions/prediction_{ticker.lower().replace('-', '').replace('^','').replace('=','')}.csv"
        if os.path.exists(pred_file):
            pred = pd.read_csv(pred_file)["prediction"].iat[-1]
            st.subheader("📈 Prédiction IA (demain)")
            st.info("Hausse probable" if pred==1 else "Baisse probable")
        else:
            st.warning("Aucune prédiction trouvée.")

        # 📊 RSI actuel
        if "Rsi" in df.columns:
            st.subheader("📊 RSI actuel")
            st.metric("RSI", round(df["Rsi"].iat[-1],2))

        # 📄 Données brutes
        st.subheader("📄 Données récentes")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Erreur pendant l'analyse : {e}")












