from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class CoreConfig:
    max_memory_size: int = 1000
    similarity_method: str = "cosine"
    concept_similarity_threshold: float = 0.75
    decay_check_interval: int = 3600
    concept_half_life_hours: float = 72.0
    min_confidence_threshold: float = 0.01
    rule_min_support: int = 2
    goal_generation_interval: int = 50
    checkpoint_interval: int = 100
    checkpoint_dir: Path = field(default_factory=lambda: Path("./checkpoints"))
    max_rules_per_observation: int = 5
