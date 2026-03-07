"""Doubleword Batch API client using the autobatcher library."""

import asyncio
import logging
import os

import openai
from autobatcher import BatchOpenAI
from dotenv import load_dotenv

import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler("llm_doubleword_calls.log")
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_fh)

load_dotenv()

SYSTEM_MESSAGE = (
    "You are an expert at extracting information from UK charity financial documents. "
    "Follow the instructions exactly. Output ONLY the JSON block, nothing else."
)


def create_client(
    completion_window: str = "1h",
    batch_size: int = 100,
    batch_window_seconds: float = 2.0,
    poll_interval_seconds: float = 10.0,
) -> BatchOpenAI:
    """Create a BatchOpenAI client configured for the Doubleword API."""
    return BatchOpenAI(
        api_key=os.getenv("DOUBLEWORD_API_KEY"),
        base_url="https://api.doubleword.ai/v1",
        batch_size=batch_size,
        batch_window_seconds=batch_window_seconds,
        poll_interval_seconds=poll_interval_seconds,
        completion_window=completion_window,
    )


async def call_llm(
    client: BatchOpenAI,
    model_name: str,
    prompt_template: str,
    extracted_text: str,
) -> str:
    """Call an LLM via the Doubleword batch API and return the extracted text response."""
    prompt = prompt_template + extracted_text
    logger.info("Calling %s, prompt_len=%d", model_name, len(prompt))

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
        )
    except (openai.APIError, openai.APITimeoutError) as e:
        logger.error("API error for %s: %s", model_name, e)
        raise RuntimeError(f"Doubleword API error ({model_name}): {e}") from e

    raw_text = response.choices[0].message.content
    logger.info("Response from %s, response_len=%d", model_name, len(raw_text) if raw_text else 0)

    extracted = utils.extract_from_triple_backticks(raw_text)
    if extracted is None:
        return raw_text
    return extracted


if __name__ == "__main__":
    async def _test():
        client = create_client()
        try:
            result = await call_llm(
                client,
                "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8",
                "Extract the charity number from the following text and return as JSON:\n\n",
                "Registered Charity Number 1132766",
            )
            print(f"Result: {result}")
        finally:
            await client.close()

    asyncio.run(_test())
