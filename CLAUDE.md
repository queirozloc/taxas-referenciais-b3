# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python ETL pipeline to download, clean, interpolate, and export Brazilian daily interest rate curves (Taxas Referenciais B3). Includes a Streamlit dashboard with Yield Curve, Download, COPOM study (FFC), and FRA views, plus GitHub Actions for daily automated collection.

## Status (atualizado 2026-05-03)

**Concluído e funcionando:**
- ETL pipeline (download → parse → spline → Excel/Parquet)
- Dashboard Streamlit (`streamlit run dashboard/app.py`) com 4 seções
- GitHub Actions: cron `0 8 * * 1-5` commitando `data/*.parquet` diariamente
- Repositório público: `github.com/queirozloc/taxas-referenciais-b3`
- Dados disponíveis: 2026-03-27 a 2026-04-30 (23 datas — limite da API B3)

**Limitação conhecida da API B3:** `GetDownloadFile` retorna apenas as ~25 datas mais recentes. Não há acesso histórico via esta API. Os dados acumulam dia a dia pelo Actions.

**Função COPOM corrigida e commitada:**
- `src/copom.py`: `COPOM_MEETINGS` usa o **primeiro dia útil APÓS a decisão** (quando a nova Selic entra em vigor) para 2024, 2025 e 2026.
- Datas 2026: Jan/29, Mar/19, Abr/30, Jun/18, Ago/06, Set/17, Nov/05, Dez/10
- 2027 ausente (sem calendário oficial BCB publicado)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run for today → Excel
python main.py

# Run for a single date → Excel
python main.py 2026-04-17

# Run for a date range → Excel
python main.py 2026-03-16 2026-04-17

# Run with --store → saves to data/*.parquet (4 files)
python main.py --store
python main.py 2026-04-17 --store

# Run dashboard locally
streamlit run dashboard/app.py
```

Output Excel: `output/taxas_b3_<start>_<end>.xlsx`. Weekends and Brazilian holidays are skipped automatically.

## Architecture

```
main.py                        (--store flag: Parquet vs Excel)
├── src/download.py            → fetch base64-encoded CSV from B3 API
├── src/clean.py               → parse semicolon-delimited CSV into DataFrame
├── src/interpolate.py         → cubic spline to standard tenors (scipy)
├── src/export.py              → formatted .xlsx (str | BytesIO)
├── src/store.py               → upsert_parquet / load_parquet
├── src/brazil_calendar.py     → feriados nacionais 2024-2026 + count_business_days
├── src/copom.py               → COPOM_MEETINGS + FFC methodology
└── src/config.py              → tenor grids, OUTPUT_DIR, DATA_DIR

dashboard/
├── app.py                     → Streamlit entry point (4 sections via sidebar)
├── data.py                    → load_di/cupom/di_raw com @st.cache_data
├── charts.py                  → Plotly figures (spline curve, COPOM bars, FRA lines)
├── yield_curve_view.py        → sobreposição de curvas por data
├── download_view.py           → date range picker + st.download_button → Excel
├── copom_view.py              → snapshot FFC + evolução + download CSV/Excel
└── fra_view.py                → FRA 1y1y (T1=252, T2=504) e FRA 5y5y (T1=1260, T2=2520)

data/
├── di.parquet                 → [date, tenor, rate] interpolados
├── di_raw.parquet             → [date, tenor_bd, tenor_cd, rate] pontos brutos
├── cupom.parquet
└── cupom_raw.parquet

