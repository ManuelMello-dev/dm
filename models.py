from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from collections import deque
from typing import Dict, Any, Deque, Set, Tuple

@dataclass
class Concept:
    id: str
    domain: str
    signature: Dict[str, float]
    examples: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=100))
    created_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp)
    last_updated: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp)
    first_seen: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp)
    last_seen: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp)
    observation_span_hours: float = 0.0
    observation_count: int = 0
    distinct_time_windows: int = 0
    confidence: float = 0.0

    def update_temporal_metrics(self, current_time: float) -> None:
        self.last_seen = current_time
        self.last_updated = current_time
        self.observation_count += 1

        self.observation_span_hours = (self.last_seen - self.first_seen) / 3600.0

        time_windows: Set[int] = set()
        for ex in self.examples:
            ts = ex.get("timestamp")
            if isinstance(ts, (int, float)):
                time_windows.add(int(ts // 3600))
        self.distinct_time_windows = len(time_windows)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["example_count"] = len(self.examples)
        d["signature"] = dict(self.signature)
        return d


@dataclass
class Rule:
    antecedent: str
    consequent: str
    confidence: float
    support: int = 1
    created_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp)
    last_seen: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp)
    observation_span_hours: float = 0.0

    def update_temporal(self, current_time: float) -> None:
        self.last_seen = current_time
        self.observation_span_hours = (current_time - self.created_at) / 3600.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMetrics:
    concepts_formed: int = 0
    concepts_decayed: int = 0
    rules_learned: int = 0
    transfers_made: int = 0
    goals_generated: int = 0
    total_observations: int = 0
    errors: int = 0
    uptime_seconds: float = 0.0
    last_observation_time: float | None = None
    symbols_tracked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
