"""
NBA Analytics: métricas avançadas e tendências históricas.

Análises:
  1. Evolução de scoring/eficiência por era
  2. Crescimento de jogadores internacionais
  3. Draft Round vs Performance (net_rating)
  4. Top players all-time por efficiency score
  5. Correlação entre métricas avançadas
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

MIN_GP = 20


@dataclass
class ResultadoAnalytics:
    evolucao_anual: pd.DataFrame       # season_start | pts_med | ts_pct_med | net_rating_med
    crescimento_internacional: pd.DataFrame  # season_start | pct_internacional
    draft_performance: pd.DataFrame    # draft_round | net_rating_med | pts_med | count
    top_players: pd.DataFrame          # top 20 all-time por efficiency
    correlacoes: pd.DataFrame          # matriz de correlação
    era_stats: pd.DataFrame            # era | pts | reb | ast | ts_pct
    pais_stats: pd.DataFrame           # top 10 países por jogadores
    test_draft: dict                   # Kruskal-Wallis draft round vs net_rating


def analisar(df: pd.DataFrame) -> ResultadoAnalytics:
    df_gp = df[df["gp"] >= MIN_GP].copy()

    evolucao = (
        df_gp.groupby("season_start")[["pts", "ts_pct", "net_rating", "ast", "reb"]]
        .mean()
        .reset_index()
        .sort_values("season_start")
    )

    intl = (
        df.groupby("season_start")["is_international"]
        .mean()
        .reset_index()
        .rename(columns={"is_international": "pct_internacional"})
    )

    draft = (
        df_gp.dropna(subset=["draft_round"])
        .groupby("draft_round")[["net_rating", "pts", "ts_pct"]]
        .agg(net_rating_med=("net_rating", "mean"),
             pts_med=("pts", "mean"),
             ts_pct_med=("ts_pct", "mean"),
             contagem=("pts", "count"))
        .reset_index()
        .sort_values("draft_round")
        .head(3)
    )

    top = (
        df_gp.groupby("player_name")
        .agg(efficiency_med=("efficiency", "mean"),
             pts_med=("pts", "mean"),
             reb_med=("reb", "mean"),
             ast_med=("ast", "mean"),
             ts_pct_med=("ts_pct", "mean"),
             net_rating_med=("net_rating", "mean"),
             temporadas=("season", "nunique"))
        .query("temporadas >= 5")
        .sort_values("efficiency_med", ascending=False)
        .head(20)
        .reset_index()
    )

    corr_cols = ["pts", "reb", "ast", "net_rating", "usg_pct", "ts_pct", "efficiency"]
    correlacoes = df_gp[corr_cols].corr(method="spearman")

    era_stats = (
        df_gp.groupby("era", observed=True)[["pts", "reb", "ast", "ts_pct"]]
        .mean()
        .reset_index()
    )

    paises = (
        df.groupby("country")["player_name"]
        .nunique()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .rename(columns={"player_name": "n_jogadores"})
    )

    # Kruskal-Wallis: draft round 1 vs 2 vs undrafted
    g1 = df_gp.loc[df_gp["draft_round"] == 1, "net_rating"].dropna().values
    g2 = df_gp.loc[df_gp["draft_round"] == 2, "net_rating"].dropna().values
    gu = df_gp.loc[df_gp["draft_round"].isna(), "net_rating"].dropna().values
    stat, p = stats.kruskal(g1, g2, gu)
    test_draft = {
        "statistic": float(stat), "p_value": float(p),
        "conclusao": "Draft round prediz net_rating" if p < 0.05 else "Sem diferença",
    }

    logger.info("Top player: %s (efficiency=%.2f)",
                top.iloc[0]["player_name"], top.iloc[0]["efficiency_med"])
    return ResultadoAnalytics(
        evolucao_anual=evolucao,
        crescimento_internacional=intl,
        draft_performance=draft,
        top_players=top,
        correlacoes=correlacoes,
        era_stats=era_stats,
        pais_stats=paises,
        test_draft=test_draft,
    )
