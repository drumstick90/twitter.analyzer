"""
Claude-powered intelligence layer for tweet datasets.

- serialize_dataset   : lean text serialization of a dataset
- generate_concept_map: one-shot knowledge tree (cached to disk)
- stream_question     : Q&A with prompt caching (corpus cached 5 min)
"""

import glob
import html
import json
import os
from datetime import datetime
from typing import Generator

import anthropic

from .intel_log import log as intel_log

# ---------------------------------------------------------------------------
# Models (override via .env — IDs change; older 3.5 snapshots may 404)
# ---------------------------------------------------------------------------
def _model_map() -> str:
    return os.getenv("ANTHROPIC_MODEL_MAP", "claude-sonnet-4-6")


def _model_qa() -> str:
    return os.getenv("ANTHROPIC_MODEL_QA", "claude-haiku-4-5-20251001")

CONCEPT_MAP_FILE = "concept_map.json"

# ---------------------------------------------------------------------------
# Client (lazy singleton so tests don't need the key)
# ---------------------------------------------------------------------------
_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------

def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%a %b %d %H:%M:%S %z %Y",):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def serialize_dataset(dataset_path: str) -> tuple[str, int]:
    """
    Load every tweet JSON in dataset_path and return:
      (lean_text, tweet_count)

    Format per line:
      YYYY-MM-DD | @author | tweet text
    """
    files = sorted(glob.glob(os.path.join(dataset_path, "*.json")))
    rows: list[tuple[datetime | None, str]] = []

    for fpath in files:
        if os.path.basename(fpath) in ("conversation_parents.json", "concept_map.json"):
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        tweets = data if isinstance(data, list) else data.get("tweets", [])
        for t in tweets:
            raw_text = t.get("text") or t.get("fullText") or ""
            text = html.unescape(raw_text).strip().replace("\n", " ")
            if not text:
                continue
            author = (t.get("author") or {}).get("userName") or "unknown"
            dt = _parse_dt(t.get("createdAt") or t.get("created_at"))
            date_str = dt.strftime("%Y-%m-%d") if dt else "????-??-??"
            rows.append((dt, f"{date_str} | @{author} | {text}"))

    rows.sort(key=lambda r: r[0] or datetime.min)
    lines = [r[1] for r in rows]
    return "\n".join(lines), len(lines)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Concept map — generate + cache (uses tool_use for guaranteed valid JSON)
# ---------------------------------------------------------------------------

_CONCEPT_MAP_TOOL = {
    "name": "save_knowledge_map",
    "description": "Save a structured knowledge map extracted from the tweet dataset.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Dataset name — Knowledge Map",
            },
            "summary": {
                "type": "string",
                "description": "2-4 sentence synthesis of the main intellectual themes and unique perspective",
            },
            "themes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Theme name (3-5 words)"},
                        "description": {"type": "string", "description": "1-2 sentences"},
                        "subtopics": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "subtopics": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "description": {"type": "string"},
                                            },
                                            "required": ["name", "description"],
                                        },
                                    },
                                },
                                "required": ["name", "description"],
                            },
                        },
                    },
                    "required": ["name", "description", "subtopics"],
                },
            },
        },
        "required": ["title", "summary", "themes"],
    },
}


def concept_map_path(dataset_path: str) -> str:
    return os.path.join(dataset_path, CONCEPT_MAP_FILE)


def concept_map_exists(dataset_path: str) -> bool:
    return os.path.exists(concept_map_path(dataset_path))


def load_concept_map(dataset_path: str) -> dict:
    with open(concept_map_path(dataset_path), encoding="utf-8") as f:
        return json.load(f)


