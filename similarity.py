from typing import Dict
import math

def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    keys = set(v1.keys()) | set(v2.keys())
    if not keys:
        return 0.0
    dot = sum(v1.get(k, 0.0) * v2.get(k, 0.0) for k in keys)
    mag1 = math.sqrt(sum(v1.get(k, 0.0) ** 2 for k in keys))
    mag2 = math.sqrt(sum(v2.get(k, 0.0) ** 2 for k in keys))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def euclidean_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    keys = set(v1.keys()) | set(v2.keys())
    if not keys:
        return 0.0
    dist = math.sqrt(sum((v1.get(k, 0.0) - v2.get(k, 0.0)) ** 2 for k in keys))
    return 1.0 / (1.0 + dist)


def jaccard_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    set1 = set((k, round(v, 2)) for k, v in v1.items())
    set2 = set((k, round(v, 2)) for k, v in v2.items())
    if not set1 and not set2:
        return 0.0
    inter = len(set1 & set2)
    union = len(set1 | set2)
    return inter / union if union else 0.0


def get_similarity(method: str):
    if method == "cosine":
        return cosine_similarity
    if method == "euclidean":
        return euclidean_similarity
    if method == "jaccard":
        return jaccard_similarity
    return cosine_similarity