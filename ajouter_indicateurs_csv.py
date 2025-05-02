import os
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator

tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
data_dir = "data"

def ajouter_indicateurs_techniques(df):
    # S'assurer que les noms de colonnes sont en minuscules
    df.columns = [col.lower() for col in df.columns]

    # Moyennes mobiles simples et exponentielles
    df["sma"] = ta.trend.sma_indicator(df["close"], window=20)
    df["ema"] = ta.trend.ema_indicator(df["close"], window=20)

    # Indicateur RSI
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    # Indicateur MACD
    macd = ta.trend.macd(df["close"])
    df["macd"] = macd

    # Bandes de Bollinger
    bollinger = ta.volatility.BollingerBands(df["close"])
    df["bb_milieu"] = bollinger.bollinger_mavg()
    df["bb_haut"] = bollinger.bollinger_hband()
    df["bb_bas"] = bollinger.bollinger_lband()

    # ADX
    df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"])

    # CCI
    df["cci"] = ta.trend.cci(df["high"], df["low"], df["close"], window=20)

    # Williams %R
    df["williams_r"] = ta.momentum.williams_r(df["high"], df["low"], df["close"], lbp=14)

    return df

for ticker in tickers:
    chemin = os.path.join(data_dir, f"donnees_{ticker.lower()}.csv")
    if os.path.exists(chemin):
        df = pd.read_csv(chemin)

        # --- Vérification/normalisation de la colonne date ---
        if 'date' not in df.columns:
            if 'Date' in df.columns:
                df.rename(columns={"Date": "date"}, inplace=True)
            else:
                df.reset_index(inplace=True)  # Si date est dans l'index
                if 'date' not in df.columns and 'Date' in df.columns:
                    df.rename(columns={"Date": "date"}, inplace=True)

        if 'date' in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
        else:
            print(f"❌ Erreur : pas de colonne 'date' dans {chemin}")
            continue

        df = ajouter_indicateurs(df)
        df.to_csv(chemin, index=False)
        print(f"✅ Indicateurs ajoutés pour {ticker}")
    else:
        print(f"❌ Fichier introuvable : {chemin}")