def generate_concept_map(dataset_path: str, dataset_name: str) -> dict:
    """
    Call Claude Sonnet with tool_use to build a knowledge tree.
    tool_use guarantees the SDK serializes valid JSON — no parse errors.
    Result is saved to concept_map.json inside dataset_path and returned.
    """
    intel_log(dataset_name, "concept map: serializing dataset…")
    corpus, tweet_count = serialize_dataset(dataset_path)
    tokens = estimate_tokens(corpus)
    intel_log(dataset_name, f"concept map: {tweet_count} tweets, ~{tokens:,} est. tokens → Claude ({_model_map()})")

    system_prompt = (
        "You are an expert knowledge analyst. "
        "You will receive a chronological stream of tweets and must extract a structured "
        "knowledge map that reveals the author's intellectual interests, recurring themes, "
        "and conceptual framework. "
        "You MUST call the save_knowledge_map tool with the result."
    )

    user_prompt = (
        f'Analyse the complete tweet dataset for "{dataset_name}" '
        f"({tweet_count} tweets, ~{tokens:,} tokens) below.\n\n"
        f"<tweets>\n{corpus}\n</tweets>\n\n"
        "Extract a knowledge map by calling save_knowledge_map.\n\n"
        "Rules:\n"
        "- 5-9 top-level themes\n"
        "- 3-6 subtopics per theme\n"
        "- Max 2 levels of nesting\n"
        "- Ground every theme in actual content from the tweets — no generic filler\n"
        "- Order themes by prevalence/importance"
    )

    client = _get_client()
    intel_log(dataset_name, "concept map: API request in flight (streaming)…")
    with client.messages.stream(
        model=_model_map(),
        max_tokens=128000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[_CONCEPT_MAP_TOOL],
        tool_choice={"type": "tool", "name": "save_knowledge_map"},
    ) as stream:
        response = stream.get_final_message()

    tool_input = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "save_knowledge_map":
            tool_input = block.input
            break

    if tool_input is None:
        raise RuntimeError("Claude did not call save_knowledge_map — no structured output returned")

    themes = tool_input.get("themes", [])
    intel_log(dataset_name, f"concept map: received {len(themes)} themes (stop={response.stop_reason})")

    if not themes:
        raise RuntimeError(
            f"Concept map returned 0 themes (stop_reason={response.stop_reason}). "
            "The model may have run out of output tokens. Try again."
        )

    concept_map = dict(tool_input)
    concept_map["_meta"] = {
        "tweet_count": tweet_count,
        "tokens_sent": tokens,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": _model_map(),
    }

    with open(concept_map_path(dataset_path), "w", encoding="utf-8") as f:
        json.dump(concept_map, f, ensure_ascii=False, indent=2)

    intel_log(dataset_name, "concept map: saved concept_map.json ✓")
    return concept_map


# ---------------------------------------------------------------------------
# Q&A — streaming with prompt caching
# ---------------------------------------------------------------------------

_QA_SYSTEM = (
    "You are an analyst helping the user explore a Twitter/X dataset. "
    "The tweets below are the complete dataset — treat them as your only source of truth. "
    "Answer questions concisely and precisely. "
    "Cite specific tweets or patterns when relevant (format: '@author, DATE: …'). "
    "If something cannot be determined from the data, say so clearly. "
    "Keep answers focused; prefer bullet points for lists."
)


def stream_question(dataset_path: str, question: str) -> Generator[str, None, None]:
    """
    Stream Claude's answer to a question about the dataset.
    The tweet corpus is marked as cacheable so repeat questions
    within the same 5-minute window pay ~10% of corpus token cost.

    Yields text chunks as they arrive.
    """
    ds = os.path.basename(dataset_path.rstrip(os.sep))
    corpus, tweet_count = serialize_dataset(dataset_path)
    tokens = estimate_tokens(corpus)
    qprev = (question[:100] + "…") if len(question) > 100 else question
    intel_log(ds, f"Q&A: {tweet_count} tweets, ~{tokens:,} tok corpus · {_model_qa()}")
    intel_log(ds, f"Q: {qprev.replace(chr(10), ' ')}")

    client = _get_client()

    with client.messages.stream(
        model=_model_qa(),
        max_tokens=2048,
        system=_QA_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"<tweets count='{tweet_count}' tokens=~'{tokens}'>\n{corpus}\n</tweets>",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": question,
                    },
                ],
            }
        ],
    ) as stream:
        n = 0
        for chunk in stream.text_stream:
            n += len(chunk)
            yield chunk
        intel_log(ds, f"Q&A: stream end, {n} chars out")
