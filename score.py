import csv
import glob
import sys

from config_models import VALUE_MODELS


def _mod_tag(model_name):
    cfg = VALUE_MODELS.get(model_name)
    return "MM" if cfg and cfg.get("multimodal") else "text"


def get_all_items(filename):
    items = []
    with open(filename, 'r') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
        for item in reader:
            # e.g.
            # ['address__post_town=SHREWSBURY', 'address__postcode=SY3_7PQ', 'address__street_line=58_TRINITY_STREET', 'charity_name=The_Sanata_Charitable_Trust', 'charity_number=1132766', 'income_annually_in_british_pounds=255653.00', 'report_date=2015-12-31', 'spending_annually_in_british_pounds=258287.00']
            k_v_pairs = dict([itm.split('=', 1) for itm in item if '=' in itm])
            items.append(k_v_pairs)
    return items


def score(expected_items, predicted_items, verbose=True):
    total = 0
    correct = 0
    for row_num, expected_row in enumerate(expected_items):
        predicted_row = predicted_items[row_num] if row_num < len(predicted_items) else {}
        for key, expected_val in expected_row.items():
            total += 1
            predicted_val = predicted_row.get(key)
            if predicted_val == expected_val:
                correct += 1
            elif verbose:
                print(f"  Row {row_num}: {key} expected='{expected_val}' predicted='{predicted_val}'")
    return correct, total


def _load_stats(stats_filename="data/extraction_stats.csv",
                 call_log_filename="data/extraction_call_log.csv"):
    """Load extraction stats keyed by model_short_name.

    Sources (in priority order):
    1. extraction_stats.csv (has totals directly)
    2. extraction_call_log.csv (aggregate per-row entries)
    3. config_models.py pricing × avg tokens (estimate, marked with ~)
    """
    stats = {}
    # 1. Primary: stats CSV
    try:
        with open(stats_filename, 'r') as f:
            for row in csv.DictReader(f):
                elapsed = float(row.get("total_elapsed_secs", 0))
                cost = float(row.get("total_cost_usd", 0))
                if elapsed or cost:
                    stats[row["model_short_name"]] = {
                        "elapsed_secs": elapsed, "cost_usd": cost, "estimated": False,
                    }
    except FileNotFoundError:
        pass

    # 2. Fallback: aggregate from call log
    try:
        with open(call_log_filename, 'r') as f:
            agg = {}
            for row in csv.DictReader(f):
                name = row["model_short_name"]
                if name in stats or row.get("status") == "error":
                    continue
                if name not in agg:
                    agg[name] = {"elapsed": 0.0, "prompt": 0, "completion": 0, "cost": 0.0}
                agg[name]["elapsed"] += float(row.get("elapsed_secs", 0))
                agg[name]["prompt"] += int(row.get("prompt_tokens", 0))
                agg[name]["completion"] += int(row.get("completion_tokens", 0))
                agg[name]["cost"] += float(row.get("cost_usd", 0))
            for name, a in agg.items():
                if a["elapsed"] or a["cost"]:
                    stats[name] = {
                        "elapsed_secs": a["elapsed"], "cost_usd": a["cost"],
                        "estimated": False,
                    }
    except FileNotFoundError:
        pass

    # 3. Estimate for remaining models using config pricing × avg tokens
    known_tokens = [(s["elapsed_secs"], s["cost_usd"])
                    for s in stats.values() if s["elapsed_secs"] > 0]
    if known_tokens:
        avg_elapsed = sum(t for t, _ in known_tokens) / len(known_tokens)
        avg_prompt = 180_000  # typical total prompt tokens across 11 rows
        avg_completion = 1_500
        for model_name, cfg in VALUE_MODELS.items():
            if model_name not in stats:
                price_in = cfg.get("price_in", 0)
                price_out = cfg.get("price_out", 0)
                est_cost = (avg_prompt * price_in + avg_completion * price_out) / 1_000_000
                if est_cost > 0:
                    stats[model_name] = {
                        "elapsed_secs": avg_elapsed, "cost_usd": est_cost,
                        "estimated": True,
                    }

    return stats


def score_all_models(expected_filename, verbose=False):
    expected_items = get_all_items(expected_filename)
    stats = _load_stats()
    results = []
    for predicted_filename in sorted(glob.glob("data/*_dev_extracted__*.tsv")):
        model_name = predicted_filename.split("__", 1)[1].removesuffix(".tsv")
        predicted_items = get_all_items(predicted_filename)
        if verbose:
            print(f"\n--- {model_name} [{_mod_tag(model_name)}] ---")
        correct, total = score(expected_items, predicted_items, verbose=verbose)
        model_stats = stats.get(model_name, {})
        results.append((model_name, correct, total,
                         model_stats.get("elapsed_secs", 0),
                         model_stats.get("cost_usd", 0),
                         model_stats.get("estimated", False)))
    return results


if __name__ == "__main__":
    expected_filename = "data/playgroup_dev_expected.tsv"

    if len(sys.argv) > 1:
        # Score a single specified file
        predicted_filename = sys.argv[1]
        expected_items = get_all_items(expected_filename)
        predicted_items = get_all_items(predicted_filename)
        correct, total = score(expected_items, predicted_items, verbose=True)
        print(f"\nScore: {correct}/{total}")
    else:
        # Score all models
        results = score_all_models(expected_filename, verbose=False)
        print(f"\n{'Model':<25} {'Mod':<6} {'Score':>10}  {'%':>7}  {'Time(s)':>9}  {'Cost($)':>9}")
        print("-" * 75)
        results.sort(key=lambda r: r[1] / r[2] if r[2] else 0, reverse=True)
        for model_name, correct, total, elapsed, cost, estimated in results:
            pct = 100 * correct / total if total else 0
            prefix = "~" if estimated else ""
            time_str = f"{prefix}{elapsed:.1f}" if elapsed else "-"
            cost_str = f"{prefix}{cost:.4f}" if cost else "-"
            print(f"{model_name:<25} {_mod_tag(model_name):<6} {correct:>4}/{total:<4}  {pct:>6.1f}%  {time_str:>9}  {cost_str:>9}")
        print(f"\n  ~ = estimated from config pricing x avg tokens")