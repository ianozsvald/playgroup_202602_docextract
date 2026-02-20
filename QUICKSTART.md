Do the following before attending playgroup please.

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

Now run `llm_openrouter.py` and it'll try to extract a fact from a canned bit of text. If this works and you get some JSON, you're in a good state. You should have something like:

```
$ python llm_openrouter.py 
Openrouter API key: %s sk-or-v1-8...
Using model: anthropic/claude-3.5-haiku
{
    "Registered Charity Number": "1132766"
}
```