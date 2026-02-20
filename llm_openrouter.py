import json
import os

from dotenv import load_dotenv
from openai import OpenAI
import utils

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)

def _get_providers(model_name):
    only_providers = "unspecified"
    # https://openrouter.ai/deepseek/deepseek-v3.2-speciale
    if model_name.startswith("deepseek/deepseek-v3.2-speciale"):
        only_providers = ["atlas-cloud"]
    # https://openrouter.ai/deepseek/deepseek-v3.1-terminus
    if model_name.startswith("deepseek/deepseek-v3.1-terminus"):
        only_providers = ["atlas-cloud"]
    if model_name.startswith("z-ai/glm-4.7"):
        only_providers = ["z-ai"]
    if model_name.startswith("anthropic"):
        only_providers = None  # ["anthropic"] gives 521 and 520 errors intermittently
    if model_name.startswith("openai"):
        only_providers = None
    
    # IF YOU GET THIS, you need to add a provider as I've done above
    # to fix 1 single provider for consistency of calls
    assert only_providers != "unspecified", "No provider found for {model_name}, you need to set one in the code"
    return only_providers

def call_llm(model_name, prompt_template, extracted_text):
    instructions = "Follow the instructions in the prompt template.\n"
    prompt = prompt_template + extracted_text

    print(prompt)
    # NOTE we need 'only_providers' to be set otherwise
    # openroute will fall back on other providers with different configurations
    # and quantization levels and we'll get inconsistent results
    only_providers = _get_providers(model_name)
    extra_params = {"provider": {"allow_fallbacks": False, "only": only_providers}}
    print(f"LLM calling with {model_name}")
    # extra_params = {}
    while True:
        try:
            response = client.responses.create(
                model=model_name,
                instructions=instructions,
                input=prompt,
                extra_body=extra_params,
            )
            break  # jump out if we're successful
        except json.JSONDecodeError:
            print("Oops, got a JSONDecodeError after calling LLM")

    print(f"Raw return from llm call:\n{response.output_text}")
    extracted = utils.extract_from_triple_backticks(response.output_text)
    print(f"Extracted answer:\n{extracted}")
    return extracted


if __name__ == "__main__":
    print(f"Openrouter API key: {os.getenv('OPENROUTER_API_KEY')}")

    #model_name = "deepseek/deepseek-v3.2-speciale"
    #model_name = "z-ai/glm-4.7"  # slow
    #model_name = "anthropic/claude-3-haiku" # failed to give the right answer to the q below
    model_name = "xanthropic/claude-3.5-haiku"

    prompt_template = """
    You are an expert at extracting information from UK charity financial documents.
    You are given a block of text that has been extracted from a UK charity financial document.
    You need to extract the following items from the block of text:
    * Registered Charity Number

    You need to output the extracted information in a JSON block, for example:
    ```
    {
        "Registered Charity Number": "1234567890"
    }
    ```

    The raw text from the document follows, after this please output the extracted information in a JSON block:
    """

    extracted_text= """
    "THE SANATA CHARITABLE TRUST\\nCompany Registration Number:\\n06999163\\n(England and Wales)\\nRegistered Charity Number\\n1132766\\nTrustees' Report and Unaudited Financial Statements\\nFor the Sixteen Month"
    """

    call_llm(model_name,
             prompt_template,
             extracted_text
    )
