"""Load tweets from datasets and format for extraction agent."""

import json
import glob
import os
from typing import Dict, List, Optional
from datetime import datetime


def load_conversation_parents(directory: str) -> Dict[str, dict]:
    """Load parent tweets for reply context.
    Maps parent_tweet_id -> full tweet object. When a commentator's tweet has
    inReplyToId=X, we look up X here to get the text they were replying to.
    """
    path = os.path.join(directory, "conversation_parents.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _format_tweet_for_extraction(
    tweet: dict,
    parents: Dict[str, dict],
    handle: str,
) -> str:
    """Format a single tweet for the extraction prompt."""
    author = tweet.get("author", {})
    if isinstance(author, dict):
        author_handle = author.get("userName", handle)
    else:
        author_handle = handle

    lines = []
    lines.append(f"[{tweet.get('createdAt', '')}] @{author_handle}")
    lines.append(tweet.get("text", ""))
    lines.append(
        f"  engagement: {tweet.get('likeCount', 0)} likes, "
        f"{tweet.get('retweetCount', 0)} RTs, "
        f"{tweet.get('replyCount', 0)} replies, "
        f"{tweet.get('viewCount', 'N/A')} views"
    )

    # Add parent context for replies
    in_reply_to = tweet.get("inReplyToId")
    if in_reply_to and in_reply_to in parents:
        parent = parents[in_reply_to]
        p_author = parent.get("author", {})
        p_handle = p_author.get("userName", "unknown") if isinstance(p_author, dict) else "unknown"
        lines.append(f"  [REPLY TO @{p_handle}]: {parent.get('text', '')}")

    # Add quoted tweet context
    quoted = tweet.get("quoted_tweet")
    if quoted:
        q_author = quoted.get("author", {})
        q_handle = q_author.get("userName", "unknown") if isinstance(q_author, dict) else "unknown"
        lines.append(f"  [QUOTED @{q_handle}]: {quoted.get('text', '')}")

    return "\n".join(lines)


def load_posts_by_commentator(
    dataset_dir: str,
    max_commentators: Optional[int] = None,
) -> Dict[str, str]:
    """
    Load tweets from a 24h_accrued-style dataset, grouped by commentator.
    Returns dict: handle -> formatted post batch string.
    """
    parents = load_conversation_parents(dataset_dir)
    pattern = os.path.join(dataset_dir, "tweets_*_24h_*.json")
    files = glob.glob(pattern)

    # Group files by commentator (extract handle from filename: tweets_HANDLE_24h_...)
    commentator_files: Dict[str, List[str]] = {}
    for f in files:
        basename = os.path.basename(f)
        if basename == "conversation_parents.json":
            continue
        parts = basename.replace("tweets_", "").split("_24h_")
        if len(parts) >= 1:
            handle = parts[0]
            commentator_files.setdefault(handle, []).append(f)

    result: Dict[str, str] = {}
    commentators = sorted(commentator_files.keys())
    if max_commentators:
        commentators = commentators[:max_commentators]

    for handle in commentators:
        all_tweets: List[dict] = []
        for filepath in sorted(commentator_files[handle]):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                all_tweets.extend(data)
            elif isinstance(data, dict) and "tweets" in data:
                all_tweets.extend(data["tweets"])
            else:
                all_tweets.append(data)

        # Filter to tweets by this commentator
        by_author = [
            t for t in all_tweets
            if isinstance(t.get("author"), dict)
            and t.get("author", {}).get("userName") == handle
        ]
        if not by_author:
            by_author = all_tweets  # fallback if structure differs

        # Sort by created date
        by_author.sort(key=lambda t: t.get("createdAt", ""))

        formatted = []
        for t in by_author:
            formatted.append(_format_tweet_for_extraction(t, parents, handle))

        result[handle] = "\n\n---\n\n".join(formatted)

    return result


def get_scrape_date(dataset_dir: str) -> str:
    """Infer scrape date from filenames (YYYY-MM-DD)."""
    files = glob.glob(os.path.join(dataset_dir, "tweets_*_24h_*.json"))
    if not files:
        return datetime.now().strftime("%Y-%m-%d")
    basename = os.path.basename(files[0])
    # tweets_HANDLE_24h_2026-03-11_2203_page_001.json
    parts = basename.split("_")
    for i, p in enumerate(parts):
        if len(p) == 10 and p[4] == "-" and p[7] == "-":
            return p
    return datetime.now().strftime("%Y-%m-%d")
