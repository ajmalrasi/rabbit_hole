"""Prompts for the rabbit hole generation stage."""
from __future__ import annotations

# The canonical category vocabulary the model should pick from.
CATEGORIES = [
    "physics",
    "engineering",
    "biology",
    "geography",
    "infrastructure",
    "architecture",
    "transportation",
    "agriculture",
    "manufacturing",
    "sports science",
    "economics",
    "chemistry",
    "earth science",
    "other",
]

RABBIT_HOLE_SYSTEM_PROMPT = """You are the lead writer for "Rabbit Hole", an app that \
reveals the HIDDEN MECHANISMS behind ordinary things. You do NOT summarise news. You \
take an ordinary observation and uncover the invisible system that secretly governs it.

Your writing is:
- Vivid and concrete, never vague.
- Scientifically accurate (no hand-waving, no made-up numbers).
- Focused on ONE clear underlying mechanism (a physical, biological, engineering, or \
economic system).
- Accessible to a curious non-expert.

Always answer the implicit question: "What invisible system is causing this?"

Respond with STRICT JSON only, no prose, no markdown fences."""


def build_rabbit_hole_prompt(
    title: str, summary: str, source_url: str, allowed_categories: list[str]
) -> str:
    """Construct the user prompt for generating a structured rabbit hole."""
    summary = (summary or "").strip()[:2500]
    categories = ", ".join(allowed_categories)
    return f"""Turn the following topic into a "Rabbit Hole" entry.

TOPIC TITLE: {title}
CONTEXT: {summary or "(no summary available)"}
SOURCE URL: {source_url}

Identify the single most fascinating HIDDEN MECHANISM behind this topic and explain it.

Return STRICT JSON in exactly this shape (all fields are required, all strings):
{{
  "title": "<short, punchy title naming the phenomenon>",
  "observation": "<the ordinary, observable thing anyone might notice (1-2 sentences)>",
  "question": "<the curiosity-driving question: what invisible system causes this?>",
  "hidden_mechanism": "<name the specific underlying system/principle in a phrase>",
  "explanation": "<clear, accurate explanation of how the mechanism works (3-5 sentences)>",
  "interesting_fact": "<one surprising, concrete fact related to the mechanism>",
  "why_it_matters": "<why understanding this matters in the real world (1-2 sentences)>",
  "follow_up_question": "<a question that pulls the reader deeper down the rabbit hole>",
  "category": "<one of: {categories}>",
  "source_url": "{source_url}"
}}"""
