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
    macd, rsi, adx = last.Macd if 'Macd' in df else None,
                   last.Rsi if 'Rsi' in df else None,
                   last.Adx if 'Adx' in df else None
    if macd is None or rsi is None or adx is None:
        return "⚠️ Indicateurs manquants."
    if macd>0 and rsi<70 and adx>20:
        sl, tp = round(last.Close*0.97,2), round(last.Close*1.05,2)
        return f"📈 Long | SL: {sl} | TP: {tp}"
    if macd<0 and rsi>30 and adx>20:
        sl, tp = round(last.Close*1.03,2), round(last.Close*0.95,2)
        return f"📉 Short | SL: {sl} | TP: {tp}"
    return "⚠️ Conditions insuffisantes."
# Sélection actif
ticker = st.selectbox("Choisissez un actif :", tickers, format_func=lambda x: nom_affichages[x])

# Lecture CSV
fichier = f"data/donnees_{ticker.lower()}.csv"
if not os.path.exists(fichier):
    st.warning(f"❌ Aucune donnée pour {nom_affichages[ticker]}")
    st.stop()

df_raw = pd.read_csv(fichier)
if df_raw.shape[1] < 6:
    st.error("Le CSV doit contenir au moins 6 colonnes OHLCV.")
    st.stop()

# On prend les 6 premières colonnes et on renomme
df = df_raw.iloc[:, :6].copy()
df.columns = ["Date","Open","High","Low","Close","Volume"]

# Conversion types
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
for c in ["Open","High","Low","Close","Volume"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df.dropna(subset=["Date","Open","High","Low","Close","Volume"], inplace=True)

# Debug initial
st.write("Données brutes (5 lignes) :", df.head())

# Ajout indicateurs
try:
    df = ajouter_indicateurs_techniques(df)
    df.columns = df.columns.str.title()
except Exception as e:
    st.error(f"Erreur indicateurs techniques : {e}")
    st.stop()

# Debug après indicateurs
st.write("Colonnes après ajout indicateurs:", df.columns.tolist())

# Analyse signaux
try:
    analyse, suggestion = analyser_signaux_techniques(df)
except Exception as e:
    st.error(f"Erreur analyse technique : {e}")
    st.stop()

# Affichages
st.subheader(f"🔎 Analyse pour {nom_affichages[ticker]}")
st.markdown(analyse or "Pas de signaux.")
st.markdown(f"💬 **Résumé :**\n{generer_resume_signal(analyse.splitlines())}")
st.success(f"🤖 *Intuition :* {suggestion}")

# Suggestion position
st.subheader("📌 Suggestion de position")
st.markdown(suggerer_position_et_niveaux(df))

# Prepare df_plot
df_plot = df.sort_values("Date").reset_index(drop=True)
st.write("Données pour graf. bougies:", df_plot.head())

# Candlestick
st.subheader("📈 Graphique en bougies japonaises")
fig = go.Figure(data=[go.Candlestick(
    x=df_plot["Date"],
    open=df_plot["Open"],
    high=df_plot["High"],
    low=df_plot["Low"],
    close=df_plot["Close"],
    increasing_line_color="green",
    decreasing_line_color="red"
)])
fig.update_layout(xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# Fallback line chart
st.subheader("📈 Prix de clôture (ligne)")
st.line_chart(df_plot.set_index("Date")["Close"])

# Actualités
st.subheader("🗞️ Actualités")
flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
if flux.entries:
    for e in flux.entries[:5]:
        st.markdown(f"- [{e.title}]({e.link})", unsafe_allow_html=True)
else:
    st.info("Pas d’actualités.")

# Prédiction IA
st.subheader("📈 Prédiction IA (demain)")
pred_file = f"predictions/prediction_{ticker.lower().replace('-','').replace('^','').replace('=','')}.csv"
if os.path.exists(pred_file):
    pred = pd.read_csv(pred_file)["prediction"].iloc[-1]
    st.info("Hausse probable" if pred==1 else "Baisse probable")
else:
    st.warning("Aucune prédiction.")

# RSI
st.subheader("📊 RSI actuel")
if "Rsi" in df_plot.columns:
    st.metric("RSI", round(df_plot["Rsi"].iloc[-1],2))
elif "Rsi14" in df_plot.columns:
    st.metric("RSI", round(df_plot["Rsi14"].iloc[-1],2))

# Données brutes
st.subheader("📄 Données récentes")
st.dataframe(df.tail(10), use_container_width=True)
















