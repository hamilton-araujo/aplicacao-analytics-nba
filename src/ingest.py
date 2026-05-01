"""Carga e limpeza do NBA Players dataset."""

import logging
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "all_seasons.csv"

MIN_GP = 20  # mínimo de jogos para análises de performance


def carregar() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado em {CSV_PATH}.\n"
            "Baixe via: kaggle datasets download -d justinas/nba-players-data"
        )
    df = pd.read_csv(CSV_PATH)
    df = _limpar(df)
    logger.info("Dataset carregado: %d registros | %d jogadores | %d temporadas",
                len(df), df["player_name"].nunique(), df["season"].nunique())
    return df


def _limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    df = df.dropna(subset=["pts", "reb", "ast", "net_rating"])
    df["draft_year"]   = pd.to_numeric(df["draft_year"],   errors="coerce")
    df["draft_round"]  = pd.to_numeric(df["draft_round"],  errors="coerce")
    df["draft_number"] = pd.to_numeric(df["draft_number"], errors="coerce")
    df["season_start"] = df["season"].str[:4].astype(int)
    df["era"] = pd.cut(
        df["season_start"],
        bins=[1995, 2002, 2010, 2018, 2030],
        labels=["Late 90s (96–02)", "2000s (03–10)", "2010s (11–18)", "Modern (19+)"],
    )
    df["is_international"] = df["country"].notna() & (df["country"] != "USA")
    df["efficiency"] = (df["pts"] + df["reb"] + df["ast"]) * df["ts_pct"]
    return df.reset_index(drop=True)


def resumo(df: pd.DataFrame) -> None:
    print(f"\n{'─'*54}")
    print(f"  NBA Players Analytics — {df['player_name'].nunique():,} jogadores")
    print(f"{'─'*54}")
    print(f"  Registros       : {len(df):,}")
    print(f"  Temporadas      : {df['season'].min()} → {df['season'].max()}")
    print(f"  Internacionais  : {df['is_international'].mean():.1%}")
    print(f"  PPG médio       : {df['pts'].mean():.1f}")
    print(f"{'─'*54}\n")
