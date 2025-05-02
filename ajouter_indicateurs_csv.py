import os
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
import ta 

tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
data_dir = "data"

def ajouter_indicateurs_techniques(df):
    # On s'assure que les noms de colonnes sont bien formatés
    df.columns = [col.strip().capitalize() for col in df.columns]

    # Ajout des indicateurs techniques
    df["Sma"] = ta.trend.sma_indicator(df["Close"], window=20)
    df["Ema"] = ta.trend.ema_indicator(df["Close"], window=20)
    df["Rsi"] = ta.momentum.rsi(df["Close"], window=14)
    df["Macd"] = ta.trend.macd(df["Close"])
    df["Adx"] = ta.trend.adx(df["High"], df["Low"], df["Close"], window=14)

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


