"""Configuration of the RSS / Atom sources to ingest."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str


# Curated sources chosen for their density of "hidden mechanism" material.
# Weighted toward engineering / systems; biology-heavy feeds removed.
FEED_SOURCES: list[FeedSource] = [
    FeedSource("Hacker News", "https://hnrss.org/frontpage"),
    FeedSource("Reddit technology", "https://www.reddit.com/r/technology/.rss"),
    FeedSource("Reddit engineering", "https://www.reddit.com/r/engineering/.rss"),
    FeedSource("Reddit MechanicalEngineering", "https://www.reddit.com/r/MechanicalEngineering/.rss"),
    FeedSource("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
    FeedSource(
        "Interesting Engineering",
        "https://interestingengineering.com/rss",
    ),
    FeedSource("Hackaday", "https://hackaday.com/feed/"),
    FeedSource("NASA", "https://www.nasa.gov/feed/"),
    FeedSource(
        "Science Daily",
        "https://www.sciencedaily.com/rss/all.xml",
    ),
]
