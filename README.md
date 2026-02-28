# UK Charity Document Extraction — Multi-Model Benchmark

Extract structured fields from UK charity financial PDFs using LLMs via [OpenRouter](https://openrouter.ai/), then score and rank the results across 40+ models.

---

## Setup

See [`QUICKSTART.md`](QUICKSTART.md) for the full pre-event setup checklist (Python version check, venv, pip install, `.env` with OpenRouter API key).

---

## Smoke Test

Verify your setup works before running anything else:

```bash
python llm_openrouter.py
```

Expected output — a JSON block with a charity number extracted from canned text:

```json
{"Registered Charity Number": "1132766"}
```

---

## End-to-End Workflow

### 1. Try a simple prompt on the dataset

```bash
python extraction_and_prompt_example.py
```

Reads `data/playgroup_dev_in.tsv`, sends each row to `claude-3.5-haiku`, and prints the raw extracted JSON. Good for experimenting with prompts.

### 2. Run extraction across one or more models

Pass one or more model names as arguments, or omit to run all models. Runs are idempotent — if the output file already exists for a model, that model is skipped.

```bash
# One model
python extractor.py gemini-2.0-flash

# Several models
python extractor.py gemini-2.0-flash deepseek-v3 llama-3.3-70b-free

# All models in config_models.py (skips any already completed)
python extractor.py
```

Each run writes `data/playgroup_dev_extracted__<model-name>.tsv` and appends a row to `data/extraction_stats.csv` (row counts and per-field hit rates).

### 3. Score and rank all models

Pass a filename to see a verbose field-by-field diff for one model, or omit to score all extracted files and print a ranked leaderboard.

```bash
# Ranked leaderboard across all extracted files
python score.py

# Verbose diff for one model
python score.py data/playgroup_dev_extracted__gemini-2.0-flash.tsv
```

The leaderboard output looks like:

```
Model                     Mod    Score        %
----------------------------------------------------
gemini-2.5-flash          MM      87/110   79.1%
gemini-2.0-flash          MM      85/110   77.3%
deepseek-v3               text    81/110   73.6%
...
```

---

## What's in This Repo

### Scripts

| File | Purpose |
|---|---|
| `llm_openrouter.py` | Low-level LLM client (OpenRouter API). Run directly for a smoke test. |
| `extraction_and_prompt_example.py` | Simple single-model extraction loop, good for prompt experiments. |
| `extractor.py` | Main extraction runner. Pass model name(s) as args to run specific models; no args runs all models idempotently (skips completed). |
| `score.py` | Scorer. No args → ranked leaderboard across all extracted files. Pass a filename → verbose field-by-field diff for that model. |
| `utils.py` | Shared helpers (`extract_from_triple_backticks`, etc.). |
| `config_models.py` | Model registry — 40+ models organised by tier. |
| `playground.py` | Ad-hoc experiments. |

### Model Tiers (`config_models.py`)

Models are grouped into four tiers by cost (per million input tokens):

| Tier | Cost | Examples |
|---|---|---|
| `free` | $0 | `llama-3.3-70b-free`, `gemini-flash-free`, `qwen3-vl-30b-free` |
| `ultra_cheap` | < $0.30 | `gemini-2.0-flash`, `deepseek-v3`, `qwen-2.5-vl-7b` |
| `great_value` | $0.30–$1.00 | `claude-3.5-haiku`, `qwen-2.5-vl-72b`, `deepseek-r1` |
| `premium` | > $1.00 | `gemini-3-pro`, `pixtral-large`, `mistral-large` |

Each model entry includes: OpenRouter model ID, `multimodal` flag, supported modalities, context length, and notes.

### Data (`data/`)

| File | Description |
|---|---|
| `playgroup_dev_in.tsv` | Input: 11 PDFs × 6 columns (filename, keys, 3 OCR text variants, combined text) |
| `playgroup_dev_expected.tsv` | Ground truth field values |
| `pdf_names.txt` | PDF filenames in row order |
| `playgroup_dev_extracted__<model>.tsv` | Per-model extraction output (one file per run) |
| `extraction_stats.csv` | Cumulative run stats: model, row counts, per-field hit rates |
| `*.pdf` | 11 UK charity financial PDFs (≤ 200 pages each) |

### Visualisations

| File | Description |
|---|---|
| `which-models-extracted-playground.html` | Interactive leaderboard |
| `architecture_animated.svg` | Animated pipeline architecture diagram |
| `performance_animated.svg` | Animated performance comparison |

### Utility Scripts (`utility/`)

| File | Description |
|---|---|
| `process_pdf.py` | PDF processing helper |
| `extract_copy_kleister_charity.sh` | Shell script to copy/prepare data from the full Kleister Charity dataset |

---

## Dataset

A small export from the [Kleister Charity dataset](https://github.com/applicaai/kleister-charity) (`dev-0` folder), using PDFs and pre-extracted OCR text (djvu2hocr, tesseract 4.11, tesseract March 2020, combined).

PDFs are drawn from ~3,000 UK charity financial documents, up to 200 pages each. The 11 in this set start smaller and get longer — a useful proxy for scale testing.

**Fields to extract:**

- `charity_number` — registered charity number
- `charity_name` — full charity name
- `report_date` — period end date (YYYY-MM-DD)
- `income_annually_in_british_pounds` — total annual income
- `spending_annually_in_british_pounds` — total annual expenditure
- `address__postcode` — UK postcode
- `address__post_town` — town/city
- `address__street_line` — street address

---

## License

Data is UK open data — see [Kleister Charity license](https://github.com/applicaai/kleister-charity/issues/2).
