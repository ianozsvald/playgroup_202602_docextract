import csv
import llm_openrouter

IN_FILENAME = 'data/playgroup_dev_in.tsv'

prompt_template_charity_number = """
You are an expert at extracting information from UK charity financial documents.
You are given a block of text that has been extracted from a UK charity financial document.
You need to extract the following items from the block of text:
* Registered Charity Number

You need to output the extracted information in a JSON block, for example:
```
{
    "Registered Charity Number": "1234567890"
}

The raw text from the document follows, after this please output the extracted information in a JSON block:

"""

prompt_template_income = """
You are an expert at extracting information from UK charity financial documents.
You are given a block of text that has been extracted from a UK charity financial document.
You need to extract the following items from the block of text:
* Annual income British Pounds for the most recent year (rounded to whole number, no commas or spaces)

You need to output the extracted information in a JSON block, for example:
```
{
    "Annual income": "123456"
}

The raw text from the document follows, after this please output the extracted information in a JSON block:

"""


if __name__ == "__main__":

    model = "anthropic/claude-3.5-haiku"
    prompt_template = prompt_template_charity_number
    #prompt_template = prompt_template_income

    # read the Kleister Charity dataset and their extracted text
    with open(IN_FILENAME, 'r') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
        for item in reader:
            assert len(item) == 6
            # see https://github.com/applicaai/kleister-charity?tab=readme-ov-file#format-of-the-test-sets
            pdf_filename, keys_ignore, text_djvu2hocr, text_tesseract411, text_tesseractmarch2020, text_combined = item

            # call llm
            response = llm_openrouter.call_llm(model, prompt_template, text_djvu2hocr)
            print(response)