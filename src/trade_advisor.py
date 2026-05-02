"""
Trade Advisor — sugere trades antes do deadline.

Por que existe:
    GMs têm 24h até o trade deadline. Decisão tem que estar pronta.
    Trade Advisor cruza time atual × free agents/trade targets do mercado
    e sugere movimentos que melhoram efficiency líquida do roster.

Heurística:
    1. Identificar buracos do time (positions com < 2 jogadores STARTER+)
    2. Sugerir trade target (efficiency superior à média do time)
    3. Calcular delta de efficiency e impacto no cap
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class SugestaoTrade:
    target_player:    str
    target_eff:       float
    target_cap:       float
    quem_sai:         str
    quem_sai_cap:     float
    quem_sai_eff:     float
    delta_efficiency: float
    delta_cap:        float
    recomendacao:     str    # FECHAR / NEGOCIAR / IGNORAR


def _decidir(delta_eff: float, delta_cap: float) -> str:
    if delta_eff >= 5 and delta_cap <= 10_000_000:
        return "FECHAR"
    if delta_eff >= 2:
        return "NEGOCIAR"
    return "IGNORAR"


def sugerir(
    df_team: pd.DataFrame,        # roster atual com cap_value, efficiency_score
    df_market: pd.DataFrame,      # candidatos disponíveis
    n_sugestoes: int = 5,
) -> pd.DataFrame:
    """Devolve top trades por delta de efficiency."""
    if len(df_team) == 0 or len(df_market) == 0:
        return pd.DataFrame()

    pior_no_team = df_team.sort_values("efficiency_score").head(3)

    rows = []
    for _, target in df_market.head(20).iterrows():
        # quem do time substituir? — pior efficiency com cap próximo
        candidatos_saida = pior_no_team[
            (pior_no_team["cap_value_usd"] <= target["cap_value_usd"] * 1.3)
        ]
        if len(candidatos_saida) == 0:
            candidatos_saida = pior_no_team.head(1)

        quem_sai = candidatos_saida.iloc[0]
        delta_eff = target["efficiency_score"] - quem_sai["efficiency_score"]
        delta_cap = target["cap_value_usd"] - quem_sai["cap_value_usd"]
        rec = _decidir(delta_eff, delta_cap)

        rows.append(SugestaoTrade(
            target_player=target.get("player_name", "?"),
            target_eff=float(target["efficiency_score"]),
            target_cap=float(target["cap_value_usd"]),
            quem_sai=quem_sai.get("player_name", "?"),
            quem_sai_cap=float(quem_sai["cap_value_usd"]),
            quem_sai_eff=float(quem_sai["efficiency_score"]),
            delta_efficiency=float(delta_eff),
            delta_cap=float(delta_cap),
            recomendacao=rec,
        ).__dict__)

    df_out = pd.DataFrame(rows).sort_values("delta_efficiency", ascending=False)
    return df_out.head(n_sugestoes)
