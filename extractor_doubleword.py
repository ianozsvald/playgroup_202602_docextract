"""Doubleword batch extraction orchestrator — parallel to extractor.py but using the Doubleword Batch API."""

import argparse
import asyncio
import csv
import os
import sys

import llm_doubleword
from config_models_doubleword import DOUBLEWORD_MODELS
from extractor import (
    ALL_FIELDS,
    IN_FILENAME,
    PROMPT_TEMPLATE,
    STATS_FILENAME,
    _append_stats,
    _mod_tag,
    _parse_llm_response,
    _row_to_tsv_line,
)
from utils import sanitize_error_message


async def _process_row(
    client,
    model_name: str,
    row_num: int,
    pdf_filename: str,
    text_combined: str,
) -> dict:
    """Process a single row via the Doubleword batch API. Returns result dict."""
    print(f"Processing row {row_num}: {pdf_filename}")
    try:
        response_text = await llm_doubleword.call_llm(client, model_name, PROMPT_TEMPLATE, text_combined)
        fields = _parse_llm_response(response_text)
        return {"row_num": row_num, "fields": fields, "error": None}
    except Exception as e:
        error_msg = sanitize_error_message(str(e)).replace("\t", " ").replace("\n", " ")
        print(f"  -> ERROR row {row_num}: {error_msg[:120]}")
        return {"row_num": row_num, "fields": None, "error": error_msg}


async def run_extraction(model_short_name: str, completion_window: str = "1h", batch_size: int = 100) -> None:
    """Run extraction for a single model using the Doubleword batch API."""
    if model_short_name not in DOUBLEWORD_MODELS:
        available = ", ".join(f"{k}{_mod_tag(DOUBLEWORD_MODELS[k]['multimodal'])}" for k in DOUBLEWORD_MODELS)
        print(f"Unknown model '{model_short_name}'. Available: {available}")
        sys.exit(1)

    model_cfg = DOUBLEWORD_MODELS[model_short_name]
    model = model_cfg["model"]
    multimodal = model_cfg["multimodal"]
    out_filename = f"data/playgroup_dev_extracted__{model_short_name}.tsv"

    if os.path.exists(out_filename):
        print(f"Skipping {model_short_name} {_mod_tag(multimodal)}: {out_filename} already exists")
        return

    print(f"\nModel: {model_short_name} ({model}) {_mod_tag(multimodal)}")
    print(f"Output: {out_filename}")
    print(f"Batch config: completion_window={completion_window}, batch_size={batch_size}")

    # Load all rows
    csv.field_size_limit(10 * 1024 * 1024)
    rows = []
    with open(IN_FILENAME, "r") as infile:
        reader = csv.reader(infile, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row_num, row in enumerate(reader):
            assert len(row) == 6, f"Expected 6 cols, got {len(row)} in row {row_num}"
            pdf_filename = row[0]
            text_combined = row[5]
            rows.append((row_num, pdf_filename, text_combined))

    print(f"Loaded {len(rows)} rows, submitting as batch...")

    client = llm_doubleword.create_client(
        completion_window=completion_window,
        batch_size=batch_size,
    )
    try:
        tasks = [
            _process_row(client, model, row_num, pdf_filename, text_combined)
            for row_num, pdf_filename, text_combined in rows
        ]
        results = await asyncio.gather(*tasks)
    finally:
        await client.close()

    # Sort by row_num to preserve original order
    results.sort(key=lambda r: r["row_num"])

    # Write output and compute stats
    rows_with_values = 0
    rows_empty = 0
    field_counts = {}

    with open(out_filename, "w") as outfile:
        for result in results:
            if result["error"]:
                outfile.write(f"error={result['error'][:500]}\n")
                rows_empty += 1
                continue

            fields = result["fields"]
            line = _row_to_tsv_line(fields)
            outfile.write(line + "\n")

            if fields:
                rows_with_values += 1
                print(f"  row {result['row_num']} -> {line[:100]}")
                for key in fields:
                    field_counts[key] = field_counts.get(key, 0) + 1
            else:
                rows_empty += 1
                print(f"  row {result['row_num']} -> (no values extracted)")

    total = rows_with_values + rows_empty
    print(f"\n--- {model_short_name} {_mod_tag(multimodal)} summary ---")
    print(f"  Rows with values : {rows_with_values}/{total}")
    print(f"  Rows empty       : {rows_empty}/{total}")
    if field_counts:
        print("  Fields found (out of rows with values):")
        for field, count in sorted(field_counts.items()):
            print(f"    {field}: {count}/{rows_with_values}")

    # Batch API doesn't return per-request token counts, so pass zeros
    _append_stats(model_short_name, model_cfg, total, rows_with_values, rows_empty, field_counts)


async def main() -> None:
    """Parse CLI args and run extraction for each model."""
    parser = argparse.ArgumentParser(description="Extract charity data using Doubleword Batch API")
    parser.add_argument("models", nargs="*", default=list(DOUBLEWORD_MODELS),
                        help="Model short names to run (default: all)")
    parser.add_argument("--completion-window", default="1h", choices=["1h", "24h"],
                        help="Batch completion window (default: 1h)")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Requests per batch (default: 100)")
    args = parser.parse_args()

    for model_short_name in args.models:
        await run_extraction(model_short_name, args.completion_window, args.batch_size)


if __name__ == "__main__":
    asyncio.run(main())
