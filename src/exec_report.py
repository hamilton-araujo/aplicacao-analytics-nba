"""
Relatório executivo GM — Player Valuation + Free Agency + Trade Advisor.
"""

import io
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest import carregar
from src.player_valuation import calcular as calcular_valor, free_agents_alvo
from src.trade_advisor import sugerir

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

CORES_TIER = {
    "SUPERSTAR": "#9b59b6", "STAR": "#3498db",
    "STARTER": "#27ae60", "ROTATION": "#f39c12", "BENCH": "#95a5a6",
}


def _grafico_tiers(df: pd.DataFrame, out: Path):
    counts = df["tier"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 6))
    ordem = ["SUPERSTAR", "STAR", "STARTER", "ROTATION", "BENCH"]
    counts = counts.reindex(ordem).fillna(0)
    cs = [CORES_TIER[t] for t in counts.index]
    ax.pie(counts.values, labels=counts.index, colors=cs,
           autopct=lambda p: f"{int(p * counts.sum() / 100):,}",
           startangle=90, wedgeprops=dict(edgecolor="white", linewidth=2))
    ax.set_title(f"Distribuição de Tiers — {int(counts.sum()):,} jogadores")
    plt.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _grafico_top_valor(df_top: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(11, 7))
    df_top = df_top.head(20).iloc[::-1]
    cs = [CORES_TIER.get(t, "#bdc3c7") for t in df_top["tier"]]
    ax.barh(df_top["player_name"], df_top["cap_value_usd"] / 1e6, color=cs, alpha=0.85)
    ax.set_xlabel("Cap Value Estimado (USD M)")
    ax.set_title("Top 20 jogadores — Cap Value (proxy WAR)")
    ax.grid(alpha=0.3, axis="x")
    plt.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info("Carregando NBA dataset...")
    df = carregar()

    # Filtra última temporada disponível
    if "season" in df.columns:
        season_alvo = df["season"].max()
        df_season = df[df["season"] == season_alvo].copy()
    else:
        season_alvo = "2022-23"
        df_season = df.copy()

    logger.info("Calculando Player Valuation (season %s)...", season_alvo)
    df_val = calcular_valor(df, season_alvo=season_alvo)
    df_val.to_csv(OUTPUT_DIR / "player_valuation.csv", index=False)

    logger.info("Identificando free agents alvo...")
    df_fa = free_agents_alvo(df_val, cap_room=50_000_000, age_max=30, top_k=15)
    df_fa.to_csv(OUTPUT_DIR / "free_agents_alvo.csv", index=False)

    # Time hipotético: 12 jogadores aleatórios da base
    df_team = df_val.iloc[10:22].copy()  # mid-tier roster

    logger.info("Sugerindo trades...")
    df_trades = sugerir(df_team, df_fa, n_sugestoes=5)
    df_trades.to_csv(OUTPUT_DIR / "trade_sugestoes.csv", index=False)

    # Charts
    _grafico_tiers(df_val, OUTPUT_DIR / "tiers_distribuicao.png")
    _grafico_top_valor(df_val, OUTPUT_DIR / "top_cap_value.png")

    # Markdown
    n_super = (df_val["tier"] == "SUPERSTAR").sum()
    n_star = (df_val["tier"] == "STAR").sum()
    cap_team = float(df_team["cap_value_usd"].sum())

    lines = [
        "# Front Office NBA — Decisão GM",
        "",
        "## Sumário Executivo",
        "",
        f"- **Temporada analisada:** {season_alvo}",
        f"- **Jogadores avaliados:** {len(df_val):,}",
        f"- **Superstars (cap ≥ $35M):** {int(n_super)}",
        f"- **Stars (cap $25-35M):** {int(n_star)}",
        f"- **Cap atual do roster (12 jogadores):** USD {cap_team/1e6:.1f}M",
        f"- **Cap room disponível:** USD 50.0M",
        "",
        "---",
        "",
        "## 1. Distribuição de Tiers da Liga",
        "",
        "![Tiers](tiers_distribuicao.png)",
        "",
        "## 2. Top 20 Jogadores por Cap Value",
        "",
        "![Top Valor](top_cap_value.png)",
        "",
        "## 3. Free Agents Alvo (cap ≤ $50M, idade ≤ 30)",
        "",
        "| Jogador | Idade | Tier | Efficiency | Cap Value |",
        "|---|---|---|---|---|",
    ]
    for _, r in df_fa.head(10).iterrows():
        lines.append(
            f"| {r.get('player_name', '?')} | {int(r['age'])} | {r['tier']} | "
            f"{r['efficiency_score']:.1f} | USD {r['cap_value_usd']/1e6:.1f}M |"
        )

    lines += [
        "",
        "## 4. Sugestões de Trade",
        "",
        "| Target | Δ Efficiency | Δ Cap | Quem Sai | Recomendação |",
        "|---|---|---|---|---|",
    ]
    for _, r in df_trades.iterrows():
        emoji = {"FECHAR": "✅", "NEGOCIAR": "⚠️", "IGNORAR": "❌"}.get(r["recomendacao"], "—")
        lines.append(
            f"| {r['target_player']} | {r['delta_efficiency']:+.1f} | "
            f"USD {r['delta_cap']/1e6:+.1f}M | {r['quem_sai']} | "
            f"{emoji} {r['recomendacao']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Metodologia",
        "",
        "- **Cap Value (proxy WAR)**: efficiency × (min/36) × age_factor × era_factor × $1.5M",
        "- **Age factor**: pico em 27 anos (curva gaussiana σ²=200).",
        "- **Era factor**: ajuste inflacionário 0.5%/ano desde 2020.",
        "- **Tiers**: SUPERSTAR ≥ $35M · STAR ≥ $25M · STARTER ≥ $15M · ROTATION ≥ $7M · BENCH < $7M.",
        "- **Trade decision**: FECHAR (Δeff ≥ 5 + Δcap ≤ $10M), NEGOCIAR (Δeff ≥ 2), IGNORAR (resto).",
    ]
    (OUTPUT_DIR / "relatorio_gm.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{'═'*60}")
    print(f"  FRONT OFFICE NBA — DECISÃO GM ({season_alvo})")
    print(f"{'═'*60}")
    print(f"  Jogadores avaliados        {len(df_val):,}")
    print(f"  Superstars                 {int(n_super)}")
    print(f"  Stars                      {int(n_star)}")
    print(f"  Free Agents alvo           {len(df_fa)}")
    print(f"  Trades sugeridas (FECHAR)  {(df_trades['recomendacao'] == 'FECHAR').sum()}")
    print(f"  Trades sugeridas (NEGOC.)  {(df_trades['recomendacao'] == 'NEGOCIAR').sum()}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
