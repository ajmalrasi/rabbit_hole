"""In-memory tracker for the live state of a running pipeline.

The pipeline runs as a FastAPI background task with no persistent run record, so
this module exposes a single process-wide :class:`PipelineState` that the
pipeline updates as it progresses. The ``/admin/status`` endpoint reads from it
to drive the app's admin panel (current stage, progress, and a rough ETA).

This is intentionally lightweight and process-local: it resets on restart and is
only meant for observability, not durable bookkeeping.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StageProgress:
    name: str = "idle"
    total: int = 0
    processed: int = 0
    started_at: datetime | None = None

    @property
    def elapsed_seconds(self) -> float:
        if self.started_at is None:
            return 0.0
        return (_now() - self.started_at).total_seconds()

    @property
    def eta_seconds(self) -> float | None:
        """Estimated seconds remaining for this stage, based on observed rate."""
        if self.processed <= 0 or self.total <= 0:
            return None
        remaining = max(self.total - self.processed, 0)
        if remaining == 0:
            return 0.0
        rate = self.elapsed_seconds / self.processed  # seconds per item
        return round(rate * remaining, 1)


class PipelineState:
    """Process-wide, thread-safe snapshot of the current/last pipeline run."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running: bool = False
        self.stage: StageProgress = StageProgress()
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.drain: bool = False
        # Cumulative counters for the active (or most recent) run.
        self.counters: dict[str, int] = self._zero_counters()
        self.errors: list[str] = []
        self.last_summary: dict | None = None

    @staticmethod
    def _zero_counters() -> dict[str, int]:
        return {
            "ingested": 0,
            "scored": 0,
            "passed": 0,
            "rejected": 0,
            "generated": 0,
            "duplicates": 0,
            "failed": 0,
            "feed_size": 0,
        }

    # ----- lifecycle hooks (called by the pipeline) -----

    def start_run(self, *, drain: bool) -> None:
        with self._lock:
            self.running = True
            self.drain = drain
            self.started_at = _now()
            self.finished_at = None
            self.counters = self._zero_counters()
            self.errors = []
            self.stage = StageProgress(name="starting", started_at=_now())

    def set_stage(self, name: str, total: int = 0) -> None:
        with self._lock:
            self.stage = StageProgress(name=name, total=total, started_at=_now())

    def set_stage_total(self, total: int) -> None:
        with self._lock:
            self.stage.total = total

    def advance(self, processed: int = 1, **counter_deltas: int) -> None:
        with self._lock:
            self.stage.processed += processed
            for key, delta in counter_deltas.items():
                if key in self.counters:
                    self.counters[key] += delta

    def set_counter(self, **counters: int) -> None:
        with self._lock:
            for key, value in counters.items():
                if key in self.counters:
                    self.counters[key] = value

    def add_error(self, message: str) -> None:
        with self._lock:
            self.errors.append(message)

    def finish(self, summary: dict | None = None) -> None:
        with self._lock:
            self.running = False
            self.finished_at = _now()
            self.stage = StageProgress(name="done", started_at=_now())
            self.last_summary = summary

    # ----- read snapshot (called by the API) -----

    def snapshot(self) -> dict:
        with self._lock:
            run_elapsed = None
            if self.started_at is not None:
                end = self.finished_at or _now()
                run_elapsed = round((end - self.started_at).total_seconds(), 1)
            return {
                "running": self.running,
                "stage": self.stage.name,
                "stage_total": self.stage.total,
                "stage_processed": self.stage.processed,
                "stage_elapsed_seconds": round(self.stage.elapsed_seconds, 1),
                "stage_eta_seconds": self.stage.eta_seconds,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "run_elapsed_seconds": run_elapsed,
                "drain": self.drain,
                "counters": dict(self.counters),
                "errors": list(self.errors),
                "last_summary": self.last_summary,
            }


# Single process-wide instance.
pipeline_state = PipelineState()
