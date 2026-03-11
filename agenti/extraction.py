"""Extraction agent — runs Claude API to extract signals from commentator posts."""

import json
import re
import os
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from .prompts import EXTRACTION_SYSTEM, EXTRACTION_USER_TEMPLATE

load_dotenv()

EXTRACTION_MODEL = "claude-opus-4-6"


def extract_signals(handle: str, raw_post_data: str, api_key: Optional[str] = None) -> dict:
    """
    Run extraction agent on a commentator's post batch.
    Returns parsed JSON extraction report.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY required. Set in .env or pass api_key.")

    user_msg = (
        EXTRACTION_USER_TEMPLATE.replace("{{HANDLE}}", f"@{handle}")
        .replace("{{RAW_POST_DATA}}", raw_post_data)
    )

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=EXTRACTION_MODEL,
        max_tokens=16384,
        system=EXTRACTION_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text if response.content else ""

    # Parse JSON — strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return json.loads(text)
