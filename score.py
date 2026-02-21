import csv

def get_all_items(filename):
    items = []
    with open(filename, 'r') as tsvfile:
        #reader = csv.reader(tsvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
        reader = csv.reader(tsvfile, delimiter=' ', quoting=csv.QUOTE_NONE)
        for item in reader:
            # e.g. 
            # ['address__post_town=SHREWSBURY', 'address__postcode=SY3_7PQ', 'address__street_line=58_TRINITY_STREET', 'charity_name=The_Sanata_Charitable_Trust', 'charity_number=1132766', 'income_annually_in_british_pounds=255653.00', 'report_date=2015-12-31', 'spending_annually_in_british_pounds=258287.00']
            k_v_pairs = dict([itm.split('=') for itm in item])
            items.append(k_v_pairs)
    return items


def score(expected_items, predicted_items):
    total = 0
    correct = 0
    for row_num, expected_row in enumerate(expected_items):
        predicted_row = predicted_items[row_num] if row_num < len(predicted_items) else {}
        for key, expected_val in expected_row.items():
            total += 1
            predicted_val = predicted_row.get(key)
            if predicted_val == expected_val:
                correct += 1
            else:
                print(f"Row {row_num}: {key} expected='{expected_val}' predicted='{predicted_val}'")
    print(f"\nScore: {correct}/{total}")


if __name__ == "__main__":
    expected_filename = "data/playgroup_dev_expected.tsv"
    # this example is a copy of playgroup_dev_expected with a few changes
    predicted_filename = "data/predicted_example.tsv"
    expected_items = get_all_items(expected_filename)
    predicted_items = get_all_items(predicted_filename)
    score(expected_items, predicted_items)