import json
from pathlib import Path
from typing import Dict, Any
from .models import Concept, Rule, SystemMetrics

class JsonCheckpointStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        concepts: Dict[str, Concept],
        rules: Dict[str, Rule],
        metrics: SystemMetrics,
        iteration: int
    ) -> None:
        tmp = self.path.with_suffix(".tmp")
        payload: Dict[str, Any] = {
            "iteration": iteration,
            "concepts": {cid: c.to_dict() for cid, c in concepts.items()},
            "rules": {rid: r.to_dict() for rid, r in rules.items()},
            "metrics": metrics.to_dict(),
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # You can add a load() method when you’re ready to restore state.