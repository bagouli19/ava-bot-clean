import os
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
import ta 

tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
data_dir = "data"

import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator


def ajouter_indicateurs_techniques(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les indicateurs techniques au DataFrame :
    - SMA20, EMA20
    - RSI14
    - MACD (ligne, signal, histogramme)
    - ADX14

    Attends que df contienne au moins les colonnes :
      "Open", "High", "Low", "Close".
    Ne renomme pas les colonnes existantes.
    """
    df = df.copy()

    # Vérification
    requis = ["Open", "High", "Low", "Close"]
    manquantes = [c for c in requis if c not in df.columns]
    if manquantes:
        raise KeyError(f"Colonnes manquantes pour indicateurs techniques : {manquantes}")

    # SMA20
    df["Sma20"] = SMAIndicator(
        close=df["Close"], window=20, fillna=True
    ).sma_indicator()

    # EMA20
    df["Ema20"] = EMAIndicator(
        close=df["Close"], window=20, fillna=True
    ).ema_indicator()

    # RSI14
    df["Rsi14"] = RSIIndicator(
        close=df["Close"], window=14, fillna=True
    ).rsi()

    # MACD (12,26,9)
    macd_obj = MACD(
        close=df["Close"], window_slow=26, window_fast=12, window_sign=9, fillna=True
    )
    df["Macd"]       = macd_obj.macd()
    df["MacdSignal"] = macd_obj.macd_signal()
    df["MacdHist"]   = macd_obj.macd_diff()

    # ADX14
    df["Adx14"] = ADXIndicator(
        high=df["High"], low=df["Low"], close=df["Close"], window=14, fillna=True
    ).adx()

    return df


def analyser_signaux_techniques(df: pd.DataFrame):
    """
    Exemple de fonction d'analyse des indicateurs.
    Retourne (texte_signaux, suggestion_action)
    """
    signaux = []
    suggestion = None

    # Exemple basique : survente sur RSI
    if "Rsi14" in df.columns:
        rsi = df["Rsi14"].iloc[-1]
        if rsi < 30:
            signaux.append("Survente")
        elif rsi > 70:
            signaux.append("Surachat")

    # Exemple : tendance MACD
    if "Macd" in df.columns and "MacdSignal" in df.columns:
        macd, signal = df["Macd"].iloc[-1], df["MacdSignal"].iloc[-1]
        if macd > signal:
            signaux.append("Haussier")
        else:
            signaux.append("Baissier")

    texte = "\n".join(signaux)
    suggestion = "Aucune action recommandée" if not signaux else "Suivre les signaux"  
    return texte, suggestion



