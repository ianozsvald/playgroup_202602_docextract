import csv
import json
import os
import re
import sys
from datetime import datetime

import llm_openrouter
from config_models import VALUE_MODELS
from utils import sanitize_error_message

IN_FILENAME = "data/playgroup_dev_in.tsv"
STATS_FILENAME = "data/extraction_stats.csv"
CALL_LOG_FILENAME = "data/extraction_call_log.csv"

ALL_FIELDS = [
    "charity_number",
    "charity_name",
    "report_date",
    "income_annually_in_british_pounds",
    "spending_annually_in_british_pounds",
    "address__postcode",
    "address__post_town",
    "address__street_line",
]

PROMPT_TEMPLATE = """You are an expert at extracting information from UK charity financial documents.
You are given a block of text extracted from a UK charity financial document.
Extract the following fields and output them as a JSON block:

- charity_number: the registered charity number (digits only, e.g. "1132766")
- charity_name: the full name of the charity (e.g. "The Sanata Charitable Trust")
- report_date: the reporting period end date in YYYY-MM-DD format
- income_annually_in_british_pounds: total annual income as a number (e.g. 255653.00)
- spending_annually_in_british_pounds: total annual expenditure/outgoings as a number (e.g. 258287.00)
- address__postcode: UK postcode (e.g. "SY3 7PQ")
- address__post_town: the town/city of the charity address (e.g. "SHREWSBURY")
- address__street_line: the street address line (e.g. "58 TRINITY STREET")

Only include fields you are confident about. Output ONLY the JSON block, nothing else.

```
{
    "charity_number": "1132766",
    "charity_name": "The Sanata Charitable Trust",
    "report_date": "2015-12-31",
    "income_annually_in_british_pounds": 255653.00,
    "spending_annually_in_british_pounds": 258287.00,
    "address__postcode": "SY3 7PQ",
    "address__post_town": "SHREWSBURY",
    "address__street_line": "58 TRINITY STREET"
}
```

The raw text from the document follows:

"""

ADDRESS_FIELDS = {"address__postcode", "address__post_town", "address__street_line"}
NUMERIC_FIELDS = {"income_annually_in_british_pounds", "spending_annually_in_british_pounds"}


def _mod_tag(multimodal):
    return "[MM]" if multimodal else "[text]"


def _format_value(key, value):
    if value is None:
        return None
    if key in NUMERIC_FIELDS:
        try:
            num = float(str(value).replace(",", "").replace("£", "").strip())
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return None
    str_val = str(value).strip()
    str_val = str_val.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    if key in ADDRESS_FIELDS:
        str_val = str_val.upper()
    return str_val.replace(" ", "_")


def _parse_llm_response(response_text):
    if not response_text:
        return {}
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return {}
    result = {}
    for key, value in data.items():
        formatted = _format_value(key, value)
        if formatted is not None and formatted != "":
            result[key] = formatted
    return result


def _row_to_tsv_line(fields):
    sorted_pairs = sorted(f"{k}={v}" for k, v in fields.items())
    return "\t".join(sorted_pairs)


CALL_LOG_FIELDS = ["datetime", "model_short_name", "model_full_name", "tier", "multimodal",
                    "row_num", "pdf_filename", "status", "elapsed_secs",
                    "prompt_tokens", "completion_tokens", "cost_usd", "fields_extracted", "error"]


def _append_call_log(row_data):
    write_header = not os.path.exists(CALL_LOG_FILENAME)
    with open(CALL_LOG_FILENAME, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CALL_LOG_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row_data)


