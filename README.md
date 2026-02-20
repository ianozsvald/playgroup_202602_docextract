
# Setup

Read `QUICKSTART.md` to get going.

You should be able to run
* `llm_openrouter.py` and it'll try to extract a fact from a canned bit of text. If this works and you get some JSON, you're in a good state.
* `extraction_and_prompt_example.py` and it'll read the input tsv (see below), run a simple prompt and extract something.

# What's here

Locally you've got a small export from the much larger https://github.com/applicaai/kleister-charity# dataset. I've taken a small set of PDFs (<= 20 pages each) and the relevant exports of text that they've provided (using djvu2hocr, tesseract 4.11, tesseract from march 2020, a combination of all 3). The chosen pdfs come from the `dev-0` folder. 

The PDFs are drawn from a heterogenous collection of UK charity financial documents, from a corpus of circa 3,000 documents of length up to 200 pages.

In `data` we have
* `playgroup_dev_in.tsv` based on `in.tsv`
* `playgroup_dev_expected.tsv` based on `expected.tsv`
* `pdf_names.txt` which lists each pdf name in the same order as `in|expected.tsv` files.

# Tasks

Here you have a handful of shorter PDFs. Imagine you have 1000s of varying lengths (up to 200 pages) - you want a fast and _inexpensive_ solution that'll scale. What's the best system you can build, without using super-expensive frontier models, that might scale? Where are the limits?

* run `llm_router.py` and check it is working with your `.env`
* run `extract_and_prompt_example.py` to check a prompt works and something is extracted
* you want to extract
  * charity number
  * reporting date (YYYY-MM-DD)
  * annual income (GBP) for the most recent year
  * annual outgoings (GBP) for the most recent year
  * post code for the charity address
  * other fields are a bonus
* ...
* build an extractor for the input files that generates an output file similar to `playgroup_dev_expected.tsv` maybe called `playgroup_dev_extracted.tsv`
* either try their evaluation (https://github.com/applicaai/kleister-charity?tab=readme-ov-file#evaluation) or build your own
  * consider how close everything should be

# License

* The data is UK open data see https://github.com/applicaai/kleister-charity/issues/2