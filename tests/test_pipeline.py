"""Testes unitários do pipeline NBA."""

import numpy as np
import pandas as pd
import pytest

from src.ingest import _limpar
from src.analysis import analisar


def _df_sintetico(n=400, seed=42):
    rng = np.random.default_rng(seed)
    seasons = [f"{y}-{str(y+1)[2:]}" for y in range(1996, 2023)]
    return pd.DataFrame({
        "player_name":       [f"Player{i % 80}" for i in range(n)],
        "team_abbreviation": rng.choice(["LAL", "BOS", "GSW", "MIA", "CHI"], n),
        "age":               rng.integers(19, 38, n).astype(float),
        "player_height":     rng.uniform(175, 215, n),
        "player_weight":     rng.uniform(75, 130, n),
        "college":           rng.choice(["Duke", "Kentucky", "UNC", None], n),
        "country":           rng.choice(["USA", "France", "Nigeria", "Spain", None], n),
        "draft_year":        rng.choice([str(y) for y in range(1996, 2022)] + ["Undrafted"], n),
        "draft_round":       rng.choice(["1", "2", "Undrafted"], n),
        "draft_number":      rng.integers(1, 60, n).astype(str),
        "gp":                rng.integers(5, 82, n),
        "pts":               rng.uniform(3, 32, n),
        "reb":               rng.uniform(1, 15, n),
        "ast":               rng.uniform(0.5, 12, n),
        "net_rating":        rng.uniform(-15, 15, n),
        "oreb_pct":          rng.uniform(0, 0.2, n),
        "dreb_pct":          rng.uniform(0, 0.4, n),
        "usg_pct":           rng.uniform(0.1, 0.4, n),
        "ts_pct":            rng.uniform(0.4, 0.7, n),
        "ast_pct":           rng.uniform(0.05, 0.5, n),
        "season":            rng.choice(seasons, n),
    })


class TestIngest:
    def test_era_criada(self):
        df = _limpar(_df_sintetico())
        assert "era" in df.columns

    def test_efficiency_criada(self):
        df = _limpar(_df_sintetico())
        assert "efficiency" in df.columns
        assert (df["efficiency"] >= 0).all()

    def test_is_international(self):
        df = _limpar(_df_sintetico())
        assert "is_international" in df.columns

    def test_season_start(self):
        df = _limpar(_df_sintetico())
        assert "season_start" in df.columns
        assert df["season_start"].between(1996, 2030).all()


class TestAnalysis:
    def setup_method(self):
        self.df = _limpar(_df_sintetico())

    def test_evolucao_sorted(self):
        r = analisar(self.df)
        anos = r.evolucao_anual["season_start"].tolist()
        assert anos == sorted(anos)

    def test_top_players_nao_vazio(self):
        r = analisar(self.df)
        assert len(r.top_players) >= 1

    def test_correlacoes_simetrica(self):
        r = analisar(self.df)
        diff = (r.correlacoes - r.correlacoes.T).abs().max().max()
        assert diff < 1e-10

    def test_pvalue_valido(self):
        r = analisar(self.df)
        assert 0 <= r.test_draft["p_value"] <= 1
