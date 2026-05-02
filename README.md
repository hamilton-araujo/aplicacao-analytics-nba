# Front Office NBA — Player Valuation + Trade Advisor

> **A pergunta do GM:** *Tenho $50M de cap room. Quais free agents priorizar? Quais trades fechar antes do deadline? Qual valor justo de contrato?*

Pipeline de NBA Analytics que vai além das tendências históricas: combina **Player Valuation (proxy WAR)** + **lista de free agents alvo** + **trade advisor** com decisão FECHAR/NEGOCIAR/IGNORAR por movimento.

---

## Por que existe

Análise descritiva (top all-time, evolução de eras) é editorial. Front Office decide três coisas:

| Pergunta | Sinal técnico |
|---|---|
| Quanto este jogador vale do cap? | Cap Value = efficiency × min × age_factor × era_factor |
| Quem buscar com $50M? | Free agents tier STAR+, idade ≤ 30 |
| Que trades fazer no deadline? | Δ efficiency vs. Δ cap |

---

## A história em três atos

### Ato 1 — A 24h antes do deadline
Trade deadline às 18h amanhã. GM precisa lista priorizada com cenários. Você roda:
```bash
python -m src.exec_report
```

### Ato 2 — A evidência
2 segundos depois:
```
Jogadores avaliados        539  (season 2022-23)
Superstars                 11
Stars                      46
Free Agents alvo           15
Trades sugeridas (FECHAR)  2
Trades sugeridas (NEGOC.)  3
```

### Ato 3 — A decisão
Os 2 trades **FECHAR** têm Δ efficiency ≥ 5 e cap delta ≤ $10M — execução prioritária. Os 3 **NEGOCIAR** ficam em standby para o final do dia (Δ efficiency ≥ 2, mas cap delta alto).

---

## Modelos

### Cap Value (proxy WAR)
```
base_value  = efficiency_score × (min / 36)
age_factor  = exp(-(idade − 27)² / 200)        # gaussian peak at 27
era_factor  = 1 − (anos_desde_2020) × 0.005    # inflation adjustment
cap_value_$ = base_value × age_factor × era_factor × $1.5M
```
Saída clipada em [$500k, $55M].

### Tiers de Cap Value
| Tier | Range | Caso típico |
|---|---|---|
| SUPERSTAR | ≥ $35M | Top 1% (LeBron, Doncic) |
| STAR | $25–35M | All-Star |
| STARTER | $15–25M | Titular sólido |
| ROTATION | $7–15M | Reserva confiável |
| BENCH | < $7M | Mínimo / 2-way |

### Free Agents Alvo
Filtra: cap_value ≤ cap_room + idade ≤ age_max + tier ≥ STARTER. Top-K por cap value.

### Trade Advisor
1. Identifica 3 piores jogadores por efficiency no roster atual
2. Para cada target do mercado, sugere quem dispensar (cap próximo)
3. Calcula `Δ_efficiency` e `Δ_cap`
4. Decide: **FECHAR** (Δeff ≥ 5 + Δcap ≤ $10M) · **NEGOCIAR** (Δeff ≥ 2) · **IGNORAR**

---

## Stack

| Camada | Tecnologia |
|---|---|
| Dados | NBA Players Data (Kaggle) — 12.844 registros 1996-2023 |
| Estatística | NumPy + scipy (Kruskal-Wallis Draft × Performance) |
| Visualização | matplotlib · 8 charts |

---

## Como rodar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Pipeline executivo (recomendado)
python -m src.exec_report

# Pipeline original (analytics + tendências)
python -m src.main
```

---

## Outputs

```
output/
├── relatorio_gm.md             # ⭐ Briefing GM + decisões trade
├── tiers_distribuicao.png      # ⭐ Distribuição de tiers da liga
├── top_cap_value.png           # ⭐ Top 20 por cap value
├── player_valuation.csv        # ⭐ Tabela completa season alvo
├── free_agents_alvo.csv        # ⭐ 15 free agents priorizados
├── trade_sugestoes.csv         # ⭐ 5 sugestões de trade
└── ... (charts originais)
```

⭐ = adicionado nesta versão.

---

## Estrutura

```
├── src/
│   ├── exec_report.py        # ⭐ Pipeline executivo GM
│   ├── player_valuation.py   # ⭐ Cap value (proxy WAR)
│   ├── trade_advisor.py      # ⭐ FECHAR/NEGOCIAR/IGNORAR por trade
│   ├── ingest.py
│   ├── analysis.py           # Tendências históricas + Kruskal-Wallis
│   ├── report.py             # Painel CLI + 6 charts
│   └── main.py
├── data/
├── output/
├── tests/
└── requirements.txt
```
