# Aplicação Analytics NBA — Evolução do Jogo (1996–2023)

Plataforma de analytics histórico da NBA cobrindo 27 temporadas, 2.551 jogadores e métricas avançadas de performance.

## Dataset

**NBA Players Data** — Kaggle (`justinas/nba-players-data`)  
12.844 registros | 2.551 jogadores | 27 temporadas (1996–2023)

## Stack

| Camada | Tecnologia |
|---|---|
| Análise | pandas · scipy (Kruskal-Wallis) |
| Visualização | matplotlib (6 dashboards) |
| Métricas | Efficiency Score · Net Rating · TS% |

## Insights

```
══════════════════════════════════════════════════════════
  NBA ANALYTICS — EVOLUÇÃO DO JOGO (1996–2023)
══════════════════════════════════════════════════════════
  Era                  PPG    TS%   Net Rating
  Late 90s (96–02)     8.8  0.509      —
  Modern (19+)        10.2  0.564   +12% eficiência

  Top 5 All-Time (efficiency score, ≥5 temporadas):
  1. Luka Doncic     eff=25.76  PPG=27.7
  2. Joel Embiid     eff=24.86  PPG=26.5
  3. LeBron James    eff=24.85  PPG=27.2
  4. Kevin Durant    eff=24.26  PPG=27.2
  5. Nikola Jokic    eff=23.92  PPG=20.4

  Internacionais: 2.0% (1996) → 23.4% (2022)
  Draft Round prediz Net Rating (Kruskal-Wallis p<0.001)
══════════════════════════════════════════════════════════
```

## Estrutura

```
├── src/
│   ├── ingest.py    # Carga e feature engineering (era, efficiency)
│   ├── analysis.py  # Métricas avançadas + testes estatísticos
│   ├── report.py    # Painel CLI + 6 gráficos
│   └── main.py      # CLI argparse
├── data/
├── output/
├── tests/
└── requirements.txt
```
