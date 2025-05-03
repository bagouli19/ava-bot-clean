import os
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
import ta 

tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
data_dir = "data"

def ajouter_indicateurs_techniques(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute à df les indicateurs techniques suivants :
      - Moyennes mobiles SMA20, EMA20
      - RSI14
      - MACD (ligne MACD, signal et histogramme)
      - ADX14
    """
    df = df.copy()

    # 1) Vérifier qu'on a bien les colonnes de base
    requis = ["Open", "High", "Low", "Close", "Volume"]
    manquantes = [c for c in requis if c not in df.columns]
    if manquantes:
        raise KeyError(f"Impossible de calculer les indicateurs, colonnes manquantes : {manquantes}")

    # 2) SMA & EMA (période 20)
    df["Sma20"] = SMAIndicator(close=df["Close"], window=20, fillna=False).sma_indicator()
    df["Ema20"] = EMAIndicator(close=df["Close"], window=20, fillna=False).ema_indicator()

    # 3) RSI (période 14)
    df["Rsi14"] = RSIIndicator(close=df["Close"], window=14, fillna=False).rsi()

    # 4) MACD (12,26,9)
    macd_obj = MACD(close=df["Close"], window_slow=26, window_fast=12, window_sign=9, fillna=False)
    df["Macd"]      = macd_obj.macd()
    df["MacdSignal"]= macd_obj.macd_signal()
    df["MacdHist"]  = macd_obj.macd_diff()

    # 5) ADX (période 14)
    df["Adx14"] = ADXIndicator(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14,
        fillna=False
    ).adx()

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


