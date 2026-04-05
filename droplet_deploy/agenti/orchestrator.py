"""Orchestrator agent — synthesises extraction reports into positioning plan."""

import json
import re
import os
from typing import List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from .prompts import ORCHESTRATOR_SYSTEM, ORCHESTRATOR_USER_TEMPLATE
from .utils import get_latest_opus_model

load_dotenv()

def orchestrate(extraction_reports: List[dict], api_key: Optional[str] = None) -> dict:
    """
    Run orchestrator agent on extraction reports.
    Returns parsed JSON positioning plan.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY required. Set in .env or pass api_key.")

    extraction_jsons = json.dumps(extraction_reports, indent=2)
    user_msg = ORCHESTRATOR_USER_TEMPLATE.replace("{{EXTRACTION_JSONS}}", extraction_jsons)

    client = Anthropic(api_key=api_key)
    model = get_latest_opus_model(api_key)

    response = client.messages.create(
        model=model,
        max_tokens=16384,
        system=ORCHESTRATOR_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text if response.content else ""

    # Parse JSON — strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return json.loads(text)