def _append_stats(model_short_name, model_cfg, total, rows_with_values, rows_empty, field_counts,
                   total_elapsed_secs=0.0, total_prompt_tokens=0, total_completion_tokens=0, total_cost_usd=0.0):
    fieldnames = (["datetime", "model_short_name", "model_full_name", "tier", "multimodal",
                   "price_in", "price_out", "ctx",
                   "total", "rows_with_values", "rows_empty",
                   "total_elapsed_secs", "total_prompt_tokens", "total_completion_tokens", "total_cost_usd",
                   "avg_secs_per_row", "avg_cost_per_row"] + ALL_FIELDS)
    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_short_name": model_short_name,
        "model_full_name": model_cfg["model"],
        "tier": model_cfg.get("tier", ""),
        "multimodal": model_cfg.get("multimodal", False),
        "price_in": model_cfg.get("price_in", 0),
        "price_out": model_cfg.get("price_out", 0),
        "ctx": model_cfg.get("ctx", 0),
        "total": total,
        "rows_with_values": rows_with_values,
        "rows_empty": rows_empty,
        "total_elapsed_secs": round(total_elapsed_secs, 2),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "avg_secs_per_row": round(total_elapsed_secs / total, 2) if total else 0,
        "avg_cost_per_row": round(total_cost_usd / total, 6) if total else 0,
        **{f: field_counts.get(f, 0) for f in ALL_FIELDS},
    }
    write_header = not os.path.exists(STATS_FILENAME)
    with open(STATS_FILENAME, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    print(f"  Stats appended to {STATS_FILENAME}")


def run_extraction(model_short_name):
    if model_short_name not in VALUE_MODELS:
        available = ", ".join(f"{k}{_mod_tag(VALUE_MODELS[k]['multimodal'])}" for k in VALUE_MODELS)
        print(f"Unknown model '{model_short_name}'. Available: {available}")
        sys.exit(1)
    model_cfg = VALUE_MODELS[model_short_name]
    model = model_cfg["model"]
    multimodal = model_cfg["multimodal"]
    max_ctx_tokens = model_cfg.get("ctx")
    out_filename = f"data/playgroup_dev_extracted__{model_short_name}.tsv"

    if os.path.exists(out_filename):
        print(f"Skipping {model_short_name} {_mod_tag(multimodal)}: {out_filename} already exists")
        return

    print(f"\nModel: {model_short_name} ({model}) {_mod_tag(multimodal)}")
    print(f"Output: {out_filename}")

    price_in = model_cfg.get("price_in", 0)   # $ per 1M input tokens
    price_out = model_cfg.get("price_out", 0)  # $ per 1M output tokens

    rows_with_values = 0
    rows_empty = 0
    field_counts = {}
    total_elapsed_secs = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cost_usd = 0.0

    csv.field_size_limit(10 * 1024 * 1024)  # 10MB — TSV rows contain large OCR text blocks
    with open(IN_FILENAME, "r") as infile, open(out_filename, "w") as outfile:
        reader = csv.reader(infile, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row_num, row in enumerate(reader):
            assert len(row) == 6, f"Expected 6 cols, got {len(row)} in row {row_num}"
            pdf_filename, _keys, text_djvu2hocr, text_tesseract411, text_tesseractmarch2020, text_combined = row

            print(f"Processing row {row_num}: {pdf_filename}")
            call_log_base = {
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model_short_name": model_short_name,
                "model_full_name": model,
                "tier": model_cfg.get("tier", ""),
                "multimodal": multimodal,
                "row_num": row_num,
                "pdf_filename": pdf_filename,
            }
            try:
                result = llm_openrouter.call_llm(model, PROMPT_TEMPLATE, text_combined, max_ctx_tokens=max_ctx_tokens)
                fields = _parse_llm_response(result["text"])
            except Exception as e:
                error_msg = sanitize_error_message(str(e)).replace("\t", " ").replace("\n", " ")
                line = f"error={error_msg}"
                outfile.write(line + "\n")
                rows_empty += 1
                print(f"  -> ERROR: {error_msg[:120]}")
                _append_call_log({**call_log_base, "status": "error", "elapsed_secs": 0,
                                  "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0,
                                  "fields_extracted": 0, "error": error_msg[:500]})
                continue

            # Accumulate cost & time
            row_cost = (result["prompt_tokens"] * price_in + result["completion_tokens"] * price_out) / 1_000_000
            total_elapsed_secs += result["elapsed_secs"]
            total_prompt_tokens += result["prompt_tokens"]
            total_completion_tokens += result["completion_tokens"]
            total_cost_usd += row_cost

            line = _row_to_tsv_line(fields)
            outfile.write(line + "\n")

            if fields:
                rows_with_values += 1
                print(f"  -> {line[:100]}  [{result['elapsed_secs']}s, ${row_cost:.6f}]")
                for key in fields:
                    field_counts[key] = field_counts.get(key, 0) + 1
            else:
                rows_empty += 1
                print(f"  -> (no values extracted)  [{result['elapsed_secs']}s]")

            _append_call_log({**call_log_base, "status": "ok" if fields else "empty",
                              "elapsed_secs": result["elapsed_secs"],
                              "prompt_tokens": result["prompt_tokens"],
                              "completion_tokens": result["completion_tokens"],
                              "cost_usd": round(row_cost, 6),
                              "fields_extracted": len(fields), "error": ""})

    total = rows_with_values + rows_empty
    print(f"\n--- {model_short_name} {_mod_tag(multimodal)} summary ---")
    print(f"  Rows with values : {rows_with_values}/{total}")
    print(f"  Rows empty       : {rows_empty}/{total}")
    print(f"  Total time       : {total_elapsed_secs:.1f}s")
    print(f"  Total tokens     : {total_prompt_tokens} in / {total_completion_tokens} out")
    print(f"  Total cost       : ${total_cost_usd:.6f}")
    if field_counts:
        print("  Fields found (out of rows with values):")
        for field, count in sorted(field_counts.items()):
            print(f"    {field}: {count}/{rows_with_values}")
    _append_stats(model_short_name, model_cfg, total, rows_with_values, rows_empty, field_counts,
                  total_elapsed_secs, total_prompt_tokens, total_completion_tokens, total_cost_usd)


if __name__ == "__main__":
    models_to_run = sys.argv[1:] if len(sys.argv) > 1 else list(VALUE_MODELS)
    for model_short_name in models_to_run:
        run_extraction(model_short_name)
