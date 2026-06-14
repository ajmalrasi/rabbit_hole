"""Prompt templates for the LLM-driven pipeline stages."""
from prompts.curiosity import build_curiosity_prompt, CURIOSITY_SYSTEM_PROMPT
from prompts.rabbit_hole import build_rabbit_hole_prompt, RABBIT_HOLE_SYSTEM_PROMPT

__all__ = [
    "build_curiosity_prompt",
    "CURIOSITY_SYSTEM_PROMPT",
    "build_rabbit_hole_prompt",
    "RABBIT_HOLE_SYSTEM_PROMPT",
]
