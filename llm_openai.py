import json
import os

from dotenv import load_dotenv
from openai import OpenAI
import utils

load_dotenv()

# LMStudio
# client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="")
# model = "meta-llama-3.1-8b-instruct"
# OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)
# model = "deepseek/deepseek-v3.1-terminus"
# model = "meta-llama/llama-4-scout"


def make_prompt(markdown_single_entry):
    instructions = "You are a chess master, you always pick the best correct move to improve your position."
    llm_input = instructions
    llm_input += "You need to extract the following items from the block of markdown text that's copied below. Output the desired items in a flat JSON block\n"
    llm_input += "Extract the Primary Name, D.O.B. and Place of Birth and Non Latin Name fields, place exactly the text you see into JSON keys 'Primary Name' and 'D.O.B.', inside a ``` triple tick block, for example ```\n{'Primary Name': ..., 'D.O.B.': ..., 'Place of Birth': ..., 'Non Latin Names': ...}\n"
    llm_input += "Here follows the markdown you need to extract from:\n"
    llm_input += markdown_single_entry
    return instructions, llm_input


def call_llm(model_name, markdown_single_entry):
    instructions, llm_input = make_prompt(markdown_single_entry)

    print(llm_input)
    if model_name.startswith("meta-llama/llama-3-70b"):
        only_providers = ["deepinfra"]
    if model_name.startswith("meta-llama/llama-4-scout"):
        only_providers = ["deepinfra"]
    if model_name.startswith("deepseek/deepseek-v3.2-speciale"):
        only_providers = ["parasail"]
    if model_name.startswith("deepseek/deepseek-v3.1-terminus"):
        only_providers = ["atlas-cloud"]
    if model_name.startswith("z-ai/glm-4.7"):
        only_providers = ["z-ai"]
    if model_name.startswith("anthropic"):
        only_providers = None  # ["anthropic"] gives 521 and 520 errors intermittently
    if model_name.startswith("openai"):
        only_providers = None
    extra_params = {"provider": {"allow_fallbacks": False, "only": only_providers}}
    print(f"LLM calling with {model_name}")
    # extra_params = {}
    while True:
        try:
            response = client.responses.create(
                model=model_name,
                instructions=instructions,
                input=llm_input,
                extra_body=extra_params,
            )
            break  # jump out if we're successful
        except json.JSONDecodeError:
            print("Oops, got a JSONDecodeError after calling LLM")

    print(f"Raw return from llm call:\n{response.output_text}")
    extracted = utils.extract_from_triple_backticks(response.output_text)
    print(f"Extracted answer:\n{extracted}")
    return extracted


# return response.output_text


if __name__ == "__main__":
    print(f"Openrouter API key: {os.getenv('OPENROUTER_API_KEY')}")

    model_name = 'meta-llama/llama-3-70b-instruct' # fast
    #model_name = 'meta-llama/llama-4-scout' # fast
    #model_name = "deepseek/deepseek-v3.1-terminus"  # fast
    #model_name = "z-ai/glm-4.7"  # slow

    markdown_single_block = """
<figure>\n\n<!-- PageHeader=\"Foreign, Commonwealth & Development Office\" -->\n\n</figure>\n\n\n# UK SANCTIONS LIST P
UBLICATION Last Updated: 19/12/2025\n\n\n## THE AFGHANISTAN (SANCTIONS) (EU EXIT) REGULATIONS 2020\n\n\n### INDIVIDUAL\n\n1\\.\nPrim
ary Name: 1: Mullah MOHAMMAD HASSAN AKHUND Position: First Deputy, Council of Ministers under the\nTaliban regime,Governor of Kandah
ar under the Taliban regime,Foreign Minister under the Taliban regime, Political\nAdvisor of Mullah Mohammed Omar D.O.B: dd/mm/1945,
dd/mm/1946,dd/mm/1947,dd/mm/1948,dd/mm/\n1949,dd/mm/1950,dd/mm/1955,dd/mm/1956,dd/mm/1957,dd/mm/1958 Place of Birth: 1: Pashmul vill
age,\nمحمد حسن آخوند :1 :Panjwai District, Kandahar Province, Afghanistan Nationality(ies): Afghanistan Non Latin Names\nSanctions I
mposed: Asset freeze, Travel Ban Other Information: A close associate of Mullah Mohammed Omar (TAi.\n004). Member of Taliban Supreme
 Council as at Dec. 2009. Belongs to Kakar tribe. Review pursuant to Security\nCouncil resolution 1822 (2008) was concluded on 21 Ju
l. 2010. INTERPOL-UN Security Council Special Notice web\nlink: https://www.interpol.int/en/How-we-work/ Notices/View-UN-Notices-Ind
ividuals click here Designation\nSource: UN Date Designated: 25/01/2001 Last Updated: 26/01/2022 Unique Id: AFG0006 OFSI Group ID: 7
172 UN\nReference ID: TAi.002\n\n2\\.
"""


    call_llm(model_name,
        markdown_single_block
    )
