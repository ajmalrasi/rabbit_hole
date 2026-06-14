"""Helpers for coaxing valid JSON out of LLM responses.

Local models in particular sometimes wrap JSON in markdown fences or add stray
prose. These helpers extract and parse the first JSON object found.
"""
from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a single JSON object from ``text``.

    Raises ``ValueError`` if no parseable object can be found.
    """
    if not text:
        raise ValueError("Empty response, no JSON to parse")

    candidate = text.strip()

    # 1. Strip markdown fences if present.
    fence_match = _FENCE_RE.search(candidate)
    if fence_match:
        candidate = fence_match.group(1).strip()

    # 2. Direct parse.
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 3. Fall back to the substring between the first '{' and last '}'.
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = candidate[start : end + 1]
        return json.loads(snippet)

    raise ValueError("No JSON object found in response")
