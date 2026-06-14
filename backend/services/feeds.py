"""Configuration of the RSS / Atom sources to ingest."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str


# Curated sources chosen for their density of "hidden mechanism" material.
FEED_SOURCES: list[FeedSource] = [
    FeedSource("Hacker News", "https://hnrss.org/frontpage"),
    FeedSource("Reddit technology", "https://www.reddit.com/r/technology/.rss"),
    FeedSource("Reddit todayilearned", "https://www.reddit.com/r/todayilearned/.rss"),
    FeedSource("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
    FeedSource("NASA", "https://www.nasa.gov/feed/"),
    FeedSource(
        "Interesting Engineering",
        "https://interestingengineering.com/rss",
    ),
    FeedSource("Nature", "https://www.nature.com/nature.rss"),
    FeedSource(
        "Science Daily",
        "https://www.sciencedaily.com/rss/all.xml",
    ),
]
