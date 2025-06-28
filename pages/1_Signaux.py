import streamlit as st
import pandas as pd
import os
from analyse_technique import ajouter_indicateurs_techniques, analyser_signaux_techniques
import plotly.graph_objects as go
import feedparser
from auth import verifier_acces
verifier_acces()

# ─────────────────────────────────────────────────────────────
#  CONFIG  •  OBLIVIA
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="OBLIVIA – Signaux d’Effondrement", layout="wide")

st.markdown("""
<style>
    .stApp { background:#0d0d0f; color:#e6e6e6; }
    .dark-title   { font-size:2.2em; font-weight:700; color:#FF3C3C; text-shadow:0 0 12px #FF3C3C; }
    .dark-sub     { font-size:1.1em; font-style:italic; color:#aaaaaa; margin-top:-10px; }
    .metric-title { color:#FF3C3C; }
    .rsi .metric-label { color:#FF3C3C !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dark-title">Signaux d’Effondrement</div>', unsafe_allow_html=True)
st.markdown('<div class="dark-sub">Oblivia scanne les marchés… pas pour prédire leur avenir, mais pour déceler les failles qui les feront tomber.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  LISTE DES ACTIFS
# ─────────────────────────────────────────────────────────────
tickers = ["aapl","tsla","googl","btc-usd","eth-usd","msft","amzn","nvda",
           "^gspc","doge-usd","ada-usd","sol-usd","gc=F","^fchi","xrp-usd",
           "bnb-usd","cl=F","si=F","matic-usd","uni-usd","^ndx","avax-usd",
           "ltc-usd","hg=F","^dji","amd","ko","meta"]

nom_affichages = {
    "aapl":"Apple","tsla":"Tesla","googl":"Google","btc-usd":"Bitcoin",
    "eth-usd":"Ethereum","msft":"Microsoft","amzn":"Amazon","nvda":"NVIDIA",
    "^gspc":"S&P500","doge-usd":"Dogecoin","ada-usd":"Cardano","^fchi":"CAC 40",
    "sol-usd":"Solana","gc=F":"Or","xrp-usd":"XRP","bnb-usd":"BNB",
    "cl=F":"Petrole brut","si=F":"Argent","matic-usd":"Polygon","uni-usd":"Uniswap",
    "^ndx":"Nasdaq 100","avax-usd":"Avalanche","ltc-usd":"Litecoin","hg=F":"Cuivre",
    "^dji":"Dow Jones","amd":"AMD","ko":"Coca-Cola","meta":"Meta"
}

# ─────────────────────────────────────────────────────────────
#  FONCTIONS AUXILIAIRES
# ─────────────────────────────────────────────────────────────
def generer_resume_signal(signaux:list):
    texte, s = "", " ".join(signaux).lower()
    if "survente" in s:  texte += "🔻 Survente critique.\n"
    if "surachat" in s:  texte += "🔺 Surachat delirant.\n"
    if "haussier" in s:  texte += "📈 Impulsion haussiere.\n"
    if "baissier" in s:  texte += "📉 Tendance baissiere.\n"
    return texte or "ℹ️  Zéro signal notable."

def suggerer_position(df:pd.DataFrame):
    last = df.iloc[-1]
    try:
        macd = float(last.Macd) if 'Macd' in df.columns else None
        rsi  = float(last.Rsi)  if 'Rsi'  in df.columns else None
        adx  = float(last.Adx)  if 'Adx'  in df.columns else None
    except: return "⚠️  Données invalides."
    if None in (macd,rsi,adx): return "⚠️  Indicateurs manquants."
    if macd>0 and rsi<70 and adx>20:
        return f"📈 Long  | SL {round(last.Close*0.97,2)} | TP {round(last.Close*1.05,2)}"
    if macd<0 and rsi>30 and adx>20:
        return f"📉 Short | SL {round(last.Close*1.03,2)} | TP {round(last.Close*0.95,2)}"
    return "🟡 Pas de configuration idéale."

# ─────────────────────────────────────────────────────────────
#  SÉLECTION UTILISATEUR
# ─────────────────────────────────────────────────────────────
ticker = st.selectbox("Choisis un actif à disséquer :", tickers,
                      format_func=lambda t: nom_affichages[t])

# ─────────────────────────────────────────────────────────────
#  DATA LOADING & PREP
# ─────────────────────────────────────────────────────────────
try:
    df_raw = pd.read_csv(f"data/donnees_{ticker.lower()}.csv", parse_dates=True)
    mapping = {"date":"Date","open":"Open","high":"High","low":"Low",
               "close":"Close","adj close":"Close","adjclose":"Close","volume":"Volume"}
    df_raw.rename(columns=lambda c: mapping.get(c.lower().strip(), c), inplace=True)
    df_raw["Date"] = pd.to_datetime(df_raw["Date"], errors="coerce")
    for col in ["Open","High","Low","Close"]:
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")
    df = df_raw.dropna(subset=["Date","Open","High","Low","Close"]).copy()
except Exception as e:
    st.error(f"⛔ Erreur de chargement : {e}")
    st.stop()

# Indicateurs + analyse
df = ajouter_indicateurs_techniques(df)
analyse, suggestion = analyser_signaux_techniques(df)

# ─────────────────────────────────────────────────────────────
#  AFFICHAGE
# ─────────────────────────────────────────────────────────────
st.subheader(f"🔎 Analyse – {nom_affichages[ticker]}")
st.markdown(analyse or "Aucun signal détecté.")
st.markdown(f"**Synthèse sombre :**\n{generer_resume_signal(analyse.splitlines())}")
st.success(f"🧠 Verdict Oblivia : {suggestion}")

# Suggestion
st.subheader("💰 Stratégie potentielle")
st.markdown(suggerer_position(df))

# Actus
st.subheader("🗞️  Dernières actualités")
flux = feedparser.parse("https://www.investing.com/rss/news_301.rss")
if flux.entries:
    for entry in flux.entries[:5]:
        st.markdown(f"• [{entry.title}]({entry.link})")
else:
    st.info("Silence radio… pour l'instant.")

# Prédiction IA
st.subheader("🔮 Projection IA (J+1)")
pred_file = f"predictions/prediction_{ticker.lower().replace('-','').replace('^','').replace('=','')}.csv"
if os.path.exists(pred_file):
    pred = pd.read_csv(pred_file)["prediction"].iloc[-1]
    st.info("Probable hausse" if pred==1 else "Probable baisse")
else:
    st.warning("Aucune projection disponible.")

# RSI
if "Rsi" in df.columns:
    st.subheader("📊 RSI")
    st.metric("RSI", round(df["Rsi"].iloc[-1], 2))

# Données récentes
st.subheader("📄 10 dernières lignes")
st.dataframe(df.tail(10), use_container_width=True)




















