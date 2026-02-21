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


if __name__ == "__main__":
    expected_items = get_all_items("data/playgroup_dev_expected.tsv")
    #items = get_all_items("data/playgroup_dev_in.tsv")
    print(expected_items)