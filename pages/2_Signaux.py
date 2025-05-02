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
    "aapl": "Apple",
    "tsla": "Tesla",
    "googl": "Google",
    "btc-usd": "Bitcoin",
    "eth-usd": "Ethereum",
    "msft": "Microsoft",
    "amzn": "Amazon",
    "nvda": "NVIDIA",
    "^gspc": "S&P500",
    "doge-usd": "Dogecoin",
    "ada-usd": "Cardano",
    "^fchi": "CAC 40",
    "sol-usd": "Solana",
    "gc=F": "Or (Gold)",
    "xrp-usd": "XRP",
    "bnb-usd": "BNB",
    "cl=F": "Pétrole brut",
    "si=F": "Argent (Silver)",
    "matic-usd": "Polygon (MATIC)",
    "uni-usd": "Uniswap",
    "^ndx": "Nasdaq 100",
    "avax-usd": "Avalanche",
    "ltc-usd": "Litecoin",
    "hg=F": "Cuivre (Copper)",
    "^dji": "Dow Jones Industrial Average",
    "amd": "AMD (Advanced Micro Devices)",
    "ko": "Coca-Cola",
    "meta": "Meta Platforms (Facebook)",


}


# --- Fonction de suggestion d'ouverture de position avec SL/TP ---
def suggerer_position_et_niveaux(df):
    close = df["Close"].iloc[-1]
    macd = df["Macd"].iloc[-1]
    rsi = df["Rsi"].iloc[-1]
    adx = df["Adx"].iloc[-1]

    if macd > 0 and rsi < 70 and adx > 20:
        position = "📈 Ouverture d’une **position acheteuse** (long)"
        sl = close * 0.97
        tp = close * 1.05
    elif macd < 0 and rsi > 30 and adx > 20:
        position = "📉 Ouverture d’une **position vendeuse** (short)"
        sl = close * 1.03
        tp = close * 0.95
    else:
        return "⚠️ Les conditions ne sont pas assez claires pour une prise de position."

    sl = round(sl, 2)
    tp = round(tp, 2)
    return f"{position}\n\n🛑 Stop-Loss : **{sl}**\n🎯 Take-Profit : **{tp}**"


# --- Sélection du ticker ---
ticker = st.selectbox("Choisissez un actif :", options=tickers, format_func=lambda x: nom_affichages.get(x, x))

# --- Chargement des données ---
fichier_data = f"data/donnees_{ticker.lower()}.csv"
fichier_pred = f"predictions/prediction_{ticker.lower().replace('-', '').replace('^', '').replace('=','')}.csv"

if os.path.exists(fichier_data):
    df = pd.read_csv(fichier_data)

    # ✅ On renomme les colonnes si nécessaire pour correspondre à l'analyse technique
    df.columns = [col.strip().capitalize() for col in df.columns]
    df = df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "date": "Date"
    })

    df = ajouter_indicateurs_techniques(df)

    try:
        analyse, suggestion = analyser_signaux_techniques(df)

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
            if texte == "":
                texte = "ℹ️ Aucun signal fort détecté pour l'instant. Restez à l'affût."
            return texte

        signaux_list = analyse.split("\n") if analyse else []
        resume = generer_resume_signal(signaux_list)

        # --- Affichage de l’analyse ---
        st.subheader(f"🔎 Analyse pour {nom_affichages.get(ticker, ticker.upper())}")
        st.markdown(analyse)
        st.markdown(f"💬 **Résumé d'AVA :**\n{resume}")
        st.success(f"🤖 *Intuition d'AVA :* {suggestion}")

        # --- Suggestion de position ---
        st.subheader("📌 Suggestion de position")
        st.markdown(suggerer_position_et_niveaux(df))

        st.subheader("📈 Graphique en bougies japonaises")
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
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



        # --- Actualités financières ---
        st.subheader("🗞️ Actualités financières récentes")
        try:
            flux_rss = "https://www.investing.com/rss/news_301.rss"
            flux = feedparser.parse(flux_rss)
            if flux.entries:
                for entry in flux.entries[:5]:
                    st.markdown(f"🔹 [{entry.title}]({entry.link})", unsafe_allow_html=True)
            else:
                st.info("Aucune actualité n’a pu être récupérée pour le moment.")
        except Exception as e:
            st.warning("⚠️ Impossible de charger les actualités financières.")
            st.text(f"Erreur : {e}")

        # --- Prédiction IA ---
        if os.path.exists(fichier_pred):
            df_pred = pd.read_csv(fichier_pred)
            prediction = df_pred["prediction"].iloc[-1]
            st.subheader("📈 Prédiction IA (demain) :")
            st.info("📈 Hausse probable demain" if prediction == 1 else "📉 Baisse probable demain")
        else:
            st.warning("Aucune prédiction trouvée.")

        # --- RSI résumé ---
        if 'rsi' in df.columns:
            st.subheader("📊 RSI actuel :")
            st.metric("RSI", round(df["rsi"].iloc[-1], 2))

        # --- Données brutes ---
        st.subheader("📄 Données récentes")
        st.dataframe(df.tail(10), use_container_width=True)

    except Exception as e:
        st.error(f"Une erreur est survenue pendant l'analyse : {e}")

else:
    st.warning(f"❌ Aucune donnée trouvée pour {ticker}. Veuillez lancer l'entraînement AVA.")








