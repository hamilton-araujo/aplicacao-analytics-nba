"""
Player Valuation — Cap Value (proxy Wins Above Replacement).

Por que existe:
    Front Office da NBA toma decisão de contrato baseada em valor.
    Estatística pura (PPG, TS%) ignora idade, minutos e impacto.
    "Cap Value" simplifica: quanto este jogador "vale" do salary cap?

Heurística (proxy WAR):
    base_value = efficiency_score × minutos_per_game / 36
    age_factor = exp(-(idade-27)² / 200)        # pico em 27 anos
    eras_factor = 1 - (anos_desde_2020) × 0.005  # ajuste inflacionário

    cap_value_$ = base_value × age_factor × era_factor × $1.5M
    salário_max NBA 2024 ≈ $50M (estrela), $5M (rookie min)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ValorJogador:
    player_name:    str
    age:            int
    season:         str
    efficiency:     float
    minutes:        float
    cap_value_usd:  float    # estimativa
    tier:           str      # SUPERSTAR / STAR / STARTER / ROTATION / BENCH


def _classificar_tier(cap_value: float) -> str:
    if cap_value >= 35_000_000:
        return "SUPERSTAR"
    if cap_value >= 25_000_000:
        return "STAR"
    if cap_value >= 15_000_000:
        return "STARTER"
    if cap_value >= 7_000_000:
        return "ROTATION"
    return "BENCH"


def calcular(
    df: pd.DataFrame,
    season_alvo: str | None = None,
    ano_atual: int = 2024,
) -> pd.DataFrame:
    """
    Calcula cap value para todos os jogadores (ou season filtrada).

    Espera colunas: player_name, age, season (string), efficiency_score (ou pts/reb/ast),
                    minutes (ou min), pts.
    """
    df = df.copy()
    if season_alvo:
        df = df[df["season"] == season_alvo]

    # Detecta colunas alternativas
    if "efficiency_score" not in df.columns:
        # Proxy: pts + reb + ast
        for c in ["pts", "reb", "ast"]:
            if c not in df.columns:
                df[c] = 0
        df["efficiency_score"] = df["pts"] + 0.7 * df["reb"] + 0.7 * df["ast"]

    if "minutes" not in df.columns and "min" in df.columns:
        df["minutes"] = df["min"]
    elif "minutes" not in df.columns:
        df["minutes"] = 25.0

    df["minutes"] = df["minutes"].fillna(25).clip(lower=5)
    df["age"] = df["age"].fillna(27)

    base_value = df["efficiency_score"] * (df["minutes"] / 36)
    age_factor = np.exp(-((df["age"] - 27) ** 2) / 200)
    if "season_start" in df.columns:
        anos_desde = (ano_atual - df["season_start"]).clip(lower=0, upper=30)
    else:
        anos_desde = 0
    era_factor = 1 - anos_desde * 0.005

    cap_value = base_value * age_factor * era_factor * 1_500_000
    df["cap_value_usd"] = cap_value.clip(lower=500_000, upper=55_000_000)
    df["tier"] = df["cap_value_usd"].apply(_classificar_tier)

    return df.sort_values("cap_value_usd", ascending=False)


def free_agents_alvo(
    df_valuation: pd.DataFrame,
    cap_room: float = 50_000_000.0,
    age_max: int = 30,
    top_k: int = 20,
) -> pd.DataFrame:
    """
    Lista candidatos a free agency: tier STAR+ com idade ≤ X e valor compatível com cap.

    Heurística simulada (não há free agency status no dataset):
        - jogadores com cap_value ≤ cap_room
        - idade ≤ age_max (potencial de longevidade)
        - tier STARTER ou superior
    """
    df = df_valuation[
        (df_valuation["cap_value_usd"] <= cap_room) &
        (df_valuation["age"] <= age_max) &
        (df_valuation["tier"].isin(["SUPERSTAR", "STAR", "STARTER"]))
    ].copy()
    return df.sort_values("cap_value_usd", ascending=False).head(top_k)
