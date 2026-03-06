import os
import re
from datetime import datetime, timezone


def sanitize_error_message(msg):
    """Strip sensitive fields (user_id, api keys) from API error messages."""
    msg = re.sub(r"'user_id':\s*'[^']*'", "'user_id': '<redacted>'", msg)
    msg = re.sub(r"\"user_id\":\s*\"[^\"]*\"", '"user_id": "<redacted>"', msg)
    return msg

def extract_from_triple_backticks(text):
    """Extract content enclosed in triple backticks from multiline text.

    Expects the text to end with lines containing triple backticks surrounding content.
    Returns the extracted content, or None if no triple backticks found.
    """
    import re

    # Find all occurrences of triple backticks with content between them
    # This handles both single-line (```content```) and multi-line formats
    # Group 1 captures optional language/first-word, Group 2 captures remaining content
    pattern = r"```(\w*)\n?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        # Fallback: try to extract raw JSON object from the text
        json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        return json_match.group(0).strip() if json_match else None

    # Get the last match
    lang_or_content, content = matches[-1]

    # If content is empty, the first group was actually the content (not a language)
    if not content.strip() and lang_or_content:
        result = lang_or_content.strip()
    else:
        result = content.strip()

    # Strip leading comment markers (e.g., "/// " or "// " from GPT 5.2 outputs)
    if result.startswith("///"):
        result = result[3:].strip()
    elif result.startswith("//"):
        result = result[2:].strip()

    return result


def create_timestamped_folder():
    """Create a folder named with current UTC datetime and return the folder name."""
    folder_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H_%M_%S")
    os.makedirs("expts/" + folder_name, exist_ok=False)
    return folder_name
