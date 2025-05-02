import os
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator

tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
data_dir = "data"

def ajouter_indicateurs_techniques(df):
    # Normalisation des noms de colonnes
    df.columns = [col.lower() for col in df.columns]

    # Sécurité : vérifie que les colonnes nécessaires sont présentes
    colonnes_requises = ["close", "high", "low"]
    for col in colonnes_requises:
        if col not in df.columns:
            raise KeyError(f"La colonne obligatoire '{col}' est absente du DataFrame.")

    # Ajout des indicateurs techniques
    df["sma"] = ta.trend.sma_indicator(df["close"], window=20)
    df["ema"] = ta.trend.ema_indicator(df["close"], window=20)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)
    df["cci"] = ta.trend.cci(df["high"], df["low"], df["close"], window=20)
    df["macd"] = ta.trend.macd(df["close"])

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


