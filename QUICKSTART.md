# Setup

```
$ python -c "import sys; print(sys.version)" # check >= 3.13
# $ conda activate python313 (Ian's route to a 3.13 python)
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install -r requirements.txt
```

Next you'll need `.env` from Slack with an OpenRouter API key, you'll want something like

```
$ more .env
OPENROUTER_API_KEY=sk-or-v1-...
```

Now run `llm_openrouter.py` and it'll try to extract a fact from a canned bit of text. If this works and you get some JSON, you're in a good state.

Now try `extraction_and_prompt_example.py` and it'll read the input tsv (see below), run a simple prompt and extract something.

# What's here

Locally you've got a small export from the much larger https://github.com/applicaai/kleister-charity# dataset. I've taken a small set of PDFs (<= 20 pages each) and the relevant exports of text that they've provided (using djvu2hocr, tesseract 4.11, tesseract from march 2020, a combination of all 3). The chosen pdfs come from the `dev-0` folder. 

The PDFs are drawn from a heterogenous collection of UK charity financial documents, from a corpus of circa 3,000 documents of length up to 200 pages.

In `data` we have
* `playgroup_dev_in.tsv` based on `in.tsv`
* `playgroup_dev_expected.tsv` based on `expected.tsv`
* `pdf_names.txt` which lists each pdf name in the same order as `in|expected.tsv` files.

# License

* The data is UK open data see https://github.com/applicaai/kleister-charity/issues/2