"""Painel CLI + dashboard de gráficos NBA."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .analysis import ResultadoAnalytics

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def imprimir(resultado: ResultadoAnalytics, n_jogadores: int, n_temporadas: int,
             output_dir: Path = OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'═'*58}")
    print("  NBA ANALYTICS — EVOLUÇÃO DO JOGO (1996–2023)")
    print(f"  {n_jogadores:,} jogadores · {n_temporadas} temporadas")
    print(f"{'═'*58}")
    print(f"\n  {'Era':<20} {'PPG':>6} {'RPG':>6} {'APG':>6} {'TS%':>6}")
    for _, r in resultado.era_stats.iterrows():
        print(f"  {str(r['era']):<20} {r['pts']:>6.1f} {r['reb']:>6.1f} "
              f"{r['ast']:>6.1f} {r['ts_pct']:>6.3f}")
    print()
    print("  ── Top 5 All-Time (efficiency score, ≥5 temporadas) ──")
    for _, r in resultado.top_players.head(5).iterrows():
        print(f"  {r['player_name']:<28} eff={r['efficiency_med']:.2f}  "
              f"PPG={r['pts_med']:.1f}")
    print()
    td = resultado.test_draft
    print(f"  Draft H: {td['conclusao']} (p={td['p_value']:.4f})")
    print()
    intl_last = resultado.crescimento_internacional.iloc[-1]
    intl_first = resultado.crescimento_internacional.iloc[0]
    print(f"  Internacionais: {intl_first['pct_internacional']:.1%} (1996) "
          f"→ {intl_last['pct_internacional']:.1%} ({int(intl_last['season_start'])})")
    print(f"{'═'*58}\n")

    _evolucao_chart(resultado, output_dir)
    _internacional_chart(resultado, output_dir)
    _top_players_chart(resultado, output_dir)
    _corr_heatmap(resultado, output_dir)
    _draft_chart(resultado, output_dir)
    _paises_chart(resultado, output_dir)


def _evolucao_chart(resultado: ResultadoAnalytics, out: Path):
    df = resultado.evolucao_anual
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    pairs = [
        (axes[0, 0], "pts",        "PPG médio",     "steelblue"),
        (axes[0, 1], "ts_pct",     "True Shooting%","darkorange"),
        (axes[1, 0], "net_rating", "Net Rating",    "green"),
        (axes[1, 1], "ast",        "APG médio",     "purple"),
    ]
    for ax, col, title, color in pairs:
        ax.plot(df["season_start"], df[col], "o-", color=color, lw=2, ms=4)
        ax.set_title(title)
        ax.set_xlabel("Temporada")
        ax.grid(alpha=0.3)
    fig.suptitle("Evolução de Métricas NBA (1996–2023)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out / "evolucao_metricas.png", dpi=150, bbox_inches="tight")
    plt.close()


def _internacional_chart(resultado: ResultadoAnalytics, out: Path):
    df = resultado.crescimento_internacional
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(df["season_start"], df["pct_internacional"] * 100,
                    alpha=0.3, color="steelblue")
    ax.plot(df["season_start"], df["pct_internacional"] * 100, "o-",
            color="steelblue", lw=2, ms=4)
    ax.set_title("Crescimento de Jogadores Internacionais na NBA (%)")
    ax.set_xlabel("Temporada")
    ax.set_ylabel("% de jogadores internacionais")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out / "crescimento_internacional.png", dpi=150, bbox_inches="tight")
    plt.close()


def _top_players_chart(resultado: ResultadoAnalytics, out: Path):
    top = resultado.top_players.head(15).sort_values("efficiency_med")
    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(top["player_name"], top["efficiency_med"], color="gold", edgecolor="gray")
    ax.set_xlabel("Efficiency Score médio")
    ax.set_title("Top 15 Jogadores All-Time — Efficiency Score (≥5 temporadas)")
    ax.grid(alpha=0.3, axis="x")
    for bar, v in zip(bars, top["efficiency_med"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f"{v:.2f}", va="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(out / "top_players.png", dpi=150, bbox_inches="tight")
    plt.close()


def _corr_heatmap(resultado: ResultadoAnalytics, out: Path):
    corr = resultado.correlacoes
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index, fontsize=9)
    plt.colorbar(im, ax=ax)
    for i in range(len(corr)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}",
                    ha="center", va="center", fontsize=7)
    ax.set_title("Correlação de Spearman — Métricas NBA")
    plt.tight_layout()
    plt.savefig(out / "correlacao_metricas.png", dpi=150, bbox_inches="tight")
    plt.close()


def _draft_chart(resultado: ResultadoAnalytics, out: Path):
    df = resultado.draft_performance
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df["draft_round"].astype(str), df["net_rating_med"],
           color=["gold", "steelblue", "gray"][:len(df)])
    ax.set_title("Net Rating Médio por Rodada do Draft")
    ax.set_xlabel("Rodada do Draft")
    ax.set_ylabel("Net Rating médio")
    ax.axhline(0, color="black", lw=1, ls="--")
    ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(out / "draft_performance.png", dpi=150, bbox_inches="tight")
    plt.close()


def _paises_chart(resultado: ResultadoAnalytics, out: Path):
    df = resultado.pais_stats
    fig, ax = plt.subplots(figsize=(9, 6))
    df.sort_values("n_jogadores")[-10:].plot(
        kind="barh", x="country", y="n_jogadores", ax=ax, color="steelblue", legend=False
    )
    ax.set_title("Top 10 Países — Jogadores Únicos na NBA (1996–2023)")
    ax.set_xlabel("Número de jogadores únicos")
    ax.grid(alpha=0.3, axis="x")
    plt.tight_layout()
    plt.savefig(out / "paises_jogadores.png", dpi=150, bbox_inches="tight")
    plt.close()
