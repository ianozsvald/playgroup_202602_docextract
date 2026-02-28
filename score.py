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


def score_all_models(expected_filename, verbose=False):
    expected_items = get_all_items(expected_filename)
    results = []
    for predicted_filename in sorted(glob.glob("data/*_dev_extracted__*.tsv")):
        model_name = predicted_filename.split("__", 1)[1].removesuffix(".tsv")
        predicted_items = get_all_items(predicted_filename)
        if verbose:
            print(f"\n--- {model_name} [{_mod_tag(model_name)}] ---")
        correct, total = score(expected_items, predicted_items, verbose=verbose)
        results.append((model_name, correct, total))
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
        print(f"\n{'Model':<25} {'Mod':<6} {'Score':>10}  {'%':>7}")
        print("-" * 52)
        results.sort(key=lambda r: r[1] / r[2] if r[2] else 0, reverse=True)
        for model_name, correct, total in results:
            pct = 100 * correct / total if total else 0
            print(f"{model_name:<25} {_mod_tag(model_name):<6} {correct:>4}/{total:<4}  {pct:>6.1f}%")