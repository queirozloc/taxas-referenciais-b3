# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python ETL pipeline to download, clean, interpolate, and export Brazilian daily interest rate curves (Taxas Referenciais B3). Output is a formatted Excel workbook with two sheets: **DI Curve** and **Cupom Cambial Limpo**.

## Status

O script de download está concluído e funcionando. O próximo passo é configurar o **GitHub Actions** para automatizar a coleta diária e disponibilizar o Excel gerado (ex: como artefato de workflow ou commit automático no repositório).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run for today
python main.py

# Run for a single date
python main.py 2026-04-17

# Run for a date range
python main.py 2026-03-16 2026-04-17
```

Output files land in `output/taxas_b3_<start>_<end>.xlsx`. Weekends and Brazilian holidays (where B3 returns empty data) are skipped automatically.

## Architecture

Linear ETL pipeline, one module per stage:

```
main.py
 ├── src/download.py    → fetch base64-encoded CSV from B3 API
 ├── src/clean.py       → parse semicolon-delimited CSV into DataFrame
 ├── src/interpolate.py → cubic spline to standard tenors (scipy)
 └── src/export.py      → formatted .xlsx with two sheets (openpyxl)
```

Shared constants (tenor grids, output dir) live in `src/config.py`.

### Data flow

`fetch_csv(date, curve)` → raw CSV string (base64-decoded, latin-1)  
`parse_csv(csv_text, date)` → DataFrame `[date, tenor_bd, tenor_cd, rate]`  
`interpolate_curve(df, curve)` → DataFrame `[date, tenor, rate]` at standard tenors  
`export_to_excel(di_df, cupom_df, path)` → `.xlsx`

### B3 API

- **Base URL:** `https://sistemaswebb3-derivativos.b3.com.br/referenceRatesProxy/Search/`
- **Endpoint:** `GetDownloadFile/{base64(json_payload)}` — returns a base64-encoded, latin-1, semicolon-delimited CSV
- **Payload fields:** `language`, `id` (product code), `date` (YYYY-MM-DD), `pageNumber`, `pageSize`
- **Required headers:** `Origin` e `Referer` devem apontar para `sistemaswebb3-derivativos.b3.com.br`
- **Curve IDs:** `PRE` = DI curve, `DOC` = Cupom Cambial Limpo (ver `src/download.CURVE_IDS`)
- **`GetDate/{base64}`** retorna as ~20 datas mais recentes com dados disponíveis
- **`GetList/`** ignora o parâmetro de data e sempre retorna o dado mais recente — usar apenas `GetDownloadFile` para dados históricos

### CSV format (after decoding)

```
Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa
DI x pré;1;1;14,65
DI x pré;4;7;14,63
...
```

Colunas usadas: 1 (`tenor_bd`), 2 (`tenor_cd`), 3 (`rate`).

### Tenor grids

Definidos em `src/config.py`:

- **DI Curve** — dias úteis (252/ano): `[1, 63, 126, 189, 252, 378, 504, 630, 756, 1008, 1260]`
- **Cupom Cambial Limpo** — dias corridos (360/ano): `[90, 180, 270, 360, 540, 720, 900, 1080, 1440, 1800, 2520, 2880, 3600]`

### Observações conhecidas

- A B3 ocasionalmente publica a mesma curva em dois dias consecutivos (ex: véspera de feriado). Isso é comportamento da fonte, não bug no código.
- Feriados nacionais retornam resposta vazia e são pulados automaticamente via tratamento de exceção em `main.py`.

## Próximos Passos — Dashboard + Automação

O plano completo está em `C:\Users\queir\.claude\plans\agora-que-temos-o-sprightly-pretzel.md`.

### Resumo do que precisa ser construído

**Novos arquivos:**
- `requirements.txt` — adicionar `plotly`, `pyarrow`, `streamlit` (já adicionado, falta instalar)
- `src/store.py` — `upsert_parquet(df, curve)` e `load_parquet(curve)`: persistência em `data/*.parquet`
- `src/brazil_calendar.py` — feriados nacionais 2024–2027 + `count_business_days(start, end)`
- `src/copom.py` — calendário COPOM 2024–2027 + metodologia **Flat-Forward Copom (FFC)**
- `dashboard/app.py` — entry point Streamlit (sidebar com 4 seções)
- `dashboard/data.py` — `load_di()`, `load_cupom()`, `load_di_raw()` com `@st.cache_data`
- `dashboard/charts.py` — figuras Plotly (`plot_yield_curve_overlay`, `plot_copom_*`)
- `dashboard/download_view.py` — date range picker + `st.download_button` gerando Excel via BytesIO
- `dashboard/copom_view.py` — snapshot + evolução da precificação do COPOM
- `dashboard/fra_view.py` — FRA 1y1y e FRA 5y5y histórico
- `.github/workflows/collect.yml` — cron `0 8 * * 1-5` (8h UTC = 5h BRT)
- `.gitignore`, `.streamlit/config.toml`, `data/.gitkeep`

**Arquivos a modificar:**
- `main.py` — flag `--store`: salva em Parquet em vez de Excel; coleta também frames brutos
- `src/config.py` — adicionar `DATA_DIR = "data"`
- `src/export.py` — `output_path` aceita `str | io.BytesIO`

### Metodologia COPOM (Flat-Forward Copom — FFC)

Baseada em Bristotti (2018) / Carreira & Brostowicz (2016). O CDI/Selic só muda em reuniões do COPOM, logo a taxa forward é constante entre reuniões consecutivas.

**Fórmulas (dias úteis, base 252):**
```
DF(T)          = 1 / (1 + r(T)/100)^(T/252)
f(T1, T2)      = [DF(T1)/DF(T2)]^(252/(T2-T1)) − 1    # forward entre T1 e T2
DF(τ) interp.  = DF(T1) · (1+f)^(−(τ−T1)/252)         # flat-forward entre nós
```

Usar `di_raw.parquet` (pontos brutos ~277/dia) como nós da interpolação, **não** os vértices do spline.

**Taxa implícita para reunião COPOM_i:**  
= forward entre a reunião anterior (COPOM_{i-1}) e COPOM_i, calculado via DF interpolado.

### FRA

Calculado diretamente dos vértices interpolados em `di.parquet`:
```
F(T) = (1 + r(T)/100)^(T/252)
FRA(T1, T2) = (F(T2)/F(T1))^(252/(T2-T1)) − 1
```
- **FRA 1y1y**: T1=252, T2=504
- **FRA 5y5y**: T1=1260, T2=2520

### Estrutura de dados

```
data/
 ├── di.parquet        # [date, tenor, rate] — vértices interpolados DI
 ├── di_raw.parquet    # [date, tenor_bd, tenor_cd, rate] — pontos brutos DI
 ├── cupom.parquet     # [date, tenor, rate] — vértices interpolados Cupom
 └── cupom_raw.parquet # [date, tenor_bd, tenor_cd, rate] — pontos brutos Cupom
```

### GitHub Actions

```yaml
on:
  schedule:
    - cron: "0 8 * * 1-5"   # 8h UTC = 5h BRT, seg–sex
  workflow_dispatch:
permissions:
  contents: write
```

Usa `stefanzweifel/git-auto-commit-action@v5` para commitar os Parquets atualizados. No-op automático em feriados.

### Streamlit Cloud

- Repositório GitHub já existe e é público
- Entry point: `dashboard/app.py`
- Nenhuma variável de ambiente necessária
- Redeploya automaticamente a cada push (i.e., diariamente pelo Actions)
- Primeiro passo: backfill local `python main.py 2024-01-01 <hoje> --store` antes de subir
