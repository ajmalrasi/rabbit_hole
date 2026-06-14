"""Tests for the resilient JSON extraction helper."""
from __future__ import annotations

import pytest

from services.json_utils import extract_json


def test_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_json_in_markdown_fence():
    text = "Here you go:\n```json\n{\"a\": 2}\n```\nthanks!"
    assert extract_json(text) == {"a": 2}


def test_json_with_surrounding_prose():
    text = 'Sure! {"score": 7, "ok": true} hope that helps'
    assert extract_json(text) == {"score": 7, "ok": True}


def test_generic_fence_without_lang():
    text = "```\n{\"x\": [1, 2, 3]}\n```"
    assert extract_json(text) == {"x": [1, 2, 3]}


def test_empty_raises():
    with pytest.raises(ValueError):
        extract_json("")


def test_no_json_raises():
    with pytest.raises(ValueError):
        extract_json("there is no json here")