.github/workflows/collect.yml  → cron 0 8 * * 1-5 (5h BRT)
```

## Data flow

`fetch_csv(date, curve)` → raw CSV string (base64-decoded, latin-1)
`parse_csv(csv_text, date)` → DataFrame `[date, tenor_bd, tenor_cd, rate]`
`interpolate_curve(df, curve)` → DataFrame `[date, tenor, rate]` at standard tenors
`export_to_excel(di_df, cupom_df, path)` → `.xlsx`

## B3 API

- **Base URL:** `https://sistemaswebb3-derivativos.b3.com.br/referenceRatesProxy/Search/`
- **Endpoint:** `GetDownloadFile/{base64(json_payload)}` — returns base64-encoded, latin-1, semicolon-delimited CSV
- **Payload fields:** `language`, `id` (product code), `date` (YYYY-MM-DD), `pageNumber`, `pageSize`
- **Required headers:** `Origin` e `Referer` → `sistemaswebb3-derivativos.b3.com.br`
- **Curve IDs:** `PRE` = DI curve, `DOC` = Cupom Cambial Limpo
- **`GetDate/{base64}`** retorna as ~20 datas mais recentes disponíveis
- **`GetList/`** ignora data, retorna sempre o mais recente — não usar para histórico

## Tenor grids (`src/config.py`)

- **DI Curve** — dias úteis (252/ano): `[1, 63, 126, 189, 252, 378, 504, 630, 756, 1008, 1260]`
  - No gráfico: tenor=1 excluído (overnight, distorce a curva visual)
- **Cupom Cambial Limpo** — dias corridos (360/ano): `[90, 180, 270, 360, 540, 720, 900, 1080, 1440, 1800, 2520, 2880, 3600]`

## Metodologia COPOM — Flat-Forward Copom (FFC)

Baseada em Bristotti (2018) / Carreira & Brostowicz (2016). O CDI/Selic só muda em reuniões do COPOM, logo a taxa forward é constante entre reuniões consecutivas. Usa `di_raw.parquet` (~277 pontos brutos/dia) como nós, **não** os vértices do spline.

**Convenção de data:** `COPOM_MEETINGS` contém o **primeiro dia útil após a decisão** (quando a nova Selic entra em vigor) — sempre quinta-feira, ou sexta se quinta for feriado.

**Fórmulas (dias úteis, base 252):**
```
DF(T)     = 1 / (1 + r(T)/100)^(T/252)
f(T1, T2) = [DF(T1)/DF(T2)]^(252/(T2-T1)) − 1
DF(τ)     = DF(T1) · (1+f)^(−(τ−T1)/252)   # flat-forward entre nós
```

**Snapshot:** taxa implícita por reunião + coluna "Variação (bps)" vs reunião anterior (âncora: DI1 overnight como proxy do Selic atual).

**Evolução:** série histórica da taxa implícita para uma reunião específica. Download em CSV e Excel disponíveis.

## FRA

Calculado dos vértices interpolados em `di.parquet`:
```
F(T)         = (1 + r(T)/100)^(T/252)
FRA(T1, T2)  = (F(T2)/F(T1))^(252/(T2-T1)) − 1
```
- **FRA 1y1y**: T1=252, T2=504 (taxa de 1 ano daqui a 1 ano)
- **FRA 5y5y**: T1=1260, T2=2520 (taxa de 5 anos daqui a 5 anos)

## Dashboard — Yield Curve

Usa CubicSpline `bc_type="not-a-knot"` com 300 pontos densos para renderização suave — mesma matemática do pipeline. Tenor=1 excluído do gráfico. Suporta sobreposição de múltiplas datas (última, 1 semana, 1 mês, 1 ano, custom). Tabela com valores exatos abaixo do gráfico.

## Observações conhecidas

- A B3 API retorna apenas as ~25 datas mais recentes. Histórico só cresce via Actions diário.
- A B3 ocasionalmente publica a mesma curva em dois dias consecutivos (véspera de feriado). Comportamento da fonte, não bug.
- Feriados nacionais retornam resposta vazia e são pulados automaticamente.
- Corpus Christi 2025 (19/06) cai no dia após a decisão COPOM de jun/25 → data efetiva = 20/06.

## Próximos passos

- [ ] Fazer deploy no Streamlit Cloud (`share.streamlit.io` → repo `queirozloc/taxas-referenciais-b3` → `dashboard/app.py`)
- [ ] Atualizar `COPOM_MEETINGS` com calendário 2027 quando BCB publicar (nov/2026)
