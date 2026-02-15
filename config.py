from pydantic import BaseModel, Field
from pathlib import Path

class CoreConfig(BaseModel):
    max_memory_size: int = Field(1000, ge=1)
    similarity_method: str = Field("cosine")
    concept_similarity_threshold: float = Field(0.75, ge=0.0, le=1.0)
    decay_check_interval: int = Field(3600, ge=60)
    concept_half_life_hours: float = Field(72.0, gt=0)
    min_confidence_threshold: float = Field(0.01, ge=0.0, le=1.0)
    rule_min_support: int = Field(2, ge=1)
    goal_generation_interval: int = Field(50, ge=1)
    checkpoint_interval: int = Field(100, ge=1)
    checkpoint_dir: Path = Field(default=Path("./checkpoints"))
    max_rules_per_observation: int = Field(5, ge=0)

    class Config:
        arbitrary_types_allowed = True